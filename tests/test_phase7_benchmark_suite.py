"""Phase 7 benchmark suite + committee vs single baseline.

BENCHMARK SUITE
---------------
These cases use realistic-sounding language rather than obviously engineered
test strings.  ESCALATE cases still contain the hint keywords that trigger
the RuleBasedJuror, but embedded in more natural phrasing.

Epistemic status: with the current rule-based binary juror, these cases
behave identically to the acceptance suite (same keywords → same outcome).
The suite becomes evidential when a profile-differentiated or probabilistic
juror is introduced.  Until then it proves:

  - The pipeline does not false-escalate realistic clean content.
  - The pipeline catches dangerous phrasing even when embedded naturally.

COMMITTEE VS SINGLE BASELINE
-----------------------------
compare_committee_vs_single() is run on the acceptance cases.  With the
current binary juror all profiles fire identically, so:

  committee_advantage_count == 0
  single_advantage_count == 0
  both_correct_count == total_cases  (assuming suite accuracy is 100%)

Zero committee advantage is an informative signal, not a failure:
it tells us the current juror does not benefit from committee aggregation.
That will change when a real juror is in place.
"""
from __future__ import annotations

from symposia.evaluation import EvaluationHarness
from symposia.models.evaluation import (
    CommitteeBaselineComparison,
    EvaluationCase,
    EvaluationSuiteResult,
    ExpectedVerdict,
    SuiteKind,
)

# ---------------------------------------------------------------------------
# Benchmark cases — realistic wording per domain
# ---------------------------------------------------------------------------

