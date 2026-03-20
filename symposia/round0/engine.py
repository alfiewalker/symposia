from __future__ import annotations

import hashlib
from typing import List

from symposia.aggregation.round0 import aggregate_round0, decide_early_stop
from symposia.config import resolve_profile_set
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
    def __init__(self):
        self._decomposer = RuleBasedSubclaimDecomposer()

    def run(
        self,
        content: str,
        domain: str,
        profile_set: str | None = None,
        profile: str | None = None,
    ) -> InitialReviewResult:
        resolved = resolve_profile_set(domain=domain, profile_set=profile_set, profile=profile)
        bundle = self._decomposer.decompose(content=content, domain=domain)

        run_id_hash = hashlib.sha256(
            f"{resolved.profile_set.profile_set_id}:{bundle.bundle_id}".encode("utf-8")
        ).hexdigest()[:12]
        run_id = f"run_{run_id_hash}"

        jurors = [
            RuleBasedJuror(juror_id=f"juror_{idx+1}", profile_id=profile_id)
            for idx, profile_id in enumerate(resolved.profile_set.profiles)
        ]

        decisions: List[JurorDecision] = []
        for subclaim in bundle.subclaims:
            for juror in jurors:
                decisions.append(juror.decide(subclaim))

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
                )
                for d in decisions
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
        )
        initial_review_result.adjudication_trace = build_adjudication_trace(initial_review_result)
        return initial_review_result
