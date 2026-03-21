from __future__ import annotations

import pytest

from symposia import validate
from symposia.models.routing import JurorRoutingConfig
from symposia.providers import ProviderConfig, ProviderRegistry


def test_default_mode_requires_openai_key_and_succeeds(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    result = validate(
        content="Aspirin can reduce fever and pain in many cases.",
        domain="medical",
    )
    assert result.run_id.startswith("run_")


def test_model_override_provider_model_parsing_and_key_check(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

    result = validate(
        content="Diversification can reduce portfolio volatility.",
        domain="finance",
        model="anthropic:claude-3-5-haiku-latest",
    )
    assert result.run_id.startswith("run_")


def test_named_routing_requires_keys_for_all_route_providers(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")

    result = validate(
        content="Chest pain with shortness of breath warrants urgent evaluation.",
        domain="medical",
        routing="default_round0",
    )
    assert result.run_id.startswith("run_")


def test_custom_routing_object_supported(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

    custom_route = JurorRoutingConfig(
        version="v1",
        route_set_id="custom_obj",
        stage="escalation",
        domain="medical",
        output_schema="juror_decision_v1",
        guardrails={
            "max_premium_jurors_per_run": 1,
            "max_estimated_run_cost_usd": 0.05,
            "require_provider_diversity": True,
            "require_model_family_diversity": True,
            "premium_allowed_in_round0": False,
        },
        assignments=[
            {
                "slot_id": "one",
                "profile_id": "risk_sentinel_v1",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "model_family": "gpt-4o",
                "tier": "small_capable",
                "timeout_seconds": 10,
                "max_output_tokens": 300,
                "estimated_cost_usd": 0.01,
                "fallback": {
                    "provider": "anthropic",
                    "model": "claude-3-5-haiku-latest",
                    "model_family": "claude-3-5",
                },
            },
            {
                "slot_id": "two",
                "profile_id": "evidence_maximalist_v1",
                "provider": "anthropic",
                "model": "claude-3-5-haiku-latest",
                "model_family": "claude-3-5",
                "tier": "small_capable",
                "timeout_seconds": 10,
                "max_output_tokens": 300,
                "estimated_cost_usd": 0.01,
                "fallback": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "model_family": "gpt-4o",
                },
            },
        ],
    )

    result = validate(
        content="Contract clauses should be reviewed for indemnity scope.",
        domain="legal",
        routing=custom_route,
    )
    assert result.run_id.startswith("run_")


def test_conflict_routing_with_model_raises(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    with pytest.raises(ValueError, match="routing cannot be combined"):
        validate(
            content="Any claim.",
            domain="general",
            routing="default_round0",
            model="openai:gpt-4o-mini",
        )


def test_provider_registry_object_supported_without_env() -> None:
    result = validate(
        content="General factual statement.",
        domain="general",
        provider_config=ProviderRegistry(
            providers=[ProviderConfig(provider="openai", api_key="registry-openai")]
        ),
    )
    assert result.run_id.startswith("run_")


def test_invalid_model_format_rejected() -> None:
    with pytest.raises(ValueError, match="provider:model"):
        validate(
            content="Any claim.",
            domain="general",
            model="gpt-4o-mini",
            provider_config=ProviderConfig(provider="openai", api_key="x"),
        )
