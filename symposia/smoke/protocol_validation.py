from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from typing import Protocol

import yaml


class _ComparisonCaseLike(Protocol):
    case_id: str
    expected_escalation: bool


HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class ProtocolValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProtocolValidationResult:
    protocol_version: str
    dataset_version: str
    allowed_route_sets: list[str]
    calibration_metric_id: str
    calibration_bin_edges: list[float]
    calibration: dict
    thresholds: dict
    statistics: dict
    governance: dict
    threshold_latency_ratio_max: float
    threshold_cost_ratio_max: float


@dataclass(frozen=True)
class TrustProtocolValidationResult:
    protocol_version: str
    dataset_version: str
    allowed_route_sets: list[str]
    metrics: dict
    thresholds: dict
    sample_size_gates: dict
    decision_outputs: dict
    statistics: dict
    runtime_change_policy: dict


def _load_yaml_resource(file_name: str) -> dict:
    path = files("symposia.smoke.protocol").joinpath(file_name)
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ProtocolValidationError(f"Invalid YAML mapping in protocol resource: {file_name}")
    return data


def validate_comparison_protocol_contract(
    *,
    route_set_id: str,
    cases: list[_ComparisonCaseLike],
) -> ProtocolValidationResult:
    protocol = _load_yaml_resource("committee_value_protocol.v1.yaml")
    manifest = _load_yaml_resource("committee_value_dataset_manifest.v1.yaml")

    required_top_keys = {"version", "allowed_route_sets", "calibration", "thresholds", "dataset_manifest"}
    missing_protocol = sorted(k for k in required_top_keys if k not in protocol)
    if missing_protocol:
        raise ProtocolValidationError(
            "Protocol file missing required keys: " + ", ".join(missing_protocol)
        )

    if route_set_id not in protocol["allowed_route_sets"]:
        raise ProtocolValidationError(
            f"Protocol violation: route_set_id '{route_set_id}' is not in allowed_route_sets"
        )

    required_manifest_keys = {"dataset_version", "cases", "splits"}
    missing_manifest = sorted(k for k in required_manifest_keys if k not in manifest)
    if missing_manifest:
        raise ProtocolValidationError(
            "Dataset manifest missing required keys: " + ", ".join(missing_manifest)
        )

    dataset_version = str(manifest["dataset_version"])
    allowed_dataset_versions = protocol["dataset_manifest"].get("allowed_dataset_versions", [])
    if dataset_version not in allowed_dataset_versions:
        raise ProtocolValidationError(
            "Protocol violation: dataset_version is not in allowed_dataset_versions"
        )

    seen_case_ids: set[str] = set()
    manifest_cases: dict[str, dict] = manifest["cases"]
    for case in cases:
        if case.case_id in seen_case_ids:
            raise ProtocolValidationError(
                f"Protocol violation: duplicate case_id in run input: '{case.case_id}'"
            )
        seen_case_ids.add(case.case_id)

        if case.case_id not in manifest_cases:
            raise ProtocolValidationError(
                f"Protocol violation: case_id '{case.case_id}' is not present in dataset manifest"
            )

        manifest_case = manifest_cases[case.case_id]
        expected_escalation = bool(manifest_case.get("expected_escalation"))
        if case.expected_escalation != expected_escalation:
            raise ProtocolValidationError(
                "Protocol violation: expected_escalation mismatch for case_id='"
                f"{case.case_id}'"
            )

        slice_ids = manifest_case.get("slice_ids", [])
        if not isinstance(slice_ids, list) or not slice_ids or not all(isinstance(s, str) and s for s in slice_ids):
            raise ProtocolValidationError(
                f"Protocol violation: case_id '{case.case_id}' must define non-empty slice_ids"
            )

        label_hash = str(manifest_case.get("label_provenance_hash", ""))
        if not HEX64_RE.match(label_hash):
            raise ProtocolValidationError(
                "Protocol violation: case_id '"
                f"{case.case_id}' has invalid label_provenance_hash"
            )

    calibration = protocol["calibration"]
    metric_id = str(calibration.get("metric_id", ""))
    if metric_id != "ece10":
        raise ProtocolValidationError(
            f"Protocol violation: unsupported calibration metric_id '{metric_id}'"
        )

    bin_edges = calibration.get("bin_edges")
    if (
        not isinstance(bin_edges, list)
        or len(bin_edges) != 11
        or abs(float(bin_edges[0]) - 0.0) > 1e-9
        or abs(float(bin_edges[-1]) - 1.0) > 1e-9
    ):
        raise ProtocolValidationError(
            "Protocol violation: calibration bin_edges must be 11 points from 0.0 to 1.0"
        )

    thresholds = protocol["thresholds"]
    latency_ratio_max = float(thresholds.get("latency_ratio_max", 0.0))
    cost_ratio_max = float(thresholds.get("cost_ratio_max", 0.0))
    if latency_ratio_max <= 0.0 or cost_ratio_max <= 0.0:
        raise ProtocolValidationError(
            "Protocol violation: latency_ratio_max and cost_ratio_max must be > 0"
        )

    return ProtocolValidationResult(
        protocol_version=str(protocol["version"]),
        dataset_version=dataset_version,
        allowed_route_sets=list(protocol.get("allowed_route_sets", [])),
        calibration_metric_id=metric_id,
        calibration_bin_edges=[float(v) for v in bin_edges],
        calibration=dict(calibration),
        thresholds=dict(thresholds),
        statistics=dict(protocol.get("statistics", {})),
        governance=dict(protocol.get("governance", {})),
        threshold_latency_ratio_max=latency_ratio_max,
        threshold_cost_ratio_max=cost_ratio_max,
    )


