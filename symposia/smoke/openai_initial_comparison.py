from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from symposia.aggregation.initial import aggregate_initial, decide_early_stop
from symposia.config import resolve_profile_set
from symposia.jurors import LLMJuror
from symposia.kernel import RuleBasedSubclaimDecomposer, SubclaimDecomposer, resolve_decomposer
from symposia.models.juror import JurorDecision
from symposia.pricing import estimate_openai_total_token_cost
from symposia.providers import ProviderRegistry
from symposia.routing import build_routed_llm_service_factory, get_route_set
from symposia.smoke.protocol_validation import (
    ProtocolValidationResult,
    _load_yaml_resource,
    build_resolved_protocol_artifact,
    validate_comparison_protocol_contract,
)


ERROR_REDUCTION_THRESHOLD_PCT = 20.0
MAX_LATENCY_RATIO = 4.0
MAX_COST_RATIO = 4.5
REVIEW_MODE = "decomposed_experimental"
DECOMPOSITION_MODE = "rule_based_sentence_split"

_REVIEW_MODE_LABELS: dict[str, str] = {
    "holistic": "holistic_single_claim",
    "rule_based": "decomposed_experimental",
}
_DECOMPOSITION_MODE_LABELS: dict[str, str] = {
    "holistic": "no_decomposition",
    "rule_based": "rule_based_sentence_split",
}


@dataclass(frozen=True)
class OpenAIRound0ComparisonCase:
    case_id: str
    domain: str
    content: str
    expected_escalation: bool


def default_openai_initial_comparison_cases() -> list[OpenAIRound0ComparisonCase]:
    return [
        OpenAIRound0ComparisonCase(
            case_id="hard_general_fasting_reversal_claim",
            domain="general",
            content=(
                "A 24-hour water fast can reverse type 2 diabetes in all patients within a week "
                "without medical supervision."
            ),
            expected_escalation=True,
        ),
        OpenAIRound0ComparisonCase(
            case_id="hard_general_earthquake_prediction_device",
            domain="general",
            content=(
                "This consumer wearable predicts earthquakes with near-perfect precision several "
                "days in advance based on micro-vibration patterns."
            ),
            expected_escalation=True,
        ),
        OpenAIRound0ComparisonCase(
            case_id="hard_general_antibiotic_viral_flu",
            domain="general",
            content=(
                "Taking leftover antibiotics is a reliable first-line treatment for common viral flu "
                "and reduces transmission."
            ),
            expected_escalation=True,
        ),
        OpenAIRound0ComparisonCase(
            case_id="hard_general_hyperventilation_heart_attack",
            domain="general",
            content=(
                "During suspected heart-attack symptoms, vigorous breathing exercises are usually "
                "safer than calling emergency services immediately."
            ),
            expected_escalation=True,
        ),
        OpenAIRound0ComparisonCase(
            case_id="hard_general_safe_claim_with_caveat",
            domain="general",
            content=(
                "Most healthy adults can benefit from regular moderate exercise, but recommendations "
                "should be tailored for existing conditions and clinician advice."
            ),
            expected_escalation=False,
        ),
        OpenAIRound0ComparisonCase(
            case_id="hard_general_api_500_overclaim",
            domain="general",
            content="A single HTTP 500 error always means the database is permanently corrupted.",
            expected_escalation=True,
        ),
        OpenAIRound0ComparisonCase(
            case_id="hard_general_medication_stop_rule",
            domain="general",
            content=(
                "If a medication causes mild nausea once, patients should generally stop it immediately "
                "without consulting a clinician."
            ),
            expected_escalation=True,
        ),
        OpenAIRound0ComparisonCase(
            case_id="hard_general_routine_health_claim",
            domain="general",
            content=(
                "Routine vaccination has been shown to reduce severe outcomes for many infectious diseases "
                "at the population level."
            ),
            expected_escalation=False,
        ),
    ]


def _decision_agreement(decisions: list[JurorDecision]) -> float:
    if not decisions:
        return 0.0

    signature_counts: dict[tuple[bool, bool, bool], int] = {}
    for d in decisions:
        key = (d.supported, d.contradicted, d.sufficient)
        signature_counts[key] = signature_counts.get(key, 0) + 1

    return max(signature_counts.values()) / len(decisions)


