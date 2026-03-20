from __future__ import annotations

import inspect

import symposia
from symposia import InitialReviewResult, load_profile_set, validate


def test_primary_surface_all_is_tiny_and_intentional() -> None:
    assert symposia.__all__ == [
        "validate",
        "load_profile_set",
        "Risk",
        "InitialReviewResult",
    ]


def test_validate_signature_is_day_one_simple() -> None:
    signature = inspect.signature(validate)
    assert list(signature.parameters.keys()) == [
        "content",
        "domain",
        "profile_set",
        "profile",
    ]


def test_load_profile_set_resolves_domain_default() -> None:
    resolved = load_profile_set(domain="medical")
    assert resolved.profile_set_id == "medical_strict_v1"
    assert resolved.domain == "medical"
    assert len(resolved.profiles) >= 1


def test_validate_returns_primary_result_type() -> None:
    result = validate(
        content="The speed of light in vacuum is approximately 299,792 kilometers per second.",
        domain="general",
    )
    assert isinstance(result, InitialReviewResult)
    assert result.run_id.startswith("run_")
    assert result.bundle.raw_content
    assert result.bundle.subclaims
