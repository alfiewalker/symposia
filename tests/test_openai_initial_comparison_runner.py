from __future__ import annotations

import pytest

pytestmark = pytest.mark.ladder

from types import SimpleNamespace

from symposia.jurors.llm import JurorExecutionRecord
from symposia.models.juror import JurorDecision
from symposia.models.routing import (
    JurorRouteAssignment,
    JurorRouteFallback,
    JurorRoutingConfig,
    JurorRoutingGuardrails,
)
from symposia.smoke.openai_initial_comparison import (
    _build_decision_markdown,
    _build_markdown_summary,
    _write_protocol_output_artifacts,
    _decision_agreement,
    OpenAIRound0ComparisonCase,
    default_openai_initial_comparison_cases,
    run_openai_initial_comparison,
)


def test_default_openai_initial_comparison_cases_are_narrow_and_bounded() -> None:
    cases = default_openai_initial_comparison_cases()

    assert 5 <= len(cases) <= 10
    assert all(case.domain == "general" for case in cases)


def test_decision_agreement_matches_majority_signature_ratio() -> None:
    decisions = [
        JurorDecision(
            juror_id="j1",
            profile_id="p1",
            subclaim_id="s1",
            supported=True,
            contradicted=False,
            sufficient=True,
            issuable=False,
            confidence=0.8,
        ),
        JurorDecision(
            juror_id="j2",
            profile_id="p2",
            subclaim_id="s1",
            supported=True,
            contradicted=False,
            sufficient=True,
            issuable=False,
            confidence=0.8,
        ),
        JurorDecision(
            juror_id="j3",
            profile_id="p3",
            subclaim_id="s1",
            supported=False,
            contradicted=True,
            sufficient=False,
            issuable=False,
            confidence=0.2,
        ),
    ]

    assert _decision_agreement(decisions) == 2 / 3


def test_build_markdown_summary_includes_requested_headline_metrics() -> None:
    report = {
        "summary": {
            "protocol_version": "committee_value_protocol_v1_2026_03_21",
            "dataset_version": "committee_value_dataset_v1_2026_03_21",
            "calibration_metric_id": "ece10",
            "calibration_bin_edges": [0.0, 0.1, 0.2],
            "model": "gpt-5.4-mini",
            "route_set_id": "default_initial_openai",
            "review_mode": "holistic_single_claim",
            "decomposition_mode": "no_decomposition",
            "case_count": 2,
            "price_version": "openai_total_token_price_v1_2026_03_21",
            "missing_price_models": [],
            "single_false_escalations": 1,
            "single_missed_escalations": 0,
            "committee_false_escalations": 0,
            "committee_missed_escalations": 0,
            "single_total_escalation_errors": 1,
            "committee_total_escalation_errors": 0,
            "escalation_error_reduction_pct": 100.0,
            "avg_latency_ratio_committee_over_single": 2.5,
            "avg_cost_ratio_committee_over_single": 3.0,
            "worth_it_rule": {
                "min_error_reduction_pct": 20.0,
                "max_latency_ratio": 4.0,
                "max_cost_ratio": 4.5,
            },
            "efficiency_worth_it_decision": True,
            "worth_it_decision": True,
        },
        "case_results": [
            {
                "case": {"case_id": "c1", "expected_escalation": False},
                "single": {"escalation": True, "agreement": 1.0},
                "committee": {"escalation": False, "agreement": 0.75},
            },
            {
                "case": {"case_id": "c2", "expected_escalation": True},
                "single": {"escalation": True, "agreement": 1.0},
                "committee": {"escalation": True, "agreement": 1.0},
            },
        ],
    }

    markdown = _build_markdown_summary(report)
    assert "OpenAI Round0 Jury Theory Comparison" in markdown
    assert "protocol_version: committee_value_protocol_v1_2026_03_21" in markdown
    assert "dataset_version: committee_value_dataset_v1_2026_03_21" in markdown
    assert "review_mode: holistic_single_claim" in markdown
    assert "decomposition_mode: no_decomposition" in markdown
    assert "price_version: openai_total_token_price_v1_2026_03_21" in markdown
    assert "missing_price_models: none" in markdown
    assert "single_false_escalations: 1" in markdown
    assert "committee_false_escalations: 0" in markdown
    assert "efficiency_worth_it_decision: True" in markdown
    assert "worth_it_decision: True (legacy_ambiguous_alias_of_efficiency_worth_it_decision)" in markdown
    assert "| c1 | 0 | 1 | 0 | 0 | 1.00 | 0.75 |" in markdown


def test_juror_execution_record_accepts_token_and_cost_fields() -> None:
    record = JurorExecutionRecord(
        juror_id="j1",
        provider_model="gpt-5.4-mini",
        raw_response="{}",
        parsed_ok=True,
        tokens_used=123,
        cost_usd=0.0123,
    )

    assert record.tokens_used == 123
    assert record.cost_usd == 0.0123


