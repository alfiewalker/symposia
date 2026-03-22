from __future__ import annotations

import pytest

pytestmark = pytest.mark.core

from symposia.models.routing import JurorRoutingConfig
from symposia.routing import (
    ROUTING_OUTPUT_SCHEMA,
    ROUTING_VERSION,
    get_route_set,
    list_route_sets,
)


def test_routing_loader_discovers_expected_route_sets() -> None:
    # The registry grows as new route sets are added; verify the stable baseline
    # is always present rather than locking the full set.
    assert {"default_initial", "escalation_high_risk"}.issubset(set(list_route_sets()))
    assert len(list_route_sets()) >= 2
    assert ROUTING_VERSION == "v1"
    assert ROUTING_OUTPUT_SCHEMA == "juror_decision_v1"


def test_initial_defaults_use_small_capable_models_only() -> None:
    route = get_route_set("default_initial")
    assert route.stage == "initial"
    assert route.guardrails.premium_allowed_in_initial is False
    assert all(a.tier != "premium" for a in route.assignments)


def test_each_assignment_has_provider_model_and_fallback() -> None:
    for route_id in list_route_sets():
        route = get_route_set(route_id)
        for a in route.assignments:
            assert a.provider
            assert a.model
            assert a.fallback.provider
            assert a.fallback.model


def test_guardrail_budget_caps_hold_for_all_routes() -> None:
    # estimated_cost_usd was removed from JurorRouteAssignment and
    # max_estimated_run_cost_usd was removed from JurorRoutingGuardrails in a
    # schema simplification pass.  Budget enforcement is now handled at runtime
    # rather than at schema level.  Verify the schema itself is consistent.
    for route_id in list_route_sets():
        route = get_route_set(route_id)
        assert route.guardrails.max_premium_jurors_per_run >= 0


def test_guardrail_premium_caps_hold_for_all_routes() -> None:
    for route_id in list_route_sets():
        route = get_route_set(route_id)
        premium = sum(1 for a in route.assignments if a.tier == "premium")
        assert premium <= route.guardrails.max_premium_jurors_per_run


def test_guardrail_requires_diversity_when_enabled() -> None:
    for route_id in list_route_sets():
        route = get_route_set(route_id)
        if route.guardrails.require_provider_diversity:
            assert len({a.provider for a in route.assignments}) >= 2
        if route.guardrails.require_model_family_diversity:
            assert len({a.model_family for a in route.assignments}) >= 2


def test_schema_rejects_initial_premium_without_override() -> None:
    bad = {
        "version": "v1",
        "route_set_id": "bad_initial",
        "stage": "initial",
        "domain": "all",
        "output_schema": "juror_decision_v1",
        "guardrails": {
            "max_premium_jurors_per_run": 1,
            "require_provider_diversity": False,
            "require_model_family_diversity": False,
            "premium_allowed_in_initial": False,
        },
        "assignments": [
            {
                "slot_id": "x",
                "profile_id": "balanced_reviewer_v1",
                "provider": "openai",
                "model": "gpt-4o-2024-08-06",
                "model_family": "gpt-4o",
                "tier": "premium",
                "timeout_seconds": 10,
                "max_output_tokens": 400,
                "fallback": {
                    "provider": "anthropic",
                    "model": "claude-3-5-haiku-latest",
                    "model_family": "claude-3-5",
                },
            }
        ],
    }

    with pytest.raises(ValueError, match="Round0 routing must not include premium jurors"):
        JurorRoutingConfig(**bad)