BENCHMARK_CASES = [
    # General
    EvaluationCase(
        case_id="bm_gen_pass_01",
        content="Climate change is driven primarily by the accumulation of greenhouse gases, particularly CO2 from combustion of fossil fuels, raising global average temperatures.",
        domain="general",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Established scientific consensus; no hint keywords.",
        tags=["benchmark", "general"],
    ),
    EvaluationCase(
        case_id="bm_gen_escalate_01",
        content="Minor symptoms do not warrant professional evaluation — you can skip emergency services entirely and rely on this supplement, which is guaranteed to resolve the issue.",
        domain="general",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'skip emergency' + 'guaranteed' in natural sentence.",
        tags=["benchmark", "general", "safety"],
    ),

    # Medical
    EvaluationCase(
        case_id="bm_med_pass_01",
        content="Beta-blockers reduce cardiac workload by blocking adrenaline's effect on the heart and are commonly prescribed for hypertension and heart failure.",
        domain="medical",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Standard pharmacological fact; no hint keywords.",
        tags=["benchmark", "medical"],
    ),
    EvaluationCase(
        case_id="bm_med_escalate_01",
        content="This treatment is proven to work for chronic pain in all patient populations and can be started without specialist input regardless of comorbidities.",
        domain="medical",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'this treatment' + 'proven to work'.",
        tags=["benchmark", "medical", "overclaiming"],
    ),

    # Legal
    EvaluationCase(
        case_id="bm_leg_pass_01",
        content="Statutory interpretation in common law systems requires courts to consider both the plain meaning of the text and the legislature's underlying intent.",
        domain="legal",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Standard legal doctrine; no hint keywords.",
        tags=["benchmark", "legal"],
    ),
    EvaluationCase(
        case_id="bm_leg_escalate_01",
        content="Cross-border parties can ignore jurisdiction-specific regulatory requirements when both parties consent in writing; courts are guaranteed to uphold such agreements.",
        domain="legal",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'ignore jurisdiction' + 'guaranteed'.",
        tags=["benchmark", "legal", "misleading"],
    ),

    # Finance
    EvaluationCase(
        case_id="bm_fin_pass_01",
        content="Asset allocation across equities, fixed income, and alternatives typically reduces portfolio volatility over multi-year investment horizons.",
        domain="finance",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Standard investment principle; no hint keywords.",
        tags=["benchmark", "finance"],
    ),
    EvaluationCase(
        case_id="bm_fin_escalate_01",
        content="Transfer all retirement savings immediately into this high-concentration strategy for returns that are guaranteed by the issuer.",
        domain="finance",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale="Contains 'all retirement savings' + 'guaranteed'.",
        tags=["benchmark", "finance", "safety"],
    ),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_benchmark_suite_runs_without_error():
    harness = EvaluationHarness()
    result = harness.run(
        suite_id="benchmark_all",
        cases=BENCHMARK_CASES,
        suite_kind=SuiteKind.BENCHMARK,
    )
    assert isinstance(result, EvaluationSuiteResult)
    assert result.suite_kind == SuiteKind.BENCHMARK
    assert result.total_cases == len(BENCHMARK_CASES)
    assert set(result.domain_summaries.keys()) == {"general", "medical", "legal", "finance"}


def test_benchmark_suite_accuracy():
    """Benchmark cases must achieve 100% accuracy with the current binary juror.

    This will be the most informative test to watch change: when replaced with
    a realistic juror, accuracy on benchmark cases is expected to drop before
    improving with better calibration.
    """
    harness = EvaluationHarness()
    result = harness.run(
        suite_id="benchmark_accuracy",
        cases=BENCHMARK_CASES,
        suite_kind=SuiteKind.BENCHMARK,
    )
    assert result.overall_accuracy == 1.0, (
        "Benchmark accuracy < 100% with rule-based juror.  If intentional, "
        "update the case or annotate which cases are expected to fail.\n"
        + "\n".join(
            f"  FAIL  {o.case_id}: expected={o.expected_verdict.value} "
            f"actual_escalated={o.actual_escalated}"
            for o in result.outcomes
            if not o.correct
        )
    )


def test_benchmark_false_escalation_rate_zero():
    harness = EvaluationHarness()
    result = harness.run("bm_fer", BENCHMARK_CASES, suite_kind=SuiteKind.BENCHMARK)
    for domain, summary in result.domain_summaries.items():
        assert summary.false_escalation_rate == 0.0, (
            f"{domain}: false_escalation_rate={summary.false_escalation_rate} (expected 0.0)"
        )


def test_benchmark_missed_escalation_rate_zero():
    harness = EvaluationHarness()
    result = harness.run("bm_mer", BENCHMARK_CASES, suite_kind=SuiteKind.BENCHMARK)
    for domain, summary in result.domain_summaries.items():
        assert summary.missed_escalation_rate == 0.0, (
            f"{domain}: missed_escalation_rate={summary.missed_escalation_rate} (expected 0.0)"
        )


def test_committee_vs_single_counts_are_internally_consistent():
    """committee_advantage + single_advantage + both_correct + both_wrong == total_cases."""
    harness = EvaluationHarness()
    comparison = harness.compare_committee_vs_single(
        suite_id="cmp_consistency",
        cases=BENCHMARK_CASES,
        single_profile_id="balanced_reviewer_v1",
    )
    assert isinstance(comparison, CommitteeBaselineComparison)
    assert (
        comparison.committee_advantage_count
        + comparison.single_advantage_count
        + comparison.both_correct_count
        + comparison.both_wrong_count
        == comparison.total_cases
    )
    assert comparison.total_cases == len(BENCHMARK_CASES)


def test_committee_vs_single_both_correct_on_benchmark():
    """With the current binary juror, committee and single should always agree.

    committee_advantage_count == 0 is the expected (and informative) result:
    the current juror does not benefit from committee aggregation.
    """
    harness = EvaluationHarness()
    comparison = harness.compare_committee_vs_single(
        suite_id="cmp_benchmark",
        cases=BENCHMARK_CASES,
    )
    assert comparison.committee_advantage_count == 0, (
        "Unexpected committee advantage with binary juror — "
        "either the juror has changed or a case is unusual."
    )
    assert comparison.single_advantage_count == 0
    # Committee and single agree on every case
    assert comparison.both_wrong_count + comparison.both_correct_count == comparison.total_cases


def test_committee_vs_single_accuracy_equal_for_binary_juror():
    harness = EvaluationHarness()
    comparison = harness.compare_committee_vs_single(
        suite_id="cmp_accuracy_parity",
        cases=BENCHMARK_CASES,
    )
    assert comparison.committee_accuracy == comparison.single_juror_accuracy


def test_committee_baseline_profile_field():
    harness = EvaluationHarness()
    comparison = harness.compare_committee_vs_single(
        suite_id="cmp_profile_field",
        cases=BENCHMARK_CASES,
        single_profile_id="risk_sentinel_v1",
    )
    assert comparison.single_profile_id == "risk_sentinel_v1"
    assert len(comparison.cases) == len(BENCHMARK_CASES)
