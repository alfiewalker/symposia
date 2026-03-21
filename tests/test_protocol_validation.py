from __future__ import annotations

import pytest

pytestmark = pytest.mark.ladder

from symposia.smoke.openai_round0_comparison import (
    OpenAIRound0ComparisonCase,
    default_openai_round0_comparison_cases,
)
from symposia.smoke.protocol_validation import (
    ProtocolValidationError,
    build_resolved_protocol_artifact,
    validate_comparison_protocol_contract,
)


def test_protocol_validation_passes_for_default_cases_and_route() -> None:
    result = validate_comparison_protocol_contract(
        route_set_id="default_round0_openai",
        cases=default_openai_round0_comparison_cases(),
    )

    assert result.protocol_version == "committee_value_protocol_v1_2026_03_21"
    assert result.dataset_version == "committee_value_dataset_v1_2026_03_21"
    assert result.calibration_metric_id == "ece10"
    assert len(result.calibration_bin_edges) == 11


def test_protocol_validation_rejects_unknown_case_id() -> None:
    bad_cases = [
        OpenAIRound0ComparisonCase(
            case_id="unknown_case",
            domain="general",
            content="Unknown case content",
            expected_escalation=True,
        )
    ]

    with pytest.raises(ProtocolValidationError, match="not present in dataset manifest"):
        validate_comparison_protocol_contract(
            route_set_id="default_round0_openai",
            cases=bad_cases,
        )


def test_protocol_validation_rejects_expected_escalation_mismatch() -> None:
    bad_cases = [
        OpenAIRound0ComparisonCase(
            case_id="hard_general_api_500_overclaim",
            domain="general",
            content="A single HTTP 500 error always means the database is permanently corrupted.",
            expected_escalation=False,
        )
    ]

    with pytest.raises(ProtocolValidationError, match="expected_escalation mismatch"):
        validate_comparison_protocol_contract(
            route_set_id="default_round0_openai",
            cases=bad_cases,
        )


def test_protocol_validation_rejects_disallowed_route() -> None:
    with pytest.raises(ProtocolValidationError, match="not in allowed_route_sets"):
        validate_comparison_protocol_contract(
            route_set_id="default_round0",
            cases=default_openai_round0_comparison_cases(),
        )


def test_resolved_protocol_artifact_contains_required_audit_fields(tmp_path) -> None:
    validation = validate_comparison_protocol_contract(
        route_set_id="default_round0_openai",
        cases=default_openai_round0_comparison_cases(),
    )

    artifact = build_resolved_protocol_artifact(
        route_set_id="default_round0_openai",
        validation=validation,
        output_dir=str(tmp_path),
    )

    assert artifact["protocol_version"] == "committee_value_protocol_v1_2026_03_21"
    assert artifact["dataset_manifest_version"] == "committee_value_dataset_v1_2026_03_21"
    assert artifact["route_set_id"] == "default_round0_openai"
    assert isinstance(artifact["calibration"], dict)
    assert isinstance(artifact["thresholds"], dict)
    assert isinstance(artifact["statistics"], dict)
    assert isinstance(artifact["governance"], dict)
    assert isinstance(artifact["timestamp_utc"], str)
    assert "git_commit" in artifact
