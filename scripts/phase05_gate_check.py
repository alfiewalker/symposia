#!/usr/bin/env python3
"""Phase 0.5 gate check.

Fail-fast checks for locked fixture integrity, schema conformance, and artifact completeness.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ROOT / "benchmarks" / "locks"
TRACE_DIR = LOCKS / "trace_snapshots"

GOLDEN = LOCKS / "golden_cases.jsonl"
SAFETY = LOCKS / "safety_slices.jsonl"
BASELINE = LOCKS / "baseline_cases.jsonl"
LOCKS_README = LOCKS / "README.md"
TRACE_SCHEMA = TRACE_DIR / "schema_v1.json"
TRACE_SAMPLE = TRACE_DIR / "sample_phase3_minimal_trace.json"

REQUIRED_ARTIFACTS = [
    GOLDEN,
    SAFETY,
    BASELINE,
    LOCKS_README,
    TRACE_DIR,
    TRACE_SCHEMA,
    TRACE_SAMPLE,
]

COMMON_REQUIRED_FIELDS = ["case_id", "domain", "content", "tags", "lock_version"]
EXPECTED_LOCK_VERSION = "v1"


@dataclass
class JsonlSpec:
    path: Path
    required_fields: List[str]
    id_set: Set[str]


class GateError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise GateError(message)


def parse_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists() or not path.is_file():
        fail(f"Missing required JSONL artifact: {path}")

    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                fail(f"JSON parse failure in {path} at line {idx}: {exc}")
            if not isinstance(payload, dict):
                fail(f"Expected object JSON at {path}:{idx}")
            rows.append(payload)

    if not rows:
        fail(f"No JSON rows found in {path}")
    return rows


def validate_required_non_empty(obj: Dict[str, Any], fields: List[str], source: str) -> None:
    for field in fields:
        if field not in obj:
            fail(f"Missing required field '{field}' in {source}")
        value = obj[field]
        if value is None:
            fail(f"Null value for required field '{field}' in {source}")
        if isinstance(value, str) and not value.strip():
            fail(f"Empty string for required field '{field}' in {source}")
        if isinstance(value, list) and len(value) == 0:
            fail(f"Empty list for required field '{field}' in {source}")


def validate_versions(rows: List[Dict[str, Any]], path: Path) -> None:
    seen_versions = set()
    for idx, row in enumerate(rows, start=1):
        source = f"{path}:{idx}"
        validate_required_non_empty(row, ["lock_version"], source)
        seen_versions.add(row["lock_version"])
    if len(seen_versions) != 1:
        fail(f"Inconsistent lock versions in {path}: {sorted(seen_versions)}")
    version = next(iter(seen_versions))
    if version != EXPECTED_LOCK_VERSION:
        fail(
            f"Unexpected lock version in {path}: found '{version}', expected '{EXPECTED_LOCK_VERSION}'"
        )


def validate_ids(rows: List[Dict[str, Any]], path: Path, id_set: Set[str]) -> None:
    local_ids: Set[str] = set()
    for idx, row in enumerate(rows, start=1):
        source = f"{path}:{idx}"
        validate_required_non_empty(row, ["case_id"], source)
        case_id = row["case_id"]
        if case_id in local_ids:
            fail(f"Duplicate case_id in {path}: '{case_id}'")
        if case_id in id_set:
            fail(f"Duplicate case_id across lock files: '{case_id}'")
        local_ids.add(case_id)
        id_set.add(case_id)


def validate_common_fields(rows: List[Dict[str, Any]], path: Path, extra: List[str]) -> None:
    required = list(dict.fromkeys(COMMON_REQUIRED_FIELDS + extra))
    for idx, row in enumerate(rows, start=1):
        validate_required_non_empty(row, required, f"{path}:{idx}")


def check_artifact_completeness() -> None:
    for artifact in REQUIRED_ARTIFACTS:
        if artifact.is_dir():
            if not artifact.exists():
                fail(f"Missing required directory artifact: {artifact}")
            continue
        if not artifact.exists() or not artifact.is_file():
            fail(f"Missing required file artifact: {artifact}")


def validate_trace_schema_and_sample() -> None:
    try:
        import jsonschema  # type: ignore
    except ModuleNotFoundError:
        fail("Missing dependency 'jsonschema'. Install dev dependencies before running gate check.")

    try:
        schema = json.loads(TRACE_SCHEMA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON schema in {TRACE_SCHEMA}: {exc}")

    try:
        sample = json.loads(TRACE_SAMPLE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON sample in {TRACE_SAMPLE}: {exc}")

    try:
        jsonschema.validate(instance=sample, schema=schema)
    except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
        fail(f"Trace sample does not conform to schema: {exc.message}")


def run_gate_checks() -> None:
    check_artifact_completeness()

    global_ids: Set[str] = set()

    specs = [
        JsonlSpec(GOLDEN, ["expected"], global_ids),
        JsonlSpec(SAFETY, ["expected"], global_ids),
        JsonlSpec(BASELINE, ["baseline_target"], global_ids),
    ]

    for spec in specs:
        rows = parse_jsonl(spec.path)
        validate_common_fields(rows, spec.path, spec.required_fields)
        validate_versions(rows, spec.path)
        validate_ids(rows, spec.path, spec.id_set)

    validate_trace_schema_and_sample()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 0.5 gate checks.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print failures; suppress success output.",
    )
    args = parser.parse_args()

    try:
        run_gate_checks()
    except GateError as exc:
        print(f"PHASE 0.5 GATE: FAIL\n{exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print("PHASE 0.5 GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