def test_estimator_returns_unknown_for_missing_model_price() -> None:
    from symposia.pricing import estimate_openai_total_token_cost

    estimate = estimate_openai_total_token_cost("unknown-model", 1000)
    assert estimate.estimated_cost_usd is None
    assert estimate.missing_price is True
    assert estimate.price_version.startswith("openai_total_token_price_v1")


def test_estimator_returns_non_zero_for_known_model() -> None:
    from symposia.pricing import estimate_openai_total_token_cost

    estimate = estimate_openai_total_token_cost("gpt-5.4-mini", 2000)
    assert estimate.missing_price is False
    assert estimate.estimated_cost_usd is not None
    assert estimate.estimated_cost_usd > 0.0


def test_estimator_returns_non_zero_for_nano_model() -> None:
    from symposia.pricing import estimate_openai_total_token_cost

    estimate = estimate_openai_total_token_cost("gpt-5.4-nano", 2000)
    assert estimate.missing_price is False
    assert estimate.estimated_cost_usd is not None
    assert estimate.estimated_cost_usd > 0.0


def test_write_protocol_output_artifacts_creates_required_files_and_trust_aware_decision(
    tmp_path,
) -> None:
    report = {
        "summary": {
            "protocol_version": "committee_value_protocol_v1_2026_03_21",
            "dataset_version": "committee_value_dataset_v1_2026_03_21",
            "calibration_metric_id": "ece10",
            "calibration_bin_edges": [0.0, 0.1, 0.2],
            "model": "gpt-5.4-mini",
            "route_set_id": "default_initial_openai",
            "review_mode": "holistic_single_claim",
            "decomposition_mode": "no_decomposition",
            "case_count": 1,
            "price_version": "openai_total_token_price_v1_2026_03_21",
            "missing_price_models": [],
            "single_false_escalations": 0,
            "single_missed_escalations": 0,
            "committee_false_escalations": 0,
            "committee_missed_escalations": 0,
            "single_total_escalation_errors": 0,
            "committee_total_escalation_errors": 0,
            "escalation_error_reduction_pct": 0.0,
            "avg_latency_ratio_committee_over_single": 4.0,
            "avg_cost_ratio_committee_over_single": 4.0,
            "worth_it_rule": {
                "min_error_reduction_pct": 20.0,
                "max_latency_ratio": 4.0,
                "max_cost_ratio": 4.5,
            },
            "efficiency_worth_it_decision": False,
            "worth_it_decision": False,
        },
        "case_results": [
            {
                "case": {
                    "case_id": "c1",
                    "expected_escalation": True,
                },
                "single": {
                    "escalation": True,
                    "agreement": 1.0,
                    "completion_reason": "sufficient",
                    "totals": {
                        "latency_ms": 100.0,
                        "estimated_cost_usd": 0.1,
                    },
                    "per_juror": [
                        {
                            "juror_id": "single_juror_1",
                            "profile_id": "balanced_reviewer_v1",
                            "subclaim_id": "s1",
                            "provider_model": "gpt-5.4-mini",
                            "parsed_ok": True,
                            "error_code": None,
                            "latency_ms": 100.0,
                            "tokens_used": 100,
                            "runtime_cost_usd": 0.01,
                            "estimated_cost_usd": 0.01,
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.9,
                        }
                    ],
                },
                "committee": {
                    "escalation": True,
                    "agreement": 0.75,
                    "completion_reason": "needs_review",
                    "totals": {
                        "latency_ms": 400.0,
                        "estimated_cost_usd": 0.4,
                    },
                    "per_juror": [
                        {
                            "juror_id": "juror_1",
                            "profile_id": "balanced_reviewer_v1",
                            "subclaim_id": "s1",
                            "provider_model": "gpt-5.4-mini",
                            "parsed_ok": True,
                            "error_code": None,
                            "latency_ms": 100.0,
                            "tokens_used": 100,
                            "runtime_cost_usd": 0.01,
                            "estimated_cost_usd": 0.01,
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.9,
                        }
                    ],
                },
            }
        ],
    }

    outputs = _write_protocol_output_artifacts(output_root=tmp_path, report=report)
    for key in ["per_case", "per_juror", "correlation", "frontier", "decision"]:
        assert key in outputs

    assert (tmp_path / "per_case.json").exists()
    assert (tmp_path / "per_juror.json").exists()
    assert (tmp_path / "correlation.json").exists()
    assert (tmp_path / "frontier.json").exists()
    assert (tmp_path / "decision.md").exists()

    per_case = (tmp_path / "per_case.json").read_text(encoding="utf-8")
    per_juror = (tmp_path / "per_juror.json").read_text(encoding="utf-8")
    assert '"review_mode": "holistic_single_claim"' in per_case
    assert '"review_mode": "holistic_single_claim"' in per_juror

    decision = (tmp_path / "decision.md").read_text(encoding="utf-8")
    assert "## Accuracy Value" in decision
    assert "## Trust Value" in decision
    assert "does not disqualify committee" in decision
    assert "Committee remains core to Symposia's product thesis" in decision


