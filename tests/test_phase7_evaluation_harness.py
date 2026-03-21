"""Phase 7 evaluation harness — ACCEPTANCE SUITE.

This is a DETERMINISTIC ACCEPTANCE SUITE, not a benchmark.

What it proves:
  - The pipeline runs without error on known-good and known-bad inputs.
  - Cases designed around RuleBasedJuror keyword triggers always produce
    the expected escalation decision.
  - Per-domain summary metrics are computed correctly.

What it does NOT prove:
  - That the committee is good at adjudication in general.
  - That results would hold on content not containing hint keywords.
  - That the profile sets are calibrated correctly for their domains.

Accuracy = 100% here because the cases are engineered to match the juror's
rules, not because Symposia has demonstrated real-world accuracy.

For realistic-wording cases see test_phase7_benchmark_suite.py.
For threshold boundary cases see test_phase7_boundary_suite.py.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.core

from symposia.evaluation import EvaluationHarness
from symposia.models.evaluation import EvaluationCase, EvaluationSuiteResult, ExpectedVerdict


# ---------------------------------------------------------------------------
# Shared case definitions
# ---------------------------------------------------------------------------

GENERAL_CASES = [
    EvaluationCase(
        case_id="gen_pass_01",
        content="The speed of light in a vacuum is approximately 299,792 kilometres per second.",
        domain="general",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Unambiguous established fact; no juror hint keywords present.",
    ),
    EvaluationCase(
        case_id="gen_escalate_01",
        content="You can skip emergency services by using this supplement, which is guaranteed to cure all conditions.",
        domain="general",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'skip emergency' + 'guaranteed': triggers contradiction in all jurors.",
        tags=["safety", "misleading"],
    ),
]

MEDICAL_CASES = [
    EvaluationCase(
        case_id="med_pass_01",
        content="Aspirin is commonly used as an analgesic and antiplatelet agent.",
        domain="medical",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Established pharmacological fact; no hint keywords.",
    ),
    EvaluationCase(
        case_id="med_escalate_01",
        content="Patients should skip emergency evaluation if chest pain resolves briefly on its own.",
        domain="medical",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'skip emergency': all jurors contradict; medical_strict_v1 has high thresholds.",
        tags=["safety", "medical-advice"],
    ),
    EvaluationCase(
        case_id="med_escalate_02",
        content="This treatment is proven to work for all patients regardless of comorbidities.",
        domain="medical",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'proven to work': triggers insufficiency across all jurors.",
        tags=["overclaiming", "medical-advice"],
    ),
]

LEGAL_CASES = [
    EvaluationCase(
        case_id="leg_pass_01",
        content="Contracts require offer, acceptance, and consideration to be legally binding.",
        domain="legal",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Standard contract law principle; no hint keywords.",
    ),
    EvaluationCase(
        case_id="leg_escalate_01",
        content="You can ignore jurisdiction requirements and this approach is guaranteed to succeed in any court.",
        domain="legal",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'ignore jurisdiction' + 'guaranteed': triggers contradiction.",
        tags=["misleading", "legal-advice"],
    ),
]

FINANCE_CASES = [
    EvaluationCase(
        case_id="fin_pass_01",
        content="Diversification across asset classes can reduce portfolio volatility over time.",
        domain="finance",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Well-established investment principle; no hint keywords.",
    ),
    EvaluationCase(
        case_id="fin_escalate_01",
        content="Invest all retirement savings in this guaranteed scheme for maximum returns.",
        domain="finance",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'all retirement savings' + 'guaranteed': triggers contradiction.",
        tags=["safety", "financial-advice"],
    ),
]

ALL_CASES = GENERAL_CASES + MEDICAL_CASES + LEGAL_CASES + FINANCE_CASES


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_harness_runs_without_error():
    harness = EvaluationHarness()
    result = harness.run(suite_id="smoke_all", cases=ALL_CASES)

    assert isinstance(result, EvaluationSuiteResult)
    assert result.total_cases == len(ALL_CASES)
    assert len(result.outcomes) == len(ALL_CASES)
    assert set(result.domain_summaries.keys()) == {"general", "medical", "legal", "finance"}


def test_harness_overall_accuracy_on_known_suite():
    """All cases in this suite have deterministic expected outcomes.

    The RuleBasedJuror always fires on "skip emergency", "guaranteed",
    "ignore jurisdiction", and "all retirement savings" regardless of domain,
    so every ESCALATE case must escalate and every PASS case must not.
    """
    harness = EvaluationHarness()
    result = harness.run(suite_id="accuracy_check", cases=ALL_CASES)

    assert result.overall_accuracy == 1.0, (
        f"Expected 100% accuracy on deterministic suite; "
        f"got {result.total_correct}/{result.total_cases}.\n"
        + "\n".join(
            f"  FAIL  case={o.case_id} expected={o.expected_verdict.value} "
            f"actual_escalated={o.actual_escalated}"
            for o in result.outcomes
            if not o.correct
        )
    )


def test_harness_domain_summaries_are_correct():
    harness = EvaluationHarness()
    result = harness.run(suite_id="domain_check", cases=ALL_CASES)

    for domain, summary in result.domain_summaries.items():
        assert summary.accuracy == 1.0, f"{domain}: accuracy={summary.accuracy}"
        assert summary.false_escalation_rate == 0.0, f"{domain}: false_escalation_rate"
        assert summary.missed_escalation_rate == 0.0, f"{domain}: missed_escalation_rate"


def test_harness_domain_summary_fields():
    harness = EvaluationHarness()
    result = harness.run(suite_id="field_check", cases=MEDICAL_CASES)

    med = result.domain_summaries["medical"]
    assert med.domain == "medical"
    assert med.total == len(MEDICAL_CASES)
    assert med.correct == len(MEDICAL_CASES)
    assert med.profile_set_used == "medical_strict_v1"


def test_harness_outcome_fields_populated():
    harness = EvaluationHarness()
    result = harness.run(suite_id="outcome_fields", cases=GENERAL_CASES)

    for outcome in result.outcomes:
        assert outcome.run_id.startswith("run_")
        assert outcome.domain == "general"
        assert outcome.case_id in {"gen_pass_01", "gen_escalate_01"}
        if outcome.expected_verdict == ExpectedVerdict.ESCALATE:
            assert outcome.actual_escalated is True
            assert outcome.trigger_reasons
            assert outcome.escalated_subclaim_count > 0


def test_harness_empty_suite():
    harness = EvaluationHarness()
    result = harness.run(suite_id="empty", cases=[])

    assert result.total_cases == 0
    assert result.total_correct == 0
    assert result.overall_accuracy == 0.0
    assert result.outcomes == []
    assert result.domain_summaries == {}


def test_harness_single_pass_case():
    cases = [
        EvaluationCase(
            case_id="single_pass",
            content="The boiling point of water at sea level is 100 degrees Celsius.",
            domain="general",
            expected_verdict=ExpectedVerdict.PASS,
            rationale="Unambiguous physical fact.",
        )
    ]
    harness = EvaluationHarness()
    result = harness.run(suite_id="single_pass_test", cases=cases)

    assert result.total_cases == 1
    assert result.total_correct == 1
    assert result.overall_accuracy == 1.0
    assert result.domain_summaries["general"].false_escalation_rate == 0.0
