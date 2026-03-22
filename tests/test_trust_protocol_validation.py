from __future__ import annotations

import pytest

pytestmark = pytest.mark.ladder

from symposia.smoke.openai_initial_comparison import (
    OpenAIRound0ComparisonCase,
    default_openai_initial_comparison_cases,
)
from symposia.smoke.protocol_validation import (
    ProtocolValidationError,
    build_resolved_trust_protocol_artifact,
    validate_trust_protocol_contract,
)


def test_trust_protocol_validation_passes_for_default_cases_and_route() -> None:
    result = validate_trust_protocol_contract(
        route_set_id="default_initial_openai",
        cases=default_openai_initial_comparison_cases(),
    )

    assert result.protocol_version == "trust_value_protocol_v2_2026_03_21"
    assert result.dataset_version == "trust_value_dataset_v1_2026_03_21"
    assert "agreement_rate" in result.metrics


def test_trust_protocol_validation_rejects_unknown_case_id() -> None:
    bad_cases = [
        OpenAIRound0ComparisonCase(
            case_id="unknown_case",
            domain="general",
            content="Unknown case content",
            expected_escalation=True,
        )
    ]

    with pytest.raises(ProtocolValidationError, match="not present in dataset manifest"):
        validate_trust_protocol_contract(
            route_set_id="default_initial_openai",
            cases=bad_cases,
        )


def test_resolved_trust_protocol_artifact_contains_required_fields(tmp_path) -> None:
    validation = validate_trust_protocol_contract(
        route_set_id="default_initial_openai",
        cases=default_openai_initial_comparison_cases(),
    )

    artifact = build_resolved_trust_protocol_artifact(
        route_set_id="default_initial_openai",
        validation=validation,
        output_dir=str(tmp_path),
    )

    assert artifact["protocol_version"] == "trust_value_protocol_v2_2026_03_21"
    assert artifact["dataset_manifest_version"] == "trust_value_dataset_v1_2026_03_21"
    assert artifact["route_set_id"] == "default_initial_openai"
    assert isinstance(artifact["metrics"], dict)
    assert isinstance(artifact["sample_size_gates"], dict)
    assert isinstance(artifact["decision_outputs"], dict)
    assert isinstance(artifact["timestamp_utc"], str)
    assert "git_commit" in artifact
