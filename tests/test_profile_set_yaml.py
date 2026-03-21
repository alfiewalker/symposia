from __future__ import annotations

import pytest

pytestmark = pytest.mark.legacy
from pydantic import ValidationError

from symposia.profile_sets import DOMAIN_DEFAULT_PROFILE_SET, get_profile_set, list_profile_sets
from symposia.profile_sets.loader import ProfileSetYamlConfig


def test_yaml_registry_contains_expected_stable_ids() -> None:
    # Verify the four stable profile sets are always present.  Other tests may
    # register additional sets into the global registry; use a subset check to
    # avoid isolation-order failures.
    assert {
        "finance_strict_v1",
        "general_default_v1",
        "legal_strict_v1",
        "medical_strict_v1",
    }.issubset(set(list_profile_sets()))


def test_yaml_domain_defaults_match_previous_registry_contract() -> None:
    assert DOMAIN_DEFAULT_PROFILE_SET == {
        "general": "general_default_v1",
        "medical": "medical_strict_v1",
        "legal": "legal_strict_v1",
        "finance": "finance_strict_v1",
    }


def test_yaml_profile_set_parity_against_previous_code_defined_defaults() -> None:
    expected = {
        "general_default_v1": {
            "domain": "general",
            "juror_count": 5,
            "profiles": [
                "balanced_reviewer_v1",
                "sceptical_verifier_v1",
                "literal_parser_v1",
                "evidence_maximalist_v1",
                "risk_sentinel_v1",
            ],
            "support": 0.70,
            "confidence": 0.70,
            "max_rounds": 2,
            "issuance_policy": "standard",
            "calibration_snapshot": "general_2026_q1",
        },
        "medical_strict_v1": {
            "domain": "medical",
            "juror_count": 5,
            "profiles": [
                "risk_sentinel_v1",
                "evidence_maximalist_v1",
                "medical_specialist_v1",
                "sceptical_verifier_v1",
                "literal_parser_v1",
            ],
            "support": 0.80,
            "confidence": 0.82,
            "max_rounds": 2,
            "issuance_policy": "conservative",
            "calibration_snapshot": "medical_2026_q1",
        },
        "legal_strict_v1": {
            "domain": "legal",
            "juror_count": 5,
            "profiles": [
                "literal_parser_v1",
                "sceptical_verifier_v1",
                "evidence_maximalist_v1",
                "legal_specialist_v1",
                "risk_sentinel_v1",
            ],
            "support": 0.78,
            "confidence": 0.80,
            "max_rounds": 2,
            "issuance_policy": "cautious",
            "calibration_snapshot": "legal_2026_q1",
        },
        "finance_strict_v1": {
            "domain": "finance",
            "juror_count": 5,
            "profiles": [
                "risk_sentinel_v1",
                "sceptical_verifier_v1",
                "evidence_maximalist_v1",
                "finance_specialist_v1",
                "balanced_reviewer_v1",
            ],
            "support": 0.77,
            "confidence": 0.79,
            "max_rounds": 2,
            "issuance_policy": "cautious",
            "calibration_snapshot": "finance_2026_q1",
        },
    }

    for profile_set_id, cfg in expected.items():
        loaded = get_profile_set(profile_set_id)
        assert loaded.domain == cfg["domain"]
        assert loaded.juror_count == cfg["juror_count"]
        assert loaded.profiles == cfg["profiles"]
        assert loaded.thresholds.support == cfg["support"]
        assert loaded.thresholds.confidence == cfg["confidence"]
        assert loaded.max_rounds == cfg["max_rounds"]
        assert loaded.issuance_policy == cfg["issuance_policy"]
        assert loaded.calibration_snapshot == cfg["calibration_snapshot"]


def test_profile_set_yaml_schema_rejects_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        ProfileSetYamlConfig(
            version="v1",
            id="test_set_v1",
            domain="general",
            purpose="test",
            profiles=["balanced_reviewer_v1"],
            juror_count=1,
            thresholds={"support": 0.7, "confidence": 0.7},
            max_rounds=1,
            issuance_policy="standard",
            defaults={"domain_default": False, "registry_group": "stable"},
            rogue_key="not allowed",
        )