def validate_trust_protocol_contract(
    *,
    route_set_id: str,
    cases: list[_ComparisonCaseLike],
) -> TrustProtocolValidationResult:
    protocol = _load_yaml_resource("trust_value_protocol.v2.yaml")
    manifest = _load_yaml_resource("trust_value_dataset_manifest.v1.yaml")

    required_protocol_keys = {
        "version",
        "allowed_route_sets",
        "metrics",
        "sample_size_gates",
        "decision_outputs",
        "dataset_manifest",
    }
    missing_protocol = sorted(k for k in required_protocol_keys if k not in protocol)
    if missing_protocol:
        raise ProtocolValidationError(
            "Trust protocol file missing required keys: " + ", ".join(missing_protocol)
        )

    if route_set_id not in protocol["allowed_route_sets"]:
        raise ProtocolValidationError(
            f"Trust protocol violation: route_set_id '{route_set_id}' is not in allowed_route_sets"
        )

    required_manifest_keys = {"dataset_version", "cases", "splits", "slice_classes"}
    missing_manifest = sorted(k for k in required_manifest_keys if k not in manifest)
    if missing_manifest:
        raise ProtocolValidationError(
            "Trust dataset manifest missing required keys: " + ", ".join(missing_manifest)
        )

    dataset_version = str(manifest["dataset_version"])
    allowed_dataset_versions = protocol["dataset_manifest"].get("allowed_dataset_versions", [])
    if dataset_version not in allowed_dataset_versions:
        raise ProtocolValidationError(
            "Trust protocol violation: dataset_version is not in allowed_dataset_versions"
        )

    defined_slice_classes = manifest.get("slice_classes", [])
    if not isinstance(defined_slice_classes, list) or not defined_slice_classes:
        raise ProtocolValidationError("Trust dataset manifest must define non-empty slice_classes")

    seen_case_ids: set[str] = set()
    manifest_cases: dict[str, dict] = manifest["cases"]
    for case in cases:
        if case.case_id in seen_case_ids:
            raise ProtocolValidationError(
                f"Trust protocol violation: duplicate case_id in run input: '{case.case_id}'"
            )
        seen_case_ids.add(case.case_id)

        if case.case_id not in manifest_cases:
            raise ProtocolValidationError(
                f"Trust protocol violation: case_id '{case.case_id}' is not present in dataset manifest"
            )

        manifest_case = manifest_cases[case.case_id]
        expected_escalation = bool(manifest_case.get("expected_escalation"))
        if case.expected_escalation != expected_escalation:
            raise ProtocolValidationError(
                "Trust protocol violation: expected_escalation mismatch for case_id='"
                f"{case.case_id}'"
            )

        slice_ids = manifest_case.get("slice_ids", [])
        if not isinstance(slice_ids, list) or not slice_ids or not all(isinstance(s, str) and s for s in slice_ids):
            raise ProtocolValidationError(
                f"Trust protocol violation: case_id '{case.case_id}' must define non-empty slice_ids"
            )
        unknown_slices = sorted({s for s in slice_ids if s not in defined_slice_classes})
        if unknown_slices:
            raise ProtocolValidationError(
                f"Trust protocol violation: case_id '{case.case_id}' includes unknown slices: {unknown_slices}"
            )

        label_hash = str(manifest_case.get("label_provenance_hash", ""))
        if not HEX64_RE.match(label_hash):
            raise ProtocolValidationError(
                "Trust protocol violation: case_id '"
                f"{case.case_id}' has invalid label_provenance_hash"
            )

    return TrustProtocolValidationResult(
        protocol_version=str(protocol["version"]),
        dataset_version=dataset_version,
        allowed_route_sets=list(protocol.get("allowed_route_sets", [])),
        metrics=dict(protocol.get("metrics", {})),
        thresholds=dict(protocol.get("thresholds", {})),
        sample_size_gates=dict(protocol.get("sample_size_gates", {})),
        decision_outputs=dict(protocol.get("decision_outputs", {})),
        statistics=dict(protocol.get("statistics", {})),
        runtime_change_policy=dict(protocol.get("runtime_change_policy", {})),
    )


def build_resolved_protocol_artifact(
    *,
    route_set_id: str,
    validation: ProtocolValidationResult,
    output_dir: str,
) -> dict[str, object]:
    return {
        "protocol_version": validation.protocol_version,
        "dataset_manifest_version": validation.dataset_version,
        "route_set_id": route_set_id,
        "calibration": validation.calibration,
        "thresholds": validation.thresholds,
        "statistics": validation.statistics,
        "governance": validation.governance,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _resolve_git_commit(output_dir),
    }


def build_resolved_trust_protocol_artifact(
    *,
    route_set_id: str,
    validation: TrustProtocolValidationResult,
    output_dir: str,
) -> dict[str, object]:
    return {
        "protocol_version": validation.protocol_version,
        "dataset_manifest_version": validation.dataset_version,
        "route_set_id": route_set_id,
        "metrics": validation.metrics,
        "thresholds": validation.thresholds,
        "sample_size_gates": validation.sample_size_gates,
        "decision_outputs": validation.decision_outputs,
        "statistics": validation.statistics,
        "runtime_change_policy": validation.runtime_change_policy,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _resolve_git_commit(output_dir),
    }


def _resolve_git_commit(output_dir: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(Path(output_dir).resolve()),
            capture_output=True,
            text=True,
            check=True,
        )
        value = proc.stdout.strip()
        return value or None
    except Exception:
        return None