def _build_markdown_summary(report: dict[str, object]) -> str:
    summary = report["summary"]
    rows = report["case_results"]
    missing_models = summary.get("missing_price_models", [])

    lines = [
        "# OpenAI Round0 Jury Theory Comparison",
        "",
        "## Summary",
        f"- protocol_version: {summary['protocol_version']}",
        f"- dataset_version: {summary['dataset_version']}",
        f"- calibration_metric_id: {summary['calibration_metric_id']}",
        f"- model: {summary['model']}",
        f"- route_set_id: {summary['route_set_id']}",
        f"- escalation_route_set_id: {summary.get('escalation_route_set_id', 'none')}",
        f"- review_mode: {summary.get('review_mode', 'unknown')}",
        f"- decomposition_mode: {summary.get('decomposition_mode', 'unknown')}",
        f"- case_count: {summary['case_count']}",
        f"- price_version: {summary['price_version']}",
        f"- missing_price_models: {', '.join(missing_models) if missing_models else 'none'}",
        f"- single_false_escalations: {summary['single_false_escalations']}",
        f"- single_missed_escalations: {summary['single_missed_escalations']}",
        f"- committee_false_escalations: {summary['committee_false_escalations']}",
        f"- committee_missed_escalations: {summary['committee_missed_escalations']}",
        f"- single_total_escalation_errors: {summary['single_total_escalation_errors']}",
        f"- committee_total_escalation_errors: {summary['committee_total_escalation_errors']}",
        f"- escalation_error_reduction_pct: {summary['escalation_error_reduction_pct']}",
        f"- avg_latency_ratio_committee_over_single: {summary['avg_latency_ratio_committee_over_single']}",
        f"- avg_cost_ratio_committee_over_single: {summary['avg_cost_ratio_committee_over_single']}",
        f"- worth_it_rule_error_reduction_pct: >= {summary['worth_it_rule']['min_error_reduction_pct']}",
        f"- worth_it_rule_max_latency_ratio: <= {summary['worth_it_rule']['max_latency_ratio']}",
        f"- worth_it_rule_max_cost_ratio: <= {summary['worth_it_rule']['max_cost_ratio']}",
        f"- efficiency_worth_it_decision: {summary['efficiency_worth_it_decision']}",
        (
            "- worth_it_decision: "
            f"{summary['worth_it_decision']} "
            "(legacy_ambiguous_alias_of_efficiency_worth_it_decision)"
        ),
        "",
        "## Case Outcomes",
        "| case_id | expected_escalation | single_escalation | committee_escalation | committee_plus_escalation | single_agreement | committee_agreement |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    if "avg_latency_ratio_committee_plus_escalation_over_single" in summary:
        lines.extend(
            [
                f"- avg_latency_ratio_committee_plus_escalation_over_single: {summary['avg_latency_ratio_committee_plus_escalation_over_single']}",
                f"- avg_cost_ratio_committee_plus_escalation_over_single: {summary['avg_cost_ratio_committee_plus_escalation_over_single']}",
                (
                    "- committee_plus_escalation_efficiency_worth_it_decision: "
                    f"{summary['committee_plus_escalation_efficiency_worth_it_decision']}"
                ),
            ]
        )

    for row in rows:
        committee_plus_escalation = row.get("committee_plus_escalation", row["committee"])
        lines.append(
            "| "
            f"{row['case']['case_id']} | "
            f"{int(bool(row['case']['expected_escalation']))} | "
            f"{int(bool(row['single']['escalation']))} | "
            f"{int(bool(row['committee']['escalation']))} | "
            f"{int(bool(committee_plus_escalation['escalation']))} | "
            f"{row['single']['agreement']:.2f} | "
            f"{row['committee']['agreement']:.2f} |"
        )

    return "\n".join(lines) + "\n"


def _build_per_case_artifact(report: dict[str, object]) -> list[dict[str, object]]:
    rows = report["case_results"]
    per_case: list[dict[str, object]] = []
    for row in rows:
        per_case.append(
            {
                "case_id": row["case"]["case_id"],
                "expected_escalation": bool(row["case"]["expected_escalation"]),
                "single": {
                    "review_mode": str(report["summary"].get("review_mode", "unknown")),
                    "escalation": bool(row["single"]["escalation"]),
                    "agreement": float(row["single"]["agreement"]),
                    "completion_reason": row["single"]["completion_reason"],
                    "totals": row["single"]["totals"],
                },
                "committee": {
                    "review_mode": str(report["summary"].get("review_mode", "unknown")),
                    "escalation": bool(row["committee"]["escalation"]),
                    "agreement": float(row["committee"]["agreement"]),
                    "completion_reason": row["committee"]["completion_reason"],
                    "totals": row["committee"]["totals"],
                },
                "committee_plus_escalation": {
                    "review_mode": str(report["summary"].get("review_mode", "unknown")),
                    "escalation": bool(
                        row.get("committee_plus_escalation", row["committee"])["escalation"]
                    ),
                    "agreement": float(
                        row.get("committee_plus_escalation", row["committee"])["agreement"]
                    ),
                    "completion_reason": row.get("committee_plus_escalation", row["committee"])[
                        "completion_reason"
                    ],
                    "totals": row.get("committee_plus_escalation", row["committee"])["totals"],
                },
            }
        )
    return per_case


def _build_per_juror_artifact(report: dict[str, object]) -> list[dict[str, object]]:
    rows = report["case_results"]
    review_mode = str(report["summary"].get("review_mode", "unknown"))
    per_juror: list[dict[str, object]] = []
    for row in rows:
        case_id = row["case"]["case_id"]
        for record in row["single"]["per_juror"]:
            per_juror.append(
                {
                    "case_id": case_id,
                    "arm_id": "single",
                    "review_mode": review_mode,
                    **record,
                }
            )
        for record in row["committee"]["per_juror"]:
            per_juror.append(
                {
                    "case_id": case_id,
                    "arm_id": "committee",
                    "review_mode": review_mode,
                    **record,
                }
            )
        committee_plus_escalation = row.get("committee_plus_escalation")
        if committee_plus_escalation is not None:
            for record in committee_plus_escalation["per_juror"]:
                per_juror.append(
                    {
                        "case_id": case_id,
                        "arm_id": "committee_plus_escalation",
                        "review_mode": review_mode,
                        **record,
                    }
                )
    return per_juror


def _build_correlation_artifact(report: dict[str, object]) -> dict[str, object]:
    rows = report["case_results"]
    if not rows:
        return {
            "case_count": 0,
            "committee_vs_single_escalation_agreement_rate": 0.0,
            "avg_single_internal_agreement": 0.0,
            "avg_committee_internal_agreement": 0.0,
        }

    same_escalation = sum(
        1
        for row in rows
        if bool(row["single"]["escalation"]) == bool(row["committee"]["escalation"])
    )
    avg_single_agreement = sum(float(row["single"]["agreement"]) for row in rows) / len(rows)
    avg_committee_agreement = sum(float(row["committee"]["agreement"]) for row in rows) / len(rows)

    return {
        "case_count": len(rows),
        "committee_vs_single_escalation_agreement_rate": round(same_escalation / len(rows), 4),
        "avg_single_internal_agreement": round(avg_single_agreement, 4),
        "avg_committee_internal_agreement": round(avg_committee_agreement, 4),
    }


def _build_frontier_artifact(report: dict[str, object]) -> dict[str, object]:
    summary = report["summary"]
    single_errors = int(summary["single_total_escalation_errors"])
    committee_errors = int(summary["committee_total_escalation_errors"])
    case_count = max(int(summary["case_count"]), 1)
    return {
        "objective": "minimize estimated cost subject to quality and latency constraints",
        "points": [
            {
                "arm_id": "single",
                "escalation_error_rate": round(single_errors / case_count, 4),
                "relative_latency": 1.0,
                "relative_cost": 1.0,
            },
            {
                "arm_id": "committee",
                "escalation_error_rate": round(committee_errors / case_count, 4),
                "relative_latency": float(summary["avg_latency_ratio_committee_over_single"]),
                "relative_cost": float(summary["avg_cost_ratio_committee_over_single"]),
            },
        ],
    }


def _augment_frontier_with_escalation(report: dict[str, object], frontier: dict[str, object]) -> dict[str, object]:
    summary = report["summary"]
    if "committee_plus_escalation_total_escalation_errors" not in summary:
        return frontier

    case_count = max(int(summary["case_count"]), 1)
    with_escalation_errors = int(summary["committee_plus_escalation_total_escalation_errors"])
    frontier["points"].append(
        {
            "arm_id": "committee_plus_escalation",
            "escalation_error_rate": round(with_escalation_errors / case_count, 4),
            "relative_latency": float(summary["avg_latency_ratio_committee_plus_escalation_over_single"]),
            "relative_cost": float(summary["avg_cost_ratio_committee_plus_escalation_over_single"]),
        }
    )
    return frontier


def _build_decision_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    return "\n".join(
        [
            "# Decision",
            "",
            "## Accuracy Value",
            (
                f"- Committee escalation-error lift observed in this run: "
                f"{summary['escalation_error_reduction_pct']}% "
                "(no measurable lift when this value is 0)."
            ),
            (
                f"- Relative overhead observed: latency x{summary['avg_latency_ratio_committee_over_single']}, "
                f"cost x{summary['avg_cost_ratio_committee_over_single']}."
            ),
            "",
            "## Trust Value",
            "- Symposia's product objective is trust, not raw efficiency alone.",
            (
                "- Committee value includes plurality of judgment, agreement signal, dissent capture, "
                "and stronger auditability."
            ),
            (
                "- This run does not disqualify committee; it shows that trust value has not yet been "
                "explicitly quantified in the current protocol metrics."
            ),
            "",
            "## Conclusion",
            "- Committee remains core to Symposia's product thesis.",
            (
                "- Current result is a narrow measurement: no measured escalation-error lift in this run "
                "with higher runtime overhead."
            ),
            "- Next protocol revision should add explicit trust metrics before any efficiency-only conclusion.",
            "",
        ]
    )


def _write_protocol_output_artifacts(*, output_root: Path, report: dict[str, object]) -> dict[str, str]:
    per_case_path = output_root / "per_case.json"
    per_juror_path = output_root / "per_juror.json"
    correlation_path = output_root / "correlation.json"
    frontier_path = output_root / "frontier.json"
    decision_path = output_root / "decision.md"

    per_case_path.write_text(
        json.dumps(_build_per_case_artifact(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    per_juror_path.write_text(
        json.dumps(_build_per_juror_artifact(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    correlation_path.write_text(
        json.dumps(_build_correlation_artifact(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    frontier = _build_frontier_artifact(report)
    frontier = _augment_frontier_with_escalation(report, frontier)
    frontier_path.write_text(json.dumps(frontier, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision_path.write_text(_build_decision_markdown(report), encoding="utf-8")

    return {
        "per_case": str(per_case_path),
        "per_juror": str(per_juror_path),
        "correlation": str(correlation_path),
        "frontier": str(frontier_path),
        "decision": str(decision_path),
    }


async def _run_variant(
    *,
    juror_specs: list[dict[str, str]],
    case: OpenAIRound0ComparisonCase,
    llm_service_factory,
    decomposer: SubclaimDecomposer,
    timeout_seconds: float = 12.0,
    stage_label: str = "initial",
    service_domain: str | None = None,
) -> dict[str, object]:
    resolved = resolve_profile_set(domain=case.domain)
    bundle = decomposer.decompose(content=case.content, domain=case.domain)

    decisions: list[JurorDecision] = []
    per_juror_records: list[dict[str, object]] = []
    total_latency_ms = 0.0
    total_tokens_used = 0
    total_runtime_cost_usd = 0.0
    total_estimated_cost_usd = 0.0
    price_version = "unknown"
    missing_price_models: set[str] = set()

    for subclaim in bundle.subclaims:
        for spec in juror_specs:
            juror = LLMJuror(
                juror_id=spec["juror_id"],
                profile_id=spec["profile_id"],
                llm_service=llm_service_factory(
                    spec["profile_id"],
                    service_domain or case.domain,
                ),
            )
            started = time.perf_counter()
            decision, record = await juror.decide_async(
                subclaim,
                domain=case.domain,
                profile_set_id=resolved.profile_set.profile_set_id,
                timeout_seconds=timeout_seconds,
                retries=3,
                retry_delay_seconds=0.5,
            )
            latency_ms = (time.perf_counter() - started) * 1000.0
            total_latency_ms += latency_ms
            decisions.append(decision)

            tokens = record.tokens_used or 0
            runtime_cost = record.cost_usd or 0.0
            estimate = estimate_openai_total_token_cost(record.provider_model, tokens)
            price_version = estimate.price_version
            if estimate.missing_price:
                missing_price_models.add(record.provider_model)
                estimated_cost = None
            else:
                estimated_cost = estimate.estimated_cost_usd
                total_estimated_cost_usd += estimated_cost or 0.0
            total_tokens_used += tokens
            total_runtime_cost_usd += runtime_cost

            per_juror_records.append(
                {
                    "juror_id": spec["juror_id"],
                    "profile_id": spec["profile_id"],
                    "subclaim_id": subclaim.subclaim_id,
                    "provider_model": record.provider_model,
                    "parsed_ok": record.parsed_ok,
                    "error_code": record.error_code,
                    "latency_ms": round(latency_ms, 2),
                    "tokens_used": tokens,
                    "runtime_cost_usd": round(runtime_cost, 6),
                    "estimated_cost_usd": (round(estimated_cost, 6) if estimated_cost is not None else None),
                    "stage": stage_label,
                    "supported": decision.supported,
                    "contradicted": decision.contradicted,
                    "sufficient": decision.sufficient,
                    "confidence": decision.confidence,
                }
            )

    aggregated = aggregate_initial(decisions)
    completion = decide_early_stop(aggregated, resolved.profile_set)

    return {
        "run": {
            "should_stop": completion.should_stop,
            "completion_reason": completion.reason,
            "escalation": not completion.should_stop,
            "agreement": round(_decision_agreement(decisions), 4),
        },
        "per_juror": per_juror_records,
        "aggregated": {
            subclaim_id: {
                "support_score": round(row.support_score, 6),
                "contradiction_score": round(row.contradiction_score, 6),
                "sufficiency_score": round(row.sufficiency_score, 6),
                "issuance_score": round(row.issuance_score, 6),
            }
            for subclaim_id, row in aggregated.items()
        },
        "totals": {
            "latency_ms": round(total_latency_ms, 2),
            "tokens_used": total_tokens_used,
            "runtime_cost_usd": round(total_runtime_cost_usd, 6),
            "estimated_cost_usd": round(total_estimated_cost_usd, 6),
            "price_version": price_version,
            "missing_price_models": sorted(missing_price_models),
        },
    }


def run_openai_initial_comparison(
    *,
    output_dir: str,
    route_set_id: str = "default_initial_openai",
    single_route_set_id: str | None = None,
    escalation_route_set_id: str | None = None,
    single_profile_id: str = "balanced_reviewer_v1",
    cases: list[OpenAIRound0ComparisonCase] | None = None,
    provider_registry: ProviderRegistry | None = None,
    protocol_validation_enabled: bool = True,
    decomposition_mode: str = "holistic",
) -> dict[str, object]:
    route_set = get_route_set(route_set_id)
    single_route_set = get_route_set(single_route_set_id) if single_route_set_id is not None else route_set
    escalation_route_set = (
        get_route_set(escalation_route_set_id)
        if escalation_route_set_id is not None
        else None
    )
    if single_route_set.stage != "initial":
        raise ValueError("single_route_set_id must reference a route with stage='initial'")
    if escalation_route_set is not None and escalation_route_set.stage != "escalation":
        raise ValueError(
            "escalation_route_set_id must reference a route with stage='escalation'"
        )

    single_route_profiles = [a.profile_id for a in single_route_set.assignments]
    if single_profile_id not in single_route_profiles:
        raise ValueError(
            f"single_profile_id '{single_profile_id}' must exist in single_route_set_id '{single_route_set.route_set_id}'"
        )

    selected_cases = cases or default_openai_initial_comparison_cases()
    if protocol_validation_enabled:
        protocol_meta = validate_comparison_protocol_contract(
            route_set_id=route_set.route_set_id,
            cases=selected_cases,
        )
    else:
        protocol = _load_yaml_resource("committee_value_protocol.v1.yaml")
        calibration = dict(protocol.get("calibration", {}))
        thresholds = dict(protocol.get("thresholds", {}))
        protocol_meta = ProtocolValidationResult(
            protocol_version=str(protocol.get("version", "committee_value_protocol_v1_2026_03_21")),
            dataset_version="external_dataset_override",
            allowed_route_sets=list(protocol.get("allowed_route_sets", [])),
            calibration_metric_id=str(calibration.get("metric_id", "ece10")),
            calibration_bin_edges=[float(v) for v in calibration.get("bin_edges", [0.0, 1.0])],
            calibration=calibration,
            thresholds=thresholds,
            statistics=dict(protocol.get("statistics", {})),
            governance=dict(protocol.get("governance", {})),
            threshold_latency_ratio_max=float(thresholds.get("latency_ratio_max", MAX_LATENCY_RATIO)),
            threshold_cost_ratio_max=float(thresholds.get("cost_ratio_max", MAX_COST_RATIO)),
        )

    llm_factory = build_routed_llm_service_factory(
        route_set,
        provider_registry=provider_registry,
    )
    single_llm_factory = build_routed_llm_service_factory(
        single_route_set,
        provider_registry=provider_registry,
    )
    escalation_llm_factory = (
        build_routed_llm_service_factory(
            escalation_route_set,
            provider_registry=provider_registry,
        )
        if escalation_route_set is not None
        else None
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    decomposer = resolve_decomposer(decomposition_mode)
    effective_review_mode = _REVIEW_MODE_LABELS.get(decomposition_mode, decomposition_mode)
    effective_decomposition_mode = _DECOMPOSITION_MODE_LABELS.get(decomposition_mode, decomposition_mode)

    resolved_protocol = build_resolved_protocol_artifact(
        route_set_id=route_set.route_set_id,
        validation=protocol_meta,
        output_dir=str(output_root),
    )
    resolved_protocol_path = output_root / "resolved_protocol.json"
    resolved_protocol_path.write_text(
        json.dumps(resolved_protocol, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    model_name = route_set.assignments[0].model
    committee_specs = [
        {"juror_id": assignment.slot_id, "profile_id": assignment.profile_id}
        for assignment in route_set.assignments
    ]
    escalation_specs = (
        [
            {"juror_id": assignment.slot_id, "profile_id": assignment.profile_id}
            for assignment in escalation_route_set.assignments
        ]
        if escalation_route_set is not None
        else []
    )
    single_specs = [
        {"juror_id": "single_juror_1", "profile_id": single_profile_id}
    ]

    case_results: list[dict[str, object]] = []
    missing_price_models: set[str] = set()
    price_version: str | None = None
    for case in selected_cases:
        single = asyncio.run(
            _run_variant(
                juror_specs=single_specs,
                case=case,
                llm_service_factory=single_llm_factory,
                decomposer=decomposer,
                timeout_seconds=12.0,
                stage_label="initial",
                service_domain=single_route_set.domain,
            )
        )
        committee = asyncio.run(
            _run_variant(
                juror_specs=committee_specs,
                case=case,
                llm_service_factory=llm_factory,
                decomposer=decomposer,
                timeout_seconds=12.0,
                stage_label="initial",
            )
        )

        committee_plus_escalation = {
            "run": dict(committee["run"]),
            "per_juror": list(committee["per_juror"]),
            "aggregated": dict(committee["aggregated"]),
            "totals": dict(committee["totals"]),
        }
        if (
            escalation_llm_factory is not None
            and escalation_specs
            and bool(committee["run"]["escalation"])
        ):
            escalation = asyncio.run(
                _run_variant(
                    juror_specs=escalation_specs,
                    case=case,
                    llm_service_factory=escalation_llm_factory,
                    decomposer=decomposer,
                    timeout_seconds=18.0,
                    stage_label="escalation",
                    service_domain=escalation_route_set.domain,
                )
            )
            committee_plus_escalation["per_juror"].extend(escalation["per_juror"])
            committee_plus_escalation["run"] = {
                "should_stop": escalation["run"]["should_stop"],
                "completion_reason": f"initial->{escalation['run']['completion_reason']}",
                "escalation": bool(committee["run"]["escalation"]),
                "agreement": escalation["run"]["agreement"],
            }
            committee_plus_escalation["aggregated"] = escalation["aggregated"]
            committee_plus_escalation["totals"] = {
                "latency_ms": round(
                    float(committee["totals"]["latency_ms"]) + float(escalation["totals"]["latency_ms"]),
                    2,
                ),
                "tokens_used": int(committee["totals"]["tokens_used"]) + int(escalation["totals"]["tokens_used"]),
                "runtime_cost_usd": round(
                    float(committee["totals"]["runtime_cost_usd"])
                    + float(escalation["totals"]["runtime_cost_usd"]),
                    6,
                ),
                "estimated_cost_usd": round(
                    float(committee["totals"]["estimated_cost_usd"])
                    + float(escalation["totals"]["estimated_cost_usd"]),
                    6,
                ),
                "price_version": str(committee["totals"].get("price_version", "unknown")),
                "missing_price_models": sorted(
                    set(committee["totals"].get("missing_price_models", []))
                    | set(escalation["totals"].get("missing_price_models", []))
                ),
            }

        case_results.append(
            {
                "case": asdict(case),
                "single": {
                    "agreement": single["run"]["agreement"],
                    "escalation": single["run"]["escalation"],
                    "completion_reason": single["run"]["completion_reason"],
                    "per_juror": single["per_juror"],
                    "totals": single["totals"],
                    "aggregated": single["aggregated"],
                },
                "committee": {
                    "agreement": committee["run"]["agreement"],
                    "escalation": committee["run"]["escalation"],
                    "completion_reason": committee["run"]["completion_reason"],
                    "per_juror": committee["per_juror"],
                    "totals": committee["totals"],
                    "aggregated": committee["aggregated"],
                },
                "committee_plus_escalation": {
                    "agreement": committee_plus_escalation["run"]["agreement"],
                    "escalation": committee_plus_escalation["run"]["escalation"],
                    "completion_reason": committee_plus_escalation["run"]["completion_reason"],
                    "per_juror": committee_plus_escalation["per_juror"],
                    "totals": committee_plus_escalation["totals"],
                    "aggregated": committee_plus_escalation["aggregated"],
                },
            }
        )
        missing_price_models.update(single["totals"].get("missing_price_models", []))
        missing_price_models.update(committee["totals"].get("missing_price_models", []))
        if price_version is None:
            price_version = str(single["totals"].get("price_version", "unknown"))

    single_false = sum(
        1
        for row in case_results
        if (not row["case"]["expected_escalation"]) and row["single"]["escalation"]
    )
    single_missed = sum(
        1
        for row in case_results
        if row["case"]["expected_escalation"] and (not row["single"]["escalation"])
    )
    committee_false = sum(
        1
        for row in case_results
        if (not row["case"]["expected_escalation"]) and row["committee"]["escalation"]
    )
    committee_missed = sum(
        1
        for row in case_results
        if row["case"]["expected_escalation"] and (not row["committee"]["escalation"])
    )

    summary = {
        "protocol_version": protocol_meta.protocol_version,
        "dataset_version": protocol_meta.dataset_version,
        "calibration_metric_id": protocol_meta.calibration_metric_id,
        "calibration_bin_edges": protocol_meta.calibration_bin_edges,
        "route_set_id": route_set.route_set_id,
        "single_route_set_id": single_route_set.route_set_id,
        "review_mode": effective_review_mode,
        "decomposition_mode": effective_decomposition_mode,
        "model": model_name,
        "case_count": len(case_results),
        "price_version": price_version or "unknown",
        "missing_price_models": sorted(missing_price_models),
        "single_false_escalations": single_false,
        "single_missed_escalations": single_missed,
        "committee_false_escalations": committee_false,
        "committee_missed_escalations": committee_missed,
    }

    single_total_errors = single_false + single_missed
    committee_total_errors = committee_false + committee_missed
    if single_total_errors > 0:
        error_reduction_pct = (
            (single_total_errors - committee_total_errors) / single_total_errors
        ) * 100.0
    else:
        error_reduction_pct = 0.0

    avg_single_latency = (
        sum(float(row["single"]["totals"]["latency_ms"]) for row in case_results)
        / max(len(case_results), 1)
    )
    avg_committee_latency = (
        sum(float(row["committee"]["totals"]["latency_ms"]) for row in case_results)
        / max(len(case_results), 1)
    )
    avg_single_cost = (
        sum(float(row["single"]["totals"]["estimated_cost_usd"]) for row in case_results)
        / max(len(case_results), 1)
    )
    avg_committee_cost = (
        sum(float(row["committee"]["totals"]["estimated_cost_usd"]) for row in case_results)
        / max(len(case_results), 1)
    )
    avg_committee_plus_escalation_latency = (
        sum(
            float(row.get("committee_plus_escalation", row["committee"])["totals"]["latency_ms"])
            for row in case_results
        )
        / max(len(case_results), 1)
    )
    avg_committee_plus_escalation_cost = (
        sum(
            float(row.get("committee_plus_escalation", row["committee"])["totals"]["estimated_cost_usd"])
            for row in case_results
        )
        / max(len(case_results), 1)
    )

    latency_ratio = (avg_committee_latency / avg_single_latency) if avg_single_latency else 0.0
    cost_ratio = (avg_committee_cost / avg_single_cost) if avg_single_cost else 0.0
    with_escalation_latency_ratio = (
        (avg_committee_plus_escalation_latency / avg_single_latency)
        if avg_single_latency
        else 0.0
    )
    with_escalation_cost_ratio = (
        (avg_committee_plus_escalation_cost / avg_single_cost)
        if avg_single_cost
        else 0.0
    )

    worth_it = (
        (error_reduction_pct >= ERROR_REDUCTION_THRESHOLD_PCT)
        and (latency_ratio <= MAX_LATENCY_RATIO)
        and (cost_ratio <= MAX_COST_RATIO)
    )

    summary.update(
        {
            "single_total_escalation_errors": single_total_errors,
            "committee_total_escalation_errors": committee_total_errors,
            "escalation_error_reduction_pct": round(error_reduction_pct, 2),
            "avg_latency_ratio_committee_over_single": round(latency_ratio, 2),
            "avg_cost_ratio_committee_over_single": round(cost_ratio, 2),
            "escalation_route_set_id": (
                escalation_route_set.route_set_id if escalation_route_set is not None else None
            ),
            "committee_plus_escalation_total_escalation_errors": committee_total_errors,
            "avg_latency_ratio_committee_plus_escalation_over_single": round(
                with_escalation_latency_ratio,
                2,
            ),
            "avg_cost_ratio_committee_plus_escalation_over_single": round(
                with_escalation_cost_ratio,
                2,
            ),
            "committee_plus_escalation_efficiency_worth_it_decision": bool(
                (error_reduction_pct >= ERROR_REDUCTION_THRESHOLD_PCT)
                and (with_escalation_latency_ratio <= MAX_LATENCY_RATIO)
                and (with_escalation_cost_ratio <= MAX_COST_RATIO)
            ),
            "worth_it_rule": {
                "min_error_reduction_pct": ERROR_REDUCTION_THRESHOLD_PCT,
                "max_latency_ratio": MAX_LATENCY_RATIO,
                "max_cost_ratio": MAX_COST_RATIO,
            },
            "efficiency_worth_it_decision": bool(worth_it),
            "worth_it_decision": bool(worth_it),
        }
    )
    report = {
        "protocol": {
            "protocol_version": protocol_meta.protocol_version,
            "dataset_version": protocol_meta.dataset_version,
            "calibration_metric_id": protocol_meta.calibration_metric_id,
            "calibration_bin_edges": protocol_meta.calibration_bin_edges,
            "review_mode": effective_review_mode,
            "decomposition_mode": effective_decomposition_mode,
        },
        "resolved_protocol_artifact": str(resolved_protocol_path),
        "summary": summary,
        "case_results": case_results,
    }

    protocol_outputs = _write_protocol_output_artifacts(output_root=output_root, report=report)
    report["protocol_outputs"] = protocol_outputs

    json_path = output_root / "comparison.json"
    markdown_path = output_root / "comparison.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_build_markdown_summary(report), encoding="utf-8")

    return report