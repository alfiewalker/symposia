#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from symposia.env import load_env
from symposia.smoke.openai_round0_trust_evaluation import run_openai_round0_trust_evaluation_v2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the trust pipeline for one or more splits and write a consolidated summary artifact."
        )
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run identifier used for artifact directory naming.",
    )
    parser.add_argument(
        "--publication-scope",
        choices=["development", "holdout", "synthesis"],
        default="synthesis",
        help=(
            "Governance publication scope label for this run output. "
            "Use synthesis when both development and holdout are executed."
        ),
    )
    parser.add_argument(
        "--output-root",
        default="artifacts/trust_pipeline_runs",
        help="Root directory for trust pipeline run artifacts.",
    )
    parser.add_argument(
        "--committee-route-set-id",
        default="default_round0_openai_nano",
        help="Route set used for committee execution.",
    )
    parser.add_argument(
        "--single-route-set-id",
        default="default_round0_openai_nano",
        help="Route set used for single baseline execution.",
    )
    parser.add_argument(
        "--escalation-route-set-id",
        default="escalation_high_risk_openai_mini",
        help="Escalation route set for high-risk cases.",
    )
    parser.add_argument(
        "--evidence-tier",
        default="tier_b_silver",
        help="Evidence label tier passed to trust evaluation.",
    )
    parser.add_argument(
        "--decomposition-mode",
        choices=["holistic", "rule_based"],
        default="holistic",
        help=(
            "Decomposition mode. Defaults to holistic for canonical evidence runs. "
            "Use rule_based only for explicit decomposition experiments."
        ),
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=["development", "holdout"],
        default=["development", "holdout"],
        help="Which dataset splits to run (default: development + holdout).",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional env file path; when omitted, default env search order is used.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.publication_scope in {"development", "holdout"}:
        if args.splits != [args.publication_scope]:
            raise SystemExit(
                "publication-scope and splits mismatch: use a single matching split, "
                "or set --publication-scope synthesis"
            )

    loaded_env_files = load_env(path=args.env_file) if args.env_file else load_env()
    if loaded_env_files:
        print("ENV_LOADED", loaded_env_files, flush=True)
    else:
        print("ENV_LOADED []", flush=True)

    base = Path(args.output_root) / args.run_id
    base.mkdir(parents=True, exist_ok=True)

    run_cfg = {
        "committee_route_set_id": args.committee_route_set_id,
        "single_route_set_id": args.single_route_set_id,
        "escalation_route_set_id": args.escalation_route_set_id,
        "evidence_label_tier": args.evidence_tier,
        "decomposition_mode": args.decomposition_mode,
    }

    split_reports: dict[str, dict[str, object]] = {}
    for split in args.splits:
        print(f"RUN_START {split}", flush=True)
        report = run_openai_round0_trust_evaluation_v2(
            output_dir=str(base / split),
            split_id=split,
            committee_route_set_id=run_cfg["committee_route_set_id"],
            single_route_set_id=run_cfg["single_route_set_id"],
            escalation_route_set_id=run_cfg["escalation_route_set_id"],
            evidence_label_tier=run_cfg["evidence_label_tier"],
            decomposition_mode=run_cfg["decomposition_mode"],
        )
        split_reports[split] = {
            "summary": report.get("summary", {}),
            "rubric_default_proof": report.get("rubric_default_proof", {}),
        }
        print(
            f"RUN_DONE {split} {split_reports[split]['summary'].get('final_decision')}",
            flush=True,
        )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "publication_scope": args.publication_scope,
        "route_setup": {
            "committee_route_set_id": args.committee_route_set_id,
            "single_route_set_id": args.single_route_set_id,
            "escalation_route_set_id": args.escalation_route_set_id,
        },
        "execution_policy": {
            "evidence_label_tier": args.evidence_tier,
            "decomposition_mode": args.decomposition_mode,
            "splits": args.splits,
        },
        "env_files_loaded": loaded_env_files,
        **split_reports,
    }

    summary_path = base / "pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PIPELINE_SUMMARY_WRITTEN", summary_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())