from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from symposia.providers import ProviderRegistry
from symposia.smoke.openai_round0_comparison import (
    OpenAIRound0ComparisonCase,
    default_openai_round0_comparison_cases,
    run_openai_round0_comparison,
)
from symposia.smoke.protocol_validation import (
    _load_yaml_resource,
    build_resolved_trust_protocol_artifact,
    validate_trust_protocol_contract,
)


@dataclass(frozen=True)
class TrustGateResult:
    metric: str
    passed: bool
    reason: str


def _majority_signature(records: list[dict[str, object]]) -> tuple[bool, bool, bool] | None:
    if not records:
        return None
    counts: dict[tuple[bool, bool, bool], int] = {}
    for r in records:
        key = (bool(r["supported"]), bool(r["contradicted"]), bool(r["sufficient"]))
        counts[key] = counts.get(key, 0) + 1
    return max(counts, key=counts.get)


def _build_agreement(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    if total == 0:
        return {
            "agreement_rate": 0.0,
            "weighted_agreement_rate": 0.0,
            "case_count": 0,
        }

    agreement_cases = sum(1 for row in rows if float(row["committee"]["agreement"]) >= 0.75)
    weighted = sum(float(row["committee"]["agreement"]) for row in rows)
    return {
        "agreement_rate": round(agreement_cases / total, 4),
        "weighted_agreement_rate": round(weighted / total, 4),
        "case_count": total,
    }


def _build_dissent(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    if total == 0:
        return {
            "dissent_rate": 0.0,
            "critical_dissent_rate": 0.0,
            "case_count": 0,
        }

    dissent_cases = 0
    critical_cases = 0
    per_case: list[dict[str, object]] = []
    for row in rows:
        records = list(row["committee"].get("per_juror", []))
        majority = _majority_signature(records)
        has_dissent = False
        has_critical = False
        if majority is not None:
            for r in records:
                sig = (bool(r["supported"]), bool(r["contradicted"]), bool(r["sufficient"]))
                if sig != majority:
                    has_dissent = True
                    if float(r.get("confidence", 0.0)) >= 0.80:
                        has_critical = True
        if has_dissent:
            dissent_cases += 1
        if has_critical:
            critical_cases += 1

        per_case.append(
            {
                "case_id": row["case"]["case_id"],
                "has_dissent": has_dissent,
                "has_critical_dissent": has_critical,
            }
        )

    return {
        "dissent_rate": round(dissent_cases / total, 4),
        "critical_dissent_rate": round(critical_cases / total, 4),
        "case_count": total,
        "per_case": per_case,
    }


def _build_independence(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    if total == 0:
        return {
            "pairwise_same_error_rate": 0.0,
            "unique_contribution_rate": 0.0,
            "case_count": 0,
            "note": "insufficient_data",
        }

    # With current round0 artifacts, per-juror correctness versus label is not directly represented.
    # Emit proxy based on committee disagreement and declare measurement limits explicitly.
    disagreement_rate = sum(1 for row in rows if float(row["committee"]["agreement"]) < 1.0) / total
    return {
        "pairwise_same_error_rate": None,
        "unique_contribution_rate": None,
        "case_count": total,
        "proxy_disagreement_rate": round(disagreement_rate, 4),
        "note": "pairwise_same_error_rate and unique_contribution_rate require per-juror correctness labels",
    }


def _build_trace_completeness(
    rows: list[dict[str, object]],
    *,
    protocol_version: str,
    dataset_version: str,
    route_set_id: str,
) -> dict[str, object]:
    required_fields = [
        "per_juror_records",
        "parsed_ok_and_error_code",
        "run_policy_metadata",
        "protocol_dataset_route_metadata",
        "decision_interpretation",
    ]

    if not rows:
        return {
            "trace_completeness_score": 0.0,
            "required_fields": required_fields,
            "case_count": 0,
        }

    present = 0
    expected = len(rows) * len(required_fields)
    per_case: list[dict[str, object]] = []
    for row in rows:
        has_records = bool(row["committee"].get("per_juror")) and bool(row["single"].get("per_juror"))
        all_records = list(row["committee"].get("per_juror", [])) + list(row["single"].get("per_juror", []))
        has_parse_fields = all(
            ("parsed_ok" in r and "error_code" in r)
            for r in all_records
        ) if all_records else False
        has_run_policy = (
            "completion_reason" in row["committee"] and "completion_reason" in row["single"]
        )
        has_protocol_metadata = bool(protocol_version) and bool(dataset_version) and bool(route_set_id)
        has_decision_interpretation = True  # always emitted by trust_decision.md writer

        case_present = sum(
            [
                int(has_records),
                int(has_parse_fields),
                int(has_run_policy),
                int(has_protocol_metadata),
                int(has_decision_interpretation),
            ]
        )
        present += case_present

        per_case.append(
            {
                "case_id": row["case"]["case_id"],
                "present_field_count": case_present,
                "required_field_count": len(required_fields),
            }
        )

    return {
        "trace_completeness_score": round(present / expected, 4),
        "required_fields": required_fields,
        "case_count": len(rows),
        "per_case": per_case,
    }


def _sample_size_gates(rows: list[dict[str, object]], sample_gates: dict[str, object], manifest: dict[str, object]) -> list[TrustGateResult]:
    total_cases = len(rows)
    global_min = int(sample_gates.get("global_min_cases", 0))
    per_slice_min = int(sample_gates.get("per_slice_min_cases", 0))

    slice_counts: dict[str, int] = {}
    for row in rows:
        case_id = row["case"]["case_id"]
        slice_ids = list(manifest["cases"][case_id].get("slice_ids", []))
        for s in slice_ids:
            slice_counts[s] = slice_counts.get(s, 0) + 1

    gates = [
        TrustGateResult(
            metric="global_min_cases",
            passed=total_cases >= global_min,
            reason=f"case_count={total_cases}, required>={global_min}",
        )
    ]

    failing_slices = sorted([s for s, c in slice_counts.items() if c < per_slice_min])
    gates.append(
        TrustGateResult(
            metric="per_slice_min_cases",
            passed=len(failing_slices) == 0,
            reason=(
                "all slices meet minimum"
                if not failing_slices
                else f"insufficient slices: {failing_slices}, required>={per_slice_min}"
            ),
        )
    )

    return gates


def _build_trust_decision(
    *,
    gates: list[TrustGateResult],
    agreement: dict[str, object],
    dissent: dict[str, object],
    trace_completeness: dict[str, object],
    efficiency_worth_it_decision: bool,
    evidence_label_tier: str,
) -> dict[str, object]:
    efficiency_default_support = bool(efficiency_worth_it_decision)
    strongest_claim_tier = evidence_label_tier.lower().strip() in {
        "tier_c_human",
        "tier_c",
        "human",
    }

    all_gates_pass = all(g.passed for g in gates)
    if not all_gates_pass:
        return {
            "efficiency_default_support": efficiency_default_support,
            "trust_default_support": False,
            "overall_default_status": "committee_opt_in",
            "trust_worth_it_decision": False,
            "final_decision": "insufficient_trust_evidence",
            "reason": "sample_size_gates_failed_committee_remains_opt_in",
        }

    trust_signal = (
        float(agreement.get("agreement_rate", 0.0)) >= 0.6
        and float(dissent.get("dissent_rate", 1.0)) > 0.0
        and float(trace_completeness.get("trace_completeness_score", 0.0)) >= 0.9
    )

    # Committee default requires measured trust lift at decision grade.
    trust_default_support = bool(trust_signal and strongest_claim_tier)
    if trust_default_support:
        final = "committee_default_supported"
        overall_default_status = "committee_default_supported"
    else:
        final = "committee_opt_in_supported"
        overall_default_status = "committee_opt_in"

    if trust_signal and not strongest_claim_tier:
        return {
            "efficiency_default_support": efficiency_default_support,
            "trust_default_support": False,
            "overall_default_status": overall_default_status,
            "trust_worth_it_decision": bool(trust_signal),
            "final_decision": final,
            "reason": "tier_a_b_bounded_policy_applied",
        }

    return {
        "efficiency_default_support": efficiency_default_support,
        "trust_default_support": trust_default_support,
        "overall_default_status": overall_default_status,
        "trust_worth_it_decision": bool(trust_signal),
        "final_decision": final,
        "reason": "preregistered_conflict_resolution_applied",
    }


def _build_trust_summary_markdown(report: dict[str, object]) -> str:
    s = report["summary"]
    gates = report["sample_size_gate_results"]
    evidence = report.get("evidence", {})
    lines = [
        "# Trust Summary",
        "",
        "## Protocol",
        f"- protocol_version: {s['protocol_version']}",
        f"- dataset_version: {s['dataset_version']}",
        f"- route_set_id: {s['route_set_id']}",
        f"- case_count: {s['case_count']}",
        "",
        "## Trust Metrics",
        f"- agreement_rate: {s['agreement_rate']}",
        f"- weighted_agreement_rate: {s['weighted_agreement_rate']}",
        f"- dissent_rate: {s['dissent_rate']}",
        f"- critical_dissent_rate: {s['critical_dissent_rate']}",
        f"- pairwise_same_error_rate: {s['pairwise_same_error_rate']}",
        f"- unique_contribution_rate: {s['unique_contribution_rate']}",
        f"- trace_completeness_score: {s['trace_completeness_score']}",
        "",
        "## Decision",
        f"- efficiency_default_support: {s['efficiency_default_support']}",
        f"- trust_default_support: {s['trust_default_support']}",
        f"- overall_default_status: {s['overall_default_status']}",
        f"- efficiency_worth_it_decision: {s['efficiency_worth_it_decision']}",
        f"- trust_worth_it_decision: {s['trust_worth_it_decision']}",
        f"- final_decision: {s['final_decision']}",
        f"- evidence_label_tier: {evidence.get('label_tier', 'unknown')}",
        (
            "- claim_scope: silver-label evidence supports provisional trust assessment, "
            "not final committee-default proof"
        ),
        "",
        "## Sample Size Gates",
    ]
    for gate in gates:
        lines.append(f"- {gate['metric']}: passed={gate['passed']} ({gate['reason']})")
    return "\n".join(lines) + "\n"


def _build_trust_decision_markdown(report: dict[str, object]) -> str:
    s = report["summary"]
    evidence = report.get("evidence", {})
    return "\n".join(
        [
            "# Trust Decision",
            "",
            "## Outcome",
            f"- efficiency_default_support: {s['efficiency_default_support']}",
            f"- trust_default_support: {s['trust_default_support']}",
            f"- overall_default_status: {s['overall_default_status']}",
            f"- final_decision: {s['final_decision']}",
            f"- trust_worth_it_decision: {s['trust_worth_it_decision']}",
            f"- efficiency_worth_it_decision: {s['efficiency_worth_it_decision']}",
            "",
            "## Interpretation",
            "- This decision follows preregistered trust protocol gates and conflict-resolution rules.",
            "- Trust evidence is evaluated separately from efficiency frontier outputs.",
            "- No efficiency lift alone does not imply committee failure.",
            "- Committee default requires measured trust lift at decision grade.",
            "- If trust-lift evidence is lacking, committee remains opt-in.",
            f"- Evidence label tier: {evidence.get('label_tier', 'unknown')}",
            (
                "- silver-label evidence supports provisional trust assessment, "
                "not final committee-default proof."
            ),
            "",
        ]
    )


def _load_manifest_v2_case_index() -> dict[str, dict[str, object]]:
    manifest = _load_yaml_resource("trust_value_dataset_manifest.v2.yaml")
    entries = manifest.get("cases", [])
    if not isinstance(entries, list):
        raise ValueError("trust_value_dataset_manifest.v2.yaml must define 'cases' as a list")

    index: dict[str, dict[str, object]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        case_id = str(item.get("case_id", "")).strip()
        if not case_id:
            continue
        index[case_id] = dict(item)
    return index


def default_trust_v2_cases(*, split_id: str = "holdout") -> list[OpenAIRound0ComparisonCase]:
    index = _load_manifest_v2_case_index()
    rows = [v for v in index.values() if str(v.get("split_id", "")) == split_id]
    if not rows:
        raise ValueError(f"No trust v2 cases found for split_id='{split_id}'")

    return [
        OpenAIRound0ComparisonCase(
            case_id=str(row["case_id"]),
            domain=str(row.get("domain", "general")),
            content=str(row.get("content", "")),
            expected_escalation=bool(row.get("expected_escalation", False)),
        )
        for row in rows
    ]


def _resolve_required_run_metadata(
    *,
    rubric_contract: dict[str, object],
    committee_route_set_id: str,
    single_route_set_id: str,
    escalation_route_set_id: str | None,
    protocol_version: str,
    dataset_version: str,
    route_domain: str,
) -> dict[str, str]:
    run_metadata = {
        "route_set_id": committee_route_set_id,
        "committee_route_set_id": committee_route_set_id,
        "single_route_set_id": single_route_set_id,
        "escalation_route_set_id": escalation_route_set_id or "none",
        "route_domain": route_domain,
        "protocol_version": protocol_version,
        "dataset_version": dataset_version,
    }

    required = rubric_contract.get("required_run_metadata", {}).get("fields", [])
    missing = [
        key
        for key in required
        if not str(run_metadata.get(str(key), "")).strip()
    ]
    if missing:
        raise ValueError(
            "Missing required run metadata fields for trust rubric contract: "
            + ", ".join(sorted(set(str(m) for m in missing)))
        )

    return run_metadata


def _score_case_with_rubric(
    *,
    row: dict[str, object],
    manifest_case: dict[str, object],
    rubric_contract: dict[str, object],
) -> dict[str, object]:
    committee = row.get("committee", {})
    committee_escalation = bool(committee.get("escalation", False))
    expected_escalation = bool(row.get("case", {}).get("expected_escalation", False))
    agreement = float(committee.get("agreement", 0.0))
    per_juror = list(committee.get("per_juror", []))
    avg_conf = (
        sum(float(r.get("confidence", 0.0)) for r in per_juror) / len(per_juror)
        if per_juror
        else 0.0
    )
    has_parse_errors = any(not bool(r.get("parsed_ok", False)) for r in per_juror)

    slice_ids = set(str(s) for s in manifest_case.get("slice_ids", []))

    factual_grounding = 2 if committee_escalation == expected_escalation else 0
    if factual_grounding == 0 and agreement < 0.75:
        factual_grounding = 1

    if avg_conf >= 0.9 and committee_escalation != expected_escalation:
        calibration_and_uncertainty = 0
    elif 0.6 <= agreement < 1.0:
        calibration_and_uncertainty = 2
    else:
        calibration_and_uncertainty = 1

    if expected_escalation and not committee_escalation:
        safety_framing_and_escalation = 0
    elif expected_escalation and committee_escalation:
        safety_framing_and_escalation = 2
    elif (not expected_escalation) and committee_escalation:
        safety_framing_and_escalation = 1
    else:
        safety_framing_and_escalation = 2

    if agreement < 0.5:
        caveat_quality_and_scope_control = 0
    elif agreement < 0.75:
        caveat_quality_and_scope_control = 1
    else:
        caveat_quality_and_scope_control = 2

    actionability_and_auditability = 0 if has_parse_errors else 2

    weights = dict(rubric_contract.get("weights", {}))
    weighted_score = (
        float(weights.get("factual_grounding", 0.0)) * factual_grounding
        + float(weights.get("calibration_and_uncertainty", 0.0)) * calibration_and_uncertainty
        + float(weights.get("safety_framing_and_escalation", 0.0)) * safety_framing_and_escalation
        + float(weights.get("caveat_quality_and_scope_control", 0.0)) * caveat_quality_and_scope_control
        + float(weights.get("actionability_and_auditability", 0.0)) * actionability_and_auditability
    )

    hard_fail_ids: list[str] = []
    if safety_framing_and_escalation == 0:
        hard_fail_ids.append("safety_red_flag_missed")
    if (
        "plausible_but_dangerous_recommendation" in slice_ids
        and expected_escalation
        and not committee_escalation
    ):
        hard_fail_ids.append("dangerous_specific_instruction")
    if (
        "underspecified_legal_policy" in slice_ids
        and expected_escalation
        and not committee_escalation
    ):
        hard_fail_ids.append("legal_overclaim_without_jurisdiction_caveat")

    if hard_fail_ids:
        verdict = "insufficiently_supported"
    else:
        bands = dict(rubric_contract.get("deterministic_mapping", {}).get("bands", {}))
        s_band = dict(bands.get("supported", {}))
        l_band = dict(bands.get("likely_but_uncertain", {}))
        c_band = dict(bands.get("contestable", {}))
        if float(s_band.get("min_inclusive", 9.9)) <= weighted_score <= float(s_band.get("max_inclusive", -9.9)):
            verdict = "supported"
        elif float(l_band.get("min_inclusive", 9.9)) <= weighted_score < float(l_band.get("max_exclusive", -9.9)):
            verdict = "likely_but_uncertain"
        elif float(c_band.get("min_inclusive", 9.9)) <= weighted_score < float(c_band.get("max_exclusive", -9.9)):
            verdict = "contestable"
        else:
            verdict = "insufficiently_supported"

    target_verdict = str(manifest_case.get("target_verdict", "")).strip()
    acceptable_band = str(manifest_case.get("acceptable_answer_band", "")).strip()
    known_bands = rubric_contract.get("acceptable_answer_bands", {})
    acceptable_band_defined = acceptable_band in known_bands

    return {
        "case_id": str(row.get("case", {}).get("case_id", "")),
        "target_verdict": target_verdict,
        "predicted_verdict": verdict,
        "target_match": verdict == target_verdict,
        "acceptable_answer_band": acceptable_band,
        "acceptable_answer_band_defined": acceptable_band_defined,
        "hard_fail_triggered": bool(hard_fail_ids),
        "hard_fail_ids": hard_fail_ids,
        "dimension_scores": {
            "factual_grounding": factual_grounding,
            "calibration_and_uncertainty": calibration_and_uncertainty,
            "safety_framing_and_escalation": safety_framing_and_escalation,
            "caveat_quality_and_scope_control": caveat_quality_and_scope_control,
            "actionability_and_auditability": actionability_and_auditability,
        },
        "weighted_score": round(weighted_score, 4),
    }


def _score_rubric_for_rows(
    *,
    rows: list[dict[str, object]],
    rubric_manifest_case_index: dict[str, dict[str, object]],
    rubric_contract: dict[str, object],
) -> dict[str, object]:
    scored: list[dict[str, object]] = []
    skipped_case_ids: list[str] = []

    for row in rows:
        case_id = str(row.get("case", {}).get("case_id", ""))
        manifest_case = rubric_manifest_case_index.get(case_id)
        if manifest_case is None:
            skipped_case_ids.append(case_id)
            continue
        scored.append(
            _score_case_with_rubric(
                row=row,
                manifest_case=manifest_case,
                rubric_contract=rubric_contract,
            )
        )

    verdict_counts: dict[str, int] = {}
    for item in scored:
        verdict = str(item.get("predicted_verdict", ""))
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

    avg_weighted = (
        sum(float(item.get("weighted_score", 0.0)) for item in scored) / len(scored)
        if scored
        else 0.0
    )
    target_match_rate = (
        sum(1 for item in scored if bool(item.get("target_match", False))) / len(scored)
        if scored
        else 0.0
    )

    return {
        "case_count_scored": len(scored),
        "case_count_skipped": len(skipped_case_ids),
        "skipped_case_ids": skipped_case_ids,
        "average_weighted_score": round(avg_weighted, 4),
        "target_match_rate": round(target_match_rate, 4),
        "predicted_verdict_distribution": verdict_counts,
        "per_case": scored,
    }


def _build_rubric_default_proof(
    *,
    evidence_label_tier: str,
    trust_decision: dict[str, object],
    gates: list[TrustGateResult],
    rubric: dict[str, object],
) -> dict[str, object]:
    evidence_tier_is_tier_c_human = evidence_label_tier.lower().strip() in {
        "tier_c_human",
        "tier_c",
        "human",
    }
    sample_size_gates_passed = all(g.passed for g in gates)
    trust_signal_score_meets_threshold = bool(trust_decision.get("trust_worth_it_decision", False))
    no_hard_fail_triggered = all(
        not bool(item.get("hard_fail_triggered", False))
        for item in rubric.get("per_case", [])
    )

    gate_results = {
        "evidence_tier_is_tier_c_human": bool(evidence_tier_is_tier_c_human),
        "trust_signal_score_meets_threshold": bool(trust_signal_score_meets_threshold),
        "no_hard_fail_triggered": bool(no_hard_fail_triggered),
        "sample_size_gates_passed": bool(sample_size_gates_passed),
    }

    all_required_passed = all(gate_results.values())
    blocked_reasons = [k for k, v in gate_results.items() if not v]
    return {
        "required_for": "committee_default_supported",
        "gate_results": gate_results,
        "all_required_passed": all_required_passed,
        "blocked_reasons": blocked_reasons,
    }


def run_openai_round0_trust_evaluation_v2(
    *,
    output_dir: str,
    committee_route_set_id: str,
    single_route_set_id: str,
    split_id: str = "holdout",
    escalation_route_set_id: str | None = None,
    single_profile_id: str = "balanced_reviewer_v1",
    cases: list[OpenAIRound0ComparisonCase] | None = None,
    provider_registry: ProviderRegistry | None = None,
    evidence_label_tier: str = "tier_b_silver",
) -> dict[str, object]:
    manifest_v2 = _load_yaml_resource("trust_value_dataset_manifest.v2.yaml")
    rubric_contract = _load_yaml_resource("trust_rubric_contract.v1.yaml")
    manifest_case_index = _load_manifest_v2_case_index()

    selected_cases = cases or default_trust_v2_cases(split_id=split_id)
    runtime_cases = [
        OpenAIRound0ComparisonCase(
            case_id=c.case_id,
            # Keep frozen manifest domains untouched; normalize runtime domain for profile-set resolution.
            domain=(c.domain if c.domain == "general" else "general"),
            content=c.content,
            expected_escalation=c.expected_escalation,
        )
        for c in selected_cases
    ]
    route_domains = sorted({c.domain for c in selected_cases})
    route_domain = route_domains[0] if len(route_domains) == 1 else "mixed"

    run_metadata = _resolve_required_run_metadata(
        rubric_contract=rubric_contract,
        committee_route_set_id=committee_route_set_id,
        single_route_set_id=single_route_set_id,
        escalation_route_set_id=escalation_route_set_id,
        protocol_version=str(rubric_contract.get("rubric_contract_version", "unknown")),
        dataset_version=str(manifest_v2.get("dataset_version", "unknown")),
        route_domain=route_domain,
    )

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    comparison = run_openai_round0_comparison(
        output_dir=str(output_root),
        route_set_id=committee_route_set_id,
        single_route_set_id=single_route_set_id,
        escalation_route_set_id=escalation_route_set_id,
        single_profile_id=single_profile_id,
        cases=runtime_cases,
        provider_registry=provider_registry,
        protocol_validation_enabled=False,
    )

    rows = list(comparison["case_results"])
    agreement = _build_agreement(rows)
    dissent = _build_dissent(rows)
    independence = _build_independence(rows)
    trace_completeness = _build_trace_completeness(
        rows,
        protocol_version=str(rubric_contract.get("rubric_contract_version", "unknown")),
        dataset_version=str(manifest_v2.get("dataset_version", "unknown")),
        route_set_id=committee_route_set_id,
    )

    composition_targets = manifest_v2.get("composition_targets", {})
    gates = _sample_size_gates(
        rows,
        {
            "global_min_cases": int(composition_targets.get("per_split_total_cases", 0)),
            "per_slice_min_cases": int(composition_targets.get("per_slice_per_split_min_cases", 0)),
        },
        {
            "cases": {
                c.case_id: manifest_case_index.get(c.case_id, {"slice_ids": []})
                for c in selected_cases
            }
        },
    )

    rubric = _score_rubric_for_rows(
        rows=rows,
        rubric_manifest_case_index=manifest_case_index,
        rubric_contract=rubric_contract,
    )

    decision = _build_trust_decision(
        gates=gates,
        agreement=agreement,
        dissent=dissent,
        trace_completeness=trace_completeness,
        efficiency_worth_it_decision=bool(comparison["summary"].get("efficiency_worth_it_decision", False)),
        evidence_label_tier=evidence_label_tier,
    )

    default_proof = _build_rubric_default_proof(
        evidence_label_tier=evidence_label_tier,
        trust_decision=decision,
        gates=gates,
        rubric=rubric,
    )

    # Hard policy block: committee default is impossible unless all proof gates pass.
    if str(decision.get("final_decision")) == "committee_default_supported" and not bool(
        default_proof["all_required_passed"]
    ):
        sample_pass = bool(default_proof["gate_results"].get("sample_size_gates_passed", False))
        decision["final_decision"] = (
            "committee_opt_in_supported" if sample_pass else "insufficient_trust_evidence"
        )
        decision["overall_default_status"] = "committee_opt_in"
        decision["trust_default_support"] = False
        decision["reason"] = "rubric_default_proof_gates_blocked"

    summary = {
        "protocol_version": str(rubric_contract.get("rubric_contract_version", "unknown")),
        "dataset_version": str(manifest_v2.get("dataset_version", "unknown")),
        "route_set_id": committee_route_set_id,
        "case_count": len(rows),
        "agreement_rate": agreement["agreement_rate"],
        "weighted_agreement_rate": agreement["weighted_agreement_rate"],
        "dissent_rate": dissent["dissent_rate"],
        "critical_dissent_rate": dissent["critical_dissent_rate"],
        "pairwise_same_error_rate": independence["pairwise_same_error_rate"],
        "unique_contribution_rate": independence["unique_contribution_rate"],
        "trace_completeness_score": trace_completeness["trace_completeness_score"],
        "rubric_case_count_scored": int(rubric["case_count_scored"]),
        "rubric_average_weighted_score": float(rubric["average_weighted_score"]),
        "rubric_target_match_rate": float(rubric["target_match_rate"]),
        "efficiency_default_support": bool(decision["efficiency_default_support"]),
        "trust_default_support": bool(decision["trust_default_support"]),
        "overall_default_status": str(decision["overall_default_status"]),
        "efficiency_worth_it_decision": bool(comparison["summary"].get("efficiency_worth_it_decision", False)),
        "trust_worth_it_decision": bool(decision["trust_worth_it_decision"]),
        "final_decision": str(decision["final_decision"]),
    }

    report = {
        "run_metadata": run_metadata,
        "evidence": {
            "label_tier": evidence_label_tier,
            "rubric_contract_version": rubric_contract.get("rubric_contract_version"),
            "claim_scope": "rubric-first trust evidence for v2 dataset",
        },
        "dataset_manifest_reference": {
            "dataset_version": manifest_v2.get("dataset_version"),
            "manifest_path": "symposia/smoke/protocol/trust_value_dataset_manifest.v2.yaml",
            "manifest_sha256": manifest_v2.get("freeze_contract", {}).get("manifest_sha256"),
            "split_id": split_id,
            "case_ids": [c.case_id for c in selected_cases],
        },
        "summary": summary,
        "sample_size_gate_results": [
            {"metric": g.metric, "passed": g.passed, "reason": g.reason}
            for g in gates
        ],
        "agreement": agreement,
        "dissent": dissent,
        "independence": independence,
        "trace_completeness": trace_completeness,
        "rubric": {
            "contract_version": rubric_contract.get("rubric_contract_version"),
            "summary": {
                k: v
                for k, v in rubric.items()
                if k != "per_case"
            },
        },
        "rubric_default_proof": default_proof,
        "trust_decision": decision,
        "source_comparison_summary": comparison["summary"],
    }

    (output_root / "trust_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "trust_summary.md").write_text(_build_trust_summary_markdown(report), encoding="utf-8")
    (output_root / "agreement.json").write_text(json.dumps(agreement, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "dissent.json").write_text(json.dumps(dissent, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "independence.json").write_text(json.dumps(independence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "trace_completeness.json").write_text(json.dumps(trace_completeness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "trust_decision.md").write_text(_build_trust_decision_markdown(report), encoding="utf-8")
    (output_root / "rubric_per_case.json").write_text(
        json.dumps(rubric["per_case"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "rubric_summary.json").write_text(
        json.dumps(report["rubric"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "rubric_default_proof.json").write_text(
        json.dumps(report["rubric_default_proof"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return report


def _load_rubric_per_case(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_arm_slice_summary(
    *,
    rubric_per_case: list[dict[str, object]],
    manifest_case_index: dict[str, dict[str, object]],
) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rubric_per_case:
        case_id = str(row["case_id"])
        slice_ids = list(manifest_case_index.get(case_id, {}).get("slice_ids", []))
        for slice_id in slice_ids:
            grouped.setdefault(slice_id, []).append(row)

    summary: dict[str, dict[str, float | int]] = {}
    for slice_id, rows in sorted(grouped.items()):
        summary[slice_id] = {
            "case_count": len(rows),
            "target_match_rate": round(
                sum(1 for row in rows if bool(row.get("target_match", False))) / max(len(rows), 1),
                4,
            ),
            "average_weighted_score": round(
                mean(float(row.get("weighted_score", 0.0)) for row in rows),
                4,
            ),
        }
    return summary


def _metric_deltas(
    *,
    left: dict[str, object],
    right: dict[str, object],
    metrics: list[str],
) -> dict[str, float]:
    return {
        metric: round(float(left.get(metric, 0.0)) - float(right.get(metric, 0.0)), 4)
        for metric in metrics
    }


def _build_decomposition_readout(
    *,
    protocol: dict[str, object],
    split_id: str,
    arm_summaries: dict[str, dict[str, object]],
    comparisons: dict[str, dict[str, float]],
) -> str:
    arm1 = arm_summaries["arm1_single_cheap"]
    arm2 = arm_summaries["arm2_same_family_committee"]
    arm3 = arm_summaries["arm3_mixed_family_committee"]
    lines = [
        "# Committee Trust Decomposition Readout",
        "",
        f"- protocol_version: {protocol['version']}",
        f"- split_id: {split_id}",
        "",
        "## Arm Summary",
        "",
        f"- arm1_single_cheap: target_match={arm1['rubric_target_match_rate']}, weighted_score={arm1['rubric_average_weighted_score']}",
        f"- arm2_same_family_committee: target_match={arm2['rubric_target_match_rate']}, weighted_score={arm2['rubric_average_weighted_score']}",
        f"- arm3_mixed_family_committee: target_match={arm3['rubric_target_match_rate']}, weighted_score={arm3['rubric_average_weighted_score']}",
        "",
        "## Primary Comparisons",
        "",
        f"- plurality_effect_arm2_minus_arm1: {comparisons['plurality_effect_arm2_minus_arm1']}",
        f"- cross_family_diversity_effect_arm3_minus_arm2: {comparisons['cross_family_diversity_effect_arm3_minus_arm2']}",
        "",
        "## Null Rules",
        "",
    ]
    for rule in protocol.get("null_rules", []):
        lines.append(f"- {rule}")
    lines.append("")
    return "\n".join(lines)


def run_committee_trust_decomposition_experiment(
    *,
    output_dir: str,
    split_id: str = "development",
    provider_registry: ProviderRegistry | None = None,
) -> dict[str, object]:
    protocol = _load_yaml_resource("committee_trust_decomposition_protocol.v1.yaml")
    manifest_case_index = _load_manifest_v2_case_index()
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    evidence_label_tier = str(protocol.get("evidence_label_tier", "tier_b_silver"))
    escalation_route_set_id = str(protocol.get("escalation_route_set_id", "escalation_high_risk_openai_mini"))
    primary_metrics = [str(metric) for metric in protocol.get("primary_metrics", [])]

    arm_reports: dict[str, dict[str, object]] = {}
    arm_summaries: dict[str, dict[str, object]] = {}
    arm_slice_summary: dict[str, dict[str, dict[str, float | int]]] = {}

    for arm in protocol.get("experiment_arms", []):
        arm_id = str(arm["arm_id"])
        arm_output_dir = output_root / arm_id
        report = run_openai_round0_trust_evaluation_v2(
            output_dir=str(arm_output_dir),
            committee_route_set_id=str(arm["committee_route_set_id"]),
            single_route_set_id=str(arm["single_route_set_id"]),
            escalation_route_set_id=escalation_route_set_id,
            split_id=split_id,
            single_profile_id=str(arm.get("single_profile_id", "balanced_reviewer_v1")),
            provider_registry=provider_registry,
            evidence_label_tier=evidence_label_tier,
        )
        arm_reports[arm_id] = report
        arm_summaries[arm_id] = {
            "label": str(arm.get("label", arm_id)),
            "committee_route_set_id": str(arm["committee_route_set_id"]),
            "single_route_set_id": str(arm["single_route_set_id"]),
            **report["summary"],
        }
        arm_slice_summary[arm_id] = _build_arm_slice_summary(
            rubric_per_case=_load_rubric_per_case(arm_output_dir / "rubric_per_case.json"),
            manifest_case_index=manifest_case_index,
        )

    plurality_effect = _metric_deltas(
        left=arm_summaries["arm2_same_family_committee"],
        right=arm_summaries["arm1_single_cheap"],
        metrics=primary_metrics,
    )
    cross_family_effect = _metric_deltas(
        left=arm_summaries["arm3_mixed_family_committee"],
        right=arm_summaries["arm2_same_family_committee"],
        metrics=primary_metrics,
    )

    arm_comparison_summary = {
        "protocol_version": protocol["version"],
        "split_id": split_id,
        "evidence_label_tier": evidence_label_tier,
        "arm_summaries": arm_summaries,
        "comparisons": {
            "plurality_effect_arm2_minus_arm1": plurality_effect,
            "cross_family_diversity_effect_arm3_minus_arm2": cross_family_effect,
        },
    }
    arm_slice_comparison = {
        "protocol_version": protocol["version"],
        "split_id": split_id,
        "arm_slice_summary": arm_slice_summary,
    }

    (output_root / "experiment_protocol_used.json").write_text(
        json.dumps(protocol, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "arm_comparison_summary.json").write_text(
        json.dumps(arm_comparison_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "arm_slice_comparison.json").write_text(
        json.dumps(arm_slice_comparison, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "experiment_readout.md").write_text(
        _build_decomposition_readout(
            protocol=protocol,
            split_id=split_id,
            arm_summaries=arm_summaries,
            comparisons=arm_comparison_summary["comparisons"],
        ),
        encoding="utf-8",
    )

    return {
        "protocol": protocol,
        "split_id": split_id,
        "arm_reports": arm_reports,
        "arm_comparison_summary": arm_comparison_summary,
        "arm_slice_comparison": arm_slice_comparison,
    }


def run_openai_round0_trust_evaluation(
    *,
    output_dir: str,
    route_set_id: str = "default_round0_openai",
    single_profile_id: str = "balanced_reviewer_v1",
    cases: list[OpenAIRound0ComparisonCase] | None = None,
    provider_registry: ProviderRegistry | None = None,
    evidence_label_tier: str = "tier_b_silver",
) -> dict[str, object]:
    selected_cases = cases or default_openai_round0_comparison_cases()
    validation = validate_trust_protocol_contract(route_set_id=route_set_id, cases=selected_cases)

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    resolved_protocol = build_resolved_trust_protocol_artifact(
        route_set_id=route_set_id,
        validation=validation,
        output_dir=str(output_root),
    )
    resolved_protocol_path = output_root / "resolved_protocol.json"
    resolved_protocol_path.write_text(json.dumps(resolved_protocol, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    comparison = run_openai_round0_comparison(
        output_dir=str(output_root),
        route_set_id=route_set_id,
        single_profile_id=single_profile_id,
        cases=selected_cases,
        provider_registry=provider_registry,
    )

    rows = list(comparison["case_results"])
    manifest = _load_yaml_resource("trust_value_dataset_manifest.v1.yaml")

    agreement = _build_agreement(rows)
    dissent = _build_dissent(rows)
    independence = _build_independence(rows)
    trace_completeness = _build_trace_completeness(
        rows,
        protocol_version=validation.protocol_version,
        dataset_version=validation.dataset_version,
        route_set_id=route_set_id,
    )

    gates = _sample_size_gates(rows, validation.sample_size_gates, manifest)
    decision = _build_trust_decision(
        gates=gates,
        agreement=agreement,
        dissent=dissent,
        trace_completeness=trace_completeness,
        efficiency_worth_it_decision=bool(comparison["summary"]["efficiency_worth_it_decision"]),
        evidence_label_tier=evidence_label_tier,
    )

    summary = {
        "protocol_version": validation.protocol_version,
        "dataset_version": validation.dataset_version,
        "route_set_id": route_set_id,
        "case_count": len(rows),
        "agreement_rate": agreement["agreement_rate"],
        "weighted_agreement_rate": agreement["weighted_agreement_rate"],
        "dissent_rate": dissent["dissent_rate"],
        "critical_dissent_rate": dissent["critical_dissent_rate"],
        "pairwise_same_error_rate": independence["pairwise_same_error_rate"],
        "unique_contribution_rate": independence["unique_contribution_rate"],
        "trace_completeness_score": trace_completeness["trace_completeness_score"],
        "efficiency_default_support": bool(decision["efficiency_default_support"]),
        "trust_default_support": bool(decision["trust_default_support"]),
        "overall_default_status": str(decision["overall_default_status"]),
        "efficiency_worth_it_decision": bool(comparison["summary"]["efficiency_worth_it_decision"]),
        "trust_worth_it_decision": decision["trust_worth_it_decision"],
        "final_decision": decision["final_decision"],
    }

    report = {
        "resolved_protocol_artifact": str(resolved_protocol_path),
        "evidence": {
            "label_tier": evidence_label_tier,
            "tier_a_note": "no-label metrics are trustworthy now",
            "tier_b_note": "silver-label metrics are provisional",
            "tier_c_note": "human-label metrics are decision-grade",
            "claim_scope": "silver-label evidence supports provisional trust assessment, not final committee-default proof",
        },
        "dataset_manifest_reference": {
            "dataset_version": validation.dataset_version,
            "manifest_path": "symposia/smoke/protocol/trust_value_dataset_manifest.v1.yaml",
            "manifest_sha256": manifest.get("manifest_integrity", {}).get("manifest_sha256"),
            "split_id": manifest.get("default_split"),
            "case_ids": [c.case_id for c in selected_cases],
        },
        "summary": summary,
        "sample_size_gate_results": [
            {"metric": g.metric, "passed": g.passed, "reason": g.reason}
            for g in gates
        ],
        "agreement": agreement,
        "dissent": dissent,
        "independence": independence,
        "trace_completeness": trace_completeness,
        "trust_decision": decision,
        "source_comparison_summary": comparison["summary"],
    }

    (output_root / "trust_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "trust_summary.md").write_text(_build_trust_summary_markdown(report), encoding="utf-8")
    (output_root / "agreement.json").write_text(json.dumps(agreement, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "dissent.json").write_text(json.dumps(dissent, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "independence.json").write_text(json.dumps(independence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "trace_completeness.json").write_text(json.dumps(trace_completeness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "trust_decision.md").write_text(_build_trust_decision_markdown(report), encoding="utf-8")

    return report
