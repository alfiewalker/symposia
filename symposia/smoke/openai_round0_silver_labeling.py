from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from symposia.smoke.openai_round0_comparison import (
    OpenAIRound0ComparisonCase,
    default_openai_round0_comparison_cases,
    run_openai_round0_comparison,
)
from symposia.smoke.protocol_validation import _load_yaml_resource


@dataclass(frozen=True)
class SilverLabelCandidate:
    case_id: str
    domain: str
    content: str
    expected_escalation: bool
    split_id: str
    slice_ids: list[str]
    source_type: str
    provenance_reference: str


def default_trust_silver_candidates() -> list[SilverLabelCandidate]:
    manifest = _load_yaml_resource("trust_value_dataset_manifest.v1.yaml")
    source_cases = {c.case_id: c for c in default_openai_round0_comparison_cases()}

    candidates: list[SilverLabelCandidate] = []
    for split_id, case_ids in manifest["splits"].items():
        for case_id in case_ids:
            mc = manifest["cases"][case_id]
            sc = source_cases.get(case_id)
            domain = str(mc.get("domain", sc.domain if sc else "general"))
            content = str(mc.get("content", sc.content if sc else ""))
            if not content:
                raise ValueError(
                    "trust_value_dataset_manifest.v1.yaml case is missing content and no fallback exists: "
                    f"{case_id}"
                )
            candidates.append(
                SilverLabelCandidate(
                    case_id=case_id,
                    domain=domain,
                    content=content,
                    expected_escalation=bool(mc.get("expected_escalation", False)),
                    split_id=split_id,
                    slice_ids=list(mc.get("slice_ids", [])),
                    source_type="benchmark",
                    provenance_reference=f"trust_manifest:{case_id}",
                )
            )
    return candidates


def _build_label_hash(case_id: str, judge_votes: list[dict[str, object]], content: str) -> str:
    payload = {
        "case_id": case_id,
        "content": content,
        "judge_votes": judge_votes,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_openai_round0_silver_labeling(
    *,
    output_dir: str,
    route_set_id: str = "default_round0_openai",
    judge_profile_id: str = "balanced_reviewer_v1",
    candidates: list[SilverLabelCandidate] | None = None,
    min_agreement: float = 1.0,
    min_avg_confidence: float = 0.80,
) -> dict[str, object]:
    selected = candidates or default_trust_silver_candidates()
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[SilverLabelCandidate]] = {"development": [], "holdout": []}
    for c in selected:
        grouped.setdefault(c.split_id, []).append(c)

    labels: list[dict[str, object]] = []
    rejections: list[dict[str, object]] = []

    for split_id, split_candidates in grouped.items():
        if not split_candidates:
            continue

        comparison_cases = [
            OpenAIRound0ComparisonCase(
                case_id=c.case_id,
                domain=c.domain,
                content=c.content,
                expected_escalation=bool(c.expected_escalation),
            )
            for c in split_candidates
        ]
        comparison = run_openai_round0_comparison(
            output_dir=str(output_root / f"_tmp_{split_id}"),
            route_set_id=route_set_id,
            single_profile_id=judge_profile_id,
            cases=comparison_cases,
        )

        by_case = {r["case"]["case_id"]: r for r in comparison["case_results"]}

        for c in split_candidates:
            row = by_case[c.case_id]
            committee_records = list(row["committee"].get("per_juror", []))
            if not committee_records:
                rejections.append(
                    {
                        "case_id": c.case_id,
                        "split_id": c.split_id,
                        "reason": "missing_committee_records",
                    }
                )
                continue

            votes: list[bool] = [bool(r["contradicted"]) for r in committee_records]
            true_count = sum(1 for v in votes if v)
            false_count = len(votes) - true_count
            majority = true_count >= false_count
            agreement = max(true_count, false_count) / max(len(votes), 1)
            avg_conf = sum(float(r.get("confidence", 0.0)) for r in committee_records) / len(committee_records)
            all_parsed = all(bool(r.get("parsed_ok", False)) for r in committee_records)

            accepted = agreement >= min_agreement and avg_conf >= min_avg_confidence and all_parsed
            judge_votes = [
                {
                    "juror_id": r.get("juror_id"),
                    "vote_contradicted": bool(r.get("contradicted")),
                    "confidence": float(r.get("confidence", 0.0)),
                    "parsed_ok": bool(r.get("parsed_ok", False)),
                    "error_code": r.get("error_code"),
                }
                for r in committee_records
            ]

            if accepted:
                labels.append(
                    {
                        **asdict(c),
                        "expected_escalation": bool(majority),
                        "label_tier": "tier_b_silver",
                        "provisional": True,
                        "agreement": round(agreement, 4),
                        "avg_confidence": round(avg_conf, 4),
                        "label_provenance_hash": _build_label_hash(c.case_id, judge_votes, c.content),
                        "judges": judge_votes,
                    }
                )
            else:
                rejections.append(
                    {
                        "case_id": c.case_id,
                        "split_id": c.split_id,
                        "reason": "insufficient_judge_agreement_or_confidence",
                        "agreement": round(agreement, 4),
                        "avg_confidence": round(avg_conf, 4),
                        "all_parsed": all_parsed,
                    }
                )

    summary = {
        "candidate_count": len(selected),
        "accepted_count": len(labels),
        "rejected_count": len(rejections),
        "label_tier": "tier_b_silver",
        "claim_scope": "silver-label evidence supports provisional trust assessment, not final committee-default proof",
    }

    (output_root / "silver_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "silver_labels.json").write_text(json.dumps(labels, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "silver_rejections.json").write_text(json.dumps(rejections, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "silver_summary.md").write_text(
        "\n".join(
            [
                "# Silver Label Summary",
                "",
                f"- candidate_count: {summary['candidate_count']}",
                f"- accepted_count: {summary['accepted_count']}",
                f"- rejected_count: {summary['rejected_count']}",
                f"- label_tier: {summary['label_tier']}",
                "- silver-label evidence supports provisional trust assessment, not final committee-default proof",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "summary": summary,
        "labels": labels,
        "rejections": rejections,
    }
