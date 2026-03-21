from __future__ import annotations

import asyncio
import hashlib
from typing import Callable, List, Literal

from symposia.aggregation.round0 import aggregate_round0, decide_early_stop
from symposia.config import resolve_profile_set
from symposia.core.providers.base import LLMService
from symposia.jurors import JurorExecutionRecord, LLMJuror
from symposia.jurors.rule_based import RuleBasedJuror
from symposia.kernel import RuleBasedSubclaimDecomposer
from symposia.models.juror import JurorDecision
from symposia.models.round0 import InitialReviewResult
from symposia.models.trace import (
    MinimalTraceAggregation,
    MinimalTraceSubclaim,
    MinimalTraceVote,
    CoreTrace,
)
from symposia.tracing import build_adjudication_trace


class InitialReviewEngine:
    def __init__(
        self,
        *,
        juror_mode: Literal["rule_based", "llm"] = "rule_based",
        llm_service_factory: Callable[[str, str], LLMService] | None = None,
        juror_profiles: list[str] | None = None,
        route_set_id: str | None = None,
        llm_timeout_seconds: float = 15.0,
        llm_retries: int = 2,
        llm_retry_delay_seconds: float = 0.5,
        max_juror_dropouts_per_subclaim: int = 2,
    ):
        self._decomposer = RuleBasedSubclaimDecomposer()
        self._juror_mode = juror_mode
        self._llm_service_factory = llm_service_factory
        self._juror_profiles = list(juror_profiles) if juror_profiles is not None else None
        self._route_set_id = route_set_id
        self._llm_timeout_seconds = llm_timeout_seconds
        self._llm_retries = llm_retries
        self._llm_retry_delay_seconds = llm_retry_delay_seconds
        self._max_juror_dropouts_per_subclaim = max_juror_dropouts_per_subclaim

    def run(
        self,
        content: str,
        domain: str,
        profile_set: str | None = None,
        profile: str | None = None,
    ) -> InitialReviewResult:
        resolved = resolve_profile_set(domain=domain, profile_set=profile_set, profile=profile)
        bundle = self._decomposer.decompose(content=content, domain=domain)
        juror_profile_ids = self._juror_profiles or resolved.profile_set.profiles

        run_id_hash = hashlib.sha256(
            (
                f"{resolved.profile_set.profile_set_id}:"
                f"{self._route_set_id or 'profile_set_default'}:"
                f"{','.join(juror_profile_ids)}:{bundle.bundle_id}"
            ).encode("utf-8")
        ).hexdigest()[:12]
        run_id = f"run_{run_id_hash}"

        if self._juror_mode == "rule_based":
            jurors = [
                RuleBasedJuror(juror_id=f"juror_{idx+1}", profile_id=profile_id)
                for idx, profile_id in enumerate(juror_profile_ids)
            ]
        else:
            if self._llm_service_factory is None:
                raise ValueError(
                    "InitialReviewEngine configured with juror_mode='llm' but llm_service_factory is not set"
                )
            jurors = [
                LLMJuror(
                    juror_id=f"juror_{idx+1}",
                    profile_id=profile_id,
                    llm_service=self._llm_service_factory(profile_id, domain),
                )
                for idx, profile_id in enumerate(juror_profile_ids)
            ]

        decisions: List[JurorDecision] = []
        execution_records: List[JurorExecutionRecord | None] = []
        total_dropouts = 0
        for subclaim in bundle.subclaims:
            subclaim_dropouts = 0
            if self._juror_mode == "rule_based":
                for juror in jurors:
                    decisions.append(juror.decide(subclaim))
                    execution_records.append(None)
            else:
                llm_decisions, llm_records = asyncio.run(
                    self._decide_subclaim_with_llm_jurors(
                        jurors=jurors,
                        subclaim=subclaim,
                        domain=domain,
                        profile_set_id=resolved.profile_set.profile_set_id,
                    )
                )
                decisions.extend(llm_decisions)
                execution_records.extend(llm_records)
                for record in llm_records:
                    if not record.parsed_ok:
                        subclaim_dropouts += 1
                        total_dropouts += 1

            if (
                self._juror_mode == "llm"
                and subclaim_dropouts > self._max_juror_dropouts_per_subclaim
            ):
                raise RuntimeError(
                    "llm_juror_dropout_threshold_exceeded: "
                    f"subclaim_id={subclaim.subclaim_id}, "
                    f"dropouts={subclaim_dropouts}, "
                    "max_allowed="
                    f"{self._max_juror_dropouts_per_subclaim}"
                )

        aggregated = aggregate_round0(decisions)
        early_stop = decide_early_stop(aggregated, resolved.profile_set)

        trace = CoreTrace(
            run_id=run_id,
            profile_set_selected=resolved.profile_set.profile_set_id,
            subclaims=[
                MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text)
                for s in bundle.subclaims
            ],
            juror_votes=[
                MinimalTraceVote(
                    juror_id=d.juror_id,
                    subclaim_id=d.subclaim_id,
                    supported=d.supported,
                    contradicted=d.contradicted,
                    sufficient=d.sufficient,
                    confidence=d.confidence,
                    provider_model=(execution_records[idx].provider_model if execution_records[idx] else None),
                    parsed_ok=(execution_records[idx].parsed_ok if execution_records[idx] else None),
                    error_code=(execution_records[idx].error_code if execution_records[idx] else None),
                )
                for idx, d in enumerate(decisions)
            ],
            aggregation_outcome=[
                MinimalTraceAggregation(
                    subclaim_id=a.subclaim_id,
                    support_score=a.support_score,
                    contradiction_score=a.contradiction_score,
                    sufficiency_score=a.sufficiency_score,
                )
                for a in aggregated.values()
            ],
        )

        initial_review_result = InitialReviewResult(
            run_id=run_id,
            bundle=bundle,
            decisions=decisions,
            aggregated_by_subclaim=aggregated,
            completion=early_stop,
            core_trace=trace,
            execution_policy={
                "juror_mode": self._juror_mode,
                "route_set_id": self._route_set_id,
                "juror_profiles": juror_profile_ids,
                "llm_timeout_seconds": self._llm_timeout_seconds,
                "llm_retries": self._llm_retries,
                "llm_retry_delay_seconds": self._llm_retry_delay_seconds,
                "max_juror_dropouts_per_subclaim": self._max_juror_dropouts_per_subclaim,
            },
            runtime_stats={
                "juror_count": len(jurors),
                "total_decisions": len(decisions),
                "total_dropouts": total_dropouts,
                "dropout_rate": (total_dropouts / len(decisions)) if decisions else 0.0,
            },
        )
        initial_review_result.adjudication_trace = build_adjudication_trace(initial_review_result)
        return initial_review_result

    async def _decide_subclaim_with_llm_jurors(
        self,
        *,
        jurors: list[LLMJuror],
        subclaim,
        domain: str,
        profile_set_id: str,
    ) -> tuple[list[JurorDecision], list[JurorExecutionRecord]]:
        decisions: list[JurorDecision] = []
        records: list[JurorExecutionRecord] = []
        for juror in jurors:
            decision, record = await juror.decide_async(
                subclaim,
                domain=domain,
                profile_set_id=profile_set_id,
                timeout_seconds=self._llm_timeout_seconds,
                retries=self._llm_retries,
                retry_delay_seconds=self._llm_retry_delay_seconds,
            )
            decisions.append(decision)
            records.append(record)
        return decisions, records
