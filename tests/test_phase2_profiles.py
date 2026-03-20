import json
from pathlib import Path

import pytest

from symposia.models import Profile, ProfileBehavior
from symposia.config import resolve_profile_set
from symposia.profile_sets import get_default_profile_set, get_profile_set
from symposia.profiles import list_profiles, register_profile


def _domains_from_locked_fixtures() -> set[str]:
    domains: set[str] = set()
    files = [
        Path("benchmarks/locks/golden_cases.jsonl"),
        Path("benchmarks/locks/safety_slices.jsonl"),
        Path("benchmarks/locks/baseline_cases.jsonl"),
    ]
    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    domains.add(json.loads(line)["domain"])
    return domains


def test_fixed_profile_registry_contains_expected_profiles():
    expected = {
        "balanced_reviewer_v1",
        "sceptical_verifier_v1",
        "evidence_maximalist_v1",
        "literal_parser_v1",
        "risk_sentinel_v1",
    }
    assert expected.issubset(set(list_profiles()))


def test_default_profile_set_resolution_is_deterministic_for_locked_domains():
    for domain in sorted(_domains_from_locked_fixtures()):
        first = resolve_profile_set(domain=domain)
        second = resolve_profile_set(domain=domain)
        assert first.profile_set.profile_set_id == second.profile_set.profile_set_id
        assert first.profile_set.to_canonical_json() == second.profile_set.to_canonical_json()


def test_explicit_profile_set_selection_wins():
    resolved = resolve_profile_set(domain="medical", profile_set="medical_strict_v1")
    assert resolved.profile_set.profile_set_id == "medical_strict_v1"
    assert resolved.metadata.source == "explicit"


def test_profile_overlay_is_deterministic_and_bounded():
    resolved = resolve_profile_set(
        domain="medical",
        profile_set="medical_strict_v1",
        profile="balanced_reviewer_v1",
    )
    assert resolved.profile_set.profile_set_id == "medical_strict_v1"
    # Already present in defaults, no duplicate should be added.
    assert resolved.profile_set.profiles.count("balanced_reviewer_v1") == 1


def test_incompatible_profile_overlay_rejected():
    register_profile(
        Profile(
            profile_id="medical_only_v1",
            label="Medical Only",
            purpose="Test-only profile limited to medical.",
            behavior=ProfileBehavior(
                stance="strict",
                literalism="medium",
                evidence_demand="high",
                safety_bias="high",
            ),
            compatible_domains=["medical"],
            version="v1",
        )
    )

    # Sanity check fixed registry still has legal defaults available.
    assert get_default_profile_set("legal").domain == "legal"
    assert get_profile_set("legal_strict_v1").domain == "legal"

    with pytest.raises(ValueError):
        resolve_profile_set(domain="legal", profile="medical_only_v1")