def test_build_decision_markdown_avoids_efficiency_only_conclusion() -> None:
    report = {
        "summary": {
            "escalation_error_reduction_pct": 0.0,
            "avg_latency_ratio_committee_over_single": 4.0,
            "avg_cost_ratio_committee_over_single": 4.0,
        }
    }

    decision = _build_decision_markdown(report)
    assert "trust" in decision.lower()
    assert "does not disqualify committee" in decision


def test_comparison_runner_supports_distinct_single_route_set(monkeypatch, tmp_path) -> None:
    def make_route(route_set_id: str, assignments: list[tuple[str, str, str]]) -> JurorRoutingConfig:
        return JurorRoutingConfig(
            version="v1",
            route_set_id=route_set_id,
            stage="initial",
            domain="all",
            output_schema="juror_decision_v1",
            guardrails=JurorRoutingGuardrails(
                max_premium_jurors_per_run=0,
                require_provider_diversity=False,
                require_model_family_diversity=False,
                premium_allowed_in_initial=False,
            ),
            assignments=[
                JurorRouteAssignment(
                    slot_id=slot_id,
                    profile_id=profile_id,
                    provider="openai",
                    model=model,
                    model_family="gpt-5.4",
                    tier="small_capable",
                    timeout_seconds=12,
                    max_output_tokens=600,
                    fallback=JurorRouteFallback(
                        provider="openai",
                        model=model,
                        model_family="gpt-5.4",
                    ),
                )
                for slot_id, profile_id, model in assignments
            ],
        )

    committee_route = make_route(
        "committee_route",
        [
            ("committee_balanced", "balanced_reviewer_v1", "gpt-5.4-nano"),
            ("committee_sceptical", "sceptical_verifier_v1", "gpt-5.4-nano"),
        ],
    )
    single_route = make_route(
        "single_route",
        [("single_literal", "literal_parser_v1", "gpt-5.4-nano")],
    )

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_comparison.get_route_set",
        lambda route_set_id: {
            "committee_route": committee_route,
            "single_route": single_route,
        }[route_set_id],
    )
    monkeypatch.setattr(
        "symposia.smoke.openai_initial_comparison.build_routed_llm_service_factory",
        lambda route_set, provider_registry=None: (
            lambda profile_id, domain: f"{route_set.route_set_id}:{profile_id}"
        ),
    )

    async def fake_run_variant(**kwargs):
        service_marker = kwargs["llm_service_factory"](
            kwargs["juror_specs"][0]["profile_id"],
            kwargs["case"].domain,
        )
        return {
            "run": {
                "should_stop": True,
                "completion_reason": "ok",
                "escalation": False,
                "agreement": 1.0,
            },
            "per_juror": [
                {
                    "juror_id": kwargs["juror_specs"][0]["juror_id"],
                    "profile_id": kwargs["juror_specs"][0]["profile_id"],
                    "subclaim_id": "sc_001",
                    "provider_model": service_marker,
                    "parsed_ok": True,
                    "error_code": None,
                    "latency_ms": 1.0,
                    "tokens_used": 1,
                    "runtime_cost_usd": 0.0,
                    "estimated_cost_usd": 0.0,
                    "stage": "initial",
                    "supported": True,
                    "contradicted": False,
                    "sufficient": True,
                    "confidence": 0.8,
                }
            ],
            "aggregated": {
                "sc_001": {
                    "support_score": 1.0,
                    "contradiction_score": 0.0,
                    "sufficiency_score": 1.0,
                    "issuance_score": 1.0,
                }
            },
            "totals": {
                "latency_ms": 1.0,
                "tokens_used": 1,
                "runtime_cost_usd": 0.0,
                "estimated_cost_usd": 0.0,
                "price_version": "test",
                "missing_price_models": [],
            },
        }

    monkeypatch.setattr("symposia.smoke.openai_initial_comparison._run_variant", fake_run_variant)
    monkeypatch.setattr(
        "symposia.smoke.openai_initial_comparison.build_resolved_protocol_artifact",
        lambda **kwargs: {"route_set_id": kwargs["route_set_id"]},
    )
    monkeypatch.setattr(
        "symposia.smoke.openai_initial_comparison._write_protocol_output_artifacts",
        lambda **kwargs: {},
    )

    report = run_openai_initial_comparison(
        output_dir=str(tmp_path),
        route_set_id="committee_route",
        single_route_set_id="single_route",
        single_profile_id="literal_parser_v1",
        cases=[
            OpenAIRound0ComparisonCase(
                case_id="c1",
                domain="general",
                content="x",
                expected_escalation=False,
            )
        ],
        protocol_validation_enabled=False,
    )

    assert report["summary"]["route_set_id"] == "committee_route"
    assert report["summary"]["single_route_set_id"] == "single_route"
    assert report["summary"]["review_mode"] == "holistic_single_claim"
    assert report["summary"]["decomposition_mode"] == "no_decomposition"
    assert report["case_results"][0]["single"]["per_juror"][0]["provider_model"].startswith("single_route:")