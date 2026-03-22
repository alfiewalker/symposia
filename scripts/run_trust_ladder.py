#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from symposia.env import load_env
from symposia.smoke.openai_round0_trust_evaluation import run_openai_round0_trust_evaluation_v2


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the canonical trust governance ladder and persist analysis-ready artifacts."
    )
    parser.add_argument("--run-id", required=True, help="Top-level ladder run identifier.")
    parser.add_argument(
        "--protocol-path",
        default="symposia/smoke/protocol/trust_ladder_protocol.v1.yaml",
        help="Path to the ladder protocol YAML.",
    )
    parser.add_argument(
        "--output-root",
        default="artifacts/trust_ladder_runs",
        help="Root directory for ladder artifacts.",
    )
    parser.add_argument(
        "--publication-scope",
        choices=["development", "holdout", "synthesis"],
        default=None,
        help="Override publication scope; defaults to protocol default.",
    )
    parser.add_argument(
        "--decomposition-mode",
        choices=["holistic", "rule_based"],
        default=None,
        help="Override decomposition mode; defaults to protocol default.",
    )
    parser.add_argument(
        "--evidence-tier",
        default=None,
        help="Override evidence tier; defaults to protocol default.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=["development", "holdout"],
        default=None,
        help="Override split set; defaults to protocol default.",
    )
    parser.add_argument(
        "--rungs",
        nargs="+",
        default=None,
        help="Optional subset of rung ids to execute. Defaults to all canonical rungs.",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Run only the minimal essential rung set from the protocol.",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional env file path; when omitted, default env search order is used.",
    )
    return parser.parse_args()


def _validate_scope(publication_scope: str, splits: list[str]) -> None:
    if publication_scope in {"development", "holdout"} and splits != [publication_scope]:
        raise SystemExit(
            "publication-scope and splits mismatch: use a single matching split, or set --publication-scope synthesis"
        )


def main() -> int:
    args = _parse_args()
    protocol_path = Path(args.protocol_path)
    protocol = _load_yaml(protocol_path)

    publication_scope = args.publication_scope or str(protocol.get("default_publication_scope", "synthesis"))
    decomposition_mode = args.decomposition_mode or str(protocol.get("default_decomposition_mode", "holistic"))
    evidence_tier = args.evidence_tier or str(protocol.get("default_evidence_label_tier", "tier_b_silver"))
    splits = list(args.splits) if args.splits is not None else [str(v) for v in protocol.get("default_splits", ["development", "holdout"])]
    escalation_route_set_id = str(protocol.get("default_escalation_route_set_id", "escalation_high_risk_openai_mini"))

    _validate_scope(publication_scope, splits)

    rung_rows = [dict(r) for r in protocol.get("canonical_rungs", [])]
    if args.minimal:
        allowed = set(str(v) for v in protocol.get("minimal_rungs_now", []))
        rung_rows = [r for r in rung_rows if str(r.get("rung_id")) in allowed]
    elif args.rungs:
        allowed = set(args.rungs)
        rung_rows = [r for r in rung_rows if str(r.get("rung_id")) in allowed]

    loaded_env_files = load_env(path=args.env_file) if args.env_file else load_env()
    print("ENV_LOADED", loaded_env_files, flush=True)

    base = Path(args.output_root) / args.run_id
    base.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "protocol_version": protocol.get("version", "unknown"),
        "protocol_path": str(protocol_path),
        "dataset_version": protocol.get("dataset_version", "unknown"),
        "publication_scope": publication_scope,
        "decomposition_mode": decomposition_mode,
        "evidence_label_tier": evidence_tier,
        "splits": splits,
        "env_files_loaded": loaded_env_files,
        "rungs": [],
    }

    ladder_summary = {
        "generated_at_utc": manifest["generated_at_utc"],
        "run_id": args.run_id,
        "protocol_version": manifest["protocol_version"],
        "dataset_version": manifest["dataset_version"],
        "publication_scope": publication_scope,
        "decomposition_mode": decomposition_mode,
        "evidence_label_tier": evidence_tier,
        "rung_summaries": {},
    }

    for rung in rung_rows:
        rung_id = str(rung["rung_id"])
        rung_root = base / rung_id
        rung_root.mkdir(parents=True, exist_ok=True)
        print(f"RUNG_START {rung_id}", flush=True)

        per_split: dict[str, dict[str, object]] = {}
        for split in splits:
            print(f"RUN_START {rung_id} {split}", flush=True)
            report = run_openai_round0_trust_evaluation_v2(
                output_dir=str(rung_root / split),
                committee_route_set_id=str(rung["committee_route_set_id"]),
                single_route_set_id=str(rung["single_route_set_id"]),
                escalation_route_set_id=escalation_route_set_id,
                split_id=split,
                evidence_label_tier=evidence_tier,
                decomposition_mode=decomposition_mode,
            )
            per_split[split] = {
                "summary": report.get("summary", {}),
                "rubric_default_proof": report.get("rubric_default_proof", {}),
            }
            print(
                f"RUN_DONE {rung_id} {split} {per_split[split]['summary'].get('final_decision')}",
                flush=True,
            )

        rung_summary = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "run_id": args.run_id,
            "rung_id": rung_id,
            "step_index": int(rung["step_index"]),
            "label": str(rung["label"]),
            "interpretation": str(rung["interpretation"]),
            "route_setup": {
                "committee_route_set_id": str(rung["committee_route_set_id"]),
                "single_route_set_id": str(rung["single_route_set_id"]),
                "escalation_route_set_id": escalation_route_set_id,
            },
            "execution_policy": {
                "publication_scope": publication_scope,
                "decomposition_mode": decomposition_mode,
                "evidence_label_tier": evidence_tier,
                "splits": splits,
            },
            **per_split,
        }
        summary_path = rung_root / "pipeline_summary.json"
        summary_path.write_text(json.dumps(rung_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        manifest["rungs"].append(
            {
                "rung_id": rung_id,
                "step_index": int(rung["step_index"]),
                "label": str(rung["label"]),
                "interpretation": str(rung["interpretation"]),
                "route_setup": rung_summary["route_setup"],
                "summary_path": str(summary_path),
                "artifact_root": str(rung_root),
            }
        )
        ladder_summary["rung_summaries"][rung_id] = rung_summary
        print(f"RUNG_DONE {rung_id}", flush=True)

    manifest_path = base / "manifest.json"
    ladder_summary_path = base / "ladder_summary.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ladder_summary_path.write_text(json.dumps(ladder_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("MANIFEST_WRITTEN", manifest_path, flush=True)
    print("LADDER_SUMMARY_WRITTEN", ladder_summary_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
