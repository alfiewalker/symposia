"""Calibration evaluation harness — Phase 7.

Runs a labeled EvaluationCase suite through the full adjudication pipeline
(InitialReviewEngine → plan_escalation) and measures per-domain accuracy.

Design constraints:
  - No LLM calls; rule-based jurors only.
  - Purely functional: EvaluationHarness.run() takes a suite and returns a
    result without side effects.
  - Domain resolution uses the same fixed registry as the rest of the system.
  - Metrics are arithmetic only: no statistical inference, no smoothing.

Current limitations (important for honest reporting):
  - The current suite is an ACCEPTANCE harness, not a benchmark.  Cases are
    designed around keyword triggers in RuleBasedJuror.  Accuracy numbers
    reflect rule-coverage, not adjudication quality.
  - compare_committee_vs_single() with the current binary juror will show
    zero committee advantage because all profiles fire identically on the
    same keyword triggers.  The method is infrastructure-ready for when a
    profile-differentiated juror is introduced.

What this harness measures:
  - Whether the committee escalates cases it should escalate (recall).
  - Whether it avoids escalating cases it should pass (precision).
  - Both, combined as accuracy, broken down per domain.
  - Committee accuracy vs single-juror accuracy (compare_committee_vs_single).

What it does NOT measure (yet):
  - Calibration of individual score magnitudes.
  - Inter-juror agreement rates.
  - Effect of profile set choice on boundary cases.
  Those belong to a future evaluation extension, not here.
"""
from __future__ import annotations

from collections import defaultdict
from typing import List, Sequence

from symposia.escalation import plan_escalation
from symposia.models.evaluation import (
    CommitteeBaselineCase,
    CommitteeBaselineComparison,
    DomainSummary,
    EvaluationCase,
    EvaluationOutcome,
    EvaluationSuiteResult,
    ExpectedVerdict,
    SuiteKind,
)
from symposia.profile_sets import get_profile_set
from symposia.profile_sets import DOMAIN_DEFAULT_PROFILE_SET
from symposia.round0 import InitialReviewEngine


def _profile_set_for_domain(domain: str) -> str:
    return DOMAIN_DEFAULT_PROFILE_SET.get(domain, "general_default_v1")


def _compute_domain_summary(
    domain: str, outcomes: List[EvaluationOutcome]
) -> DomainSummary:
    total = len(outcomes)
    if total == 0:
        return DomainSummary(
            domain=domain,
            total=0,
            correct=0,
            accuracy=0.0,
            false_escalation_rate=0.0,
            missed_escalation_rate=0.0,
            profile_set_used=_profile_set_for_domain(domain),
        )

    correct = sum(1 for o in outcomes if o.correct)

    pass_cases = [o for o in outcomes if o.expected_verdict == ExpectedVerdict.PASS]
    escalate_cases = [o for o in outcomes if o.expected_verdict == ExpectedVerdict.ESCALATE]

    false_escalations = sum(1 for o in pass_cases if o.actual_escalated)
    missed_escalations = sum(1 for o in escalate_cases if not o.actual_escalated)

    false_escalation_rate = false_escalations / len(pass_cases) if pass_cases else 0.0
    missed_escalation_rate = missed_escalations / len(escalate_cases) if escalate_cases else 0.0

    return DomainSummary(
        domain=domain,
        total=total,
        correct=correct,
        accuracy=correct / total,
        false_escalation_rate=false_escalation_rate,
        missed_escalation_rate=missed_escalation_rate,
        profile_set_used=_profile_set_for_domain(domain),
    )


class EvaluationHarness:
    """Runs a labeled suite through the full adjudication pipeline."""

    def __init__(self) -> None:
        self._engine = InitialReviewEngine()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_single_case(
        self,
        case: EvaluationCase,
        profile_set_id: str | None = None,
    ) -> EvaluationOutcome:
        """Run one case through the pipeline and return its outcome.

        profile_set_id: if given, overrides the domain-default profile set.
        Used internally by compare_committee_vs_single().
        """
        initial_result = self._engine.run(
            content=case.content,
            domain=case.domain,
            profile_set=profile_set_id,
        )
        decision = plan_escalation(initial_result)
        expected_escalation = case.expected_verdict == ExpectedVerdict.ESCALATE
        correct = decision.should_escalate == expected_escalation
        return EvaluationOutcome(
            case_id=case.case_id,
            domain=case.domain,
            expected_verdict=case.expected_verdict,
            actual_escalated=decision.should_escalate,
            correct=correct,
            trigger_reasons=[r.value for r in decision.trigger_reasons],
            escalated_subclaim_count=len(decision.escalated_issues),
            run_id=initial_result.run_id,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        suite_id: str,
        cases: Sequence[EvaluationCase],
        suite_kind: SuiteKind = SuiteKind.ACCEPTANCE,
    ) -> EvaluationSuiteResult:
        """Run all cases and return aggregated results.

        suite_kind: label that declares the epistemic status of this suite.
        Use SuiteKind.ACCEPTANCE for keyword-based deterministic cases,
        SuiteKind.BENCHMARK for realistic-wording quality probes.
        Thread-safety: not guaranteed.  Single-threaded harness.
        Order of outcomes mirrors order of cases.
        """
        outcomes: List[EvaluationOutcome] = [self._run_single_case(case) for case in cases]

        by_domain: dict[str, List[EvaluationOutcome]] = defaultdict(list)
        for outcome in outcomes:
            by_domain[outcome.domain].append(outcome)

        domain_summaries = {
            domain: _compute_domain_summary(domain, domain_outcomes)
            for domain, domain_outcomes in by_domain.items()
        }

        total = len(outcomes)
        total_correct = sum(1 for o in outcomes if o.correct)

        return EvaluationSuiteResult(
            suite_id=suite_id,
            suite_kind=suite_kind,
            outcomes=outcomes,
            domain_summaries=domain_summaries,
            total_cases=total,
            total_correct=total_correct,
            overall_accuracy=total_correct / total if total > 0 else 0.0,
        )

    def compare_committee_vs_single(
        self,
        suite_id: str,
        cases: Sequence[EvaluationCase],
        single_profile_id: str = "balanced_reviewer_v1",
    ) -> CommitteeBaselineComparison:
        """Compare full-committee accuracy against a single-juror baseline.

        For each case the engine is run twice: once with the domain-default
        profile set (committee) and once with a single-profile set built from
        single_profile_id but sharing the domain's pass/fail thresholds.

        With the current rule-based juror (all profiles fire identically on
        keyword triggers) committee_advantage_count will be 0.  That is an
        informative signal: the committee adds no differentiation over a single
        juror under keyword-binary conditions.
        """
        from symposia.models.profile import ProfileSet
        from symposia.profile_sets import register_profile_set

        # Register a single-profile set per domain (shared thresholds, one juror).
        single_ps_ids: dict[str, str] = {}
        for domain in {c.domain for c in cases}:
            base_id = DOMAIN_DEFAULT_PROFILE_SET.get(domain, "general_default_v1")
            base_ps = get_profile_set(base_id)
            temp_id = f"_cmp_{single_profile_id}_{domain}"
            register_profile_set(
                ProfileSet(
                    profile_set_id=temp_id,
                    domain=domain,
                    purpose=f"Single-juror comparison baseline: {single_profile_id}",
                    juror_count=1,
                    profiles=[single_profile_id],
                    thresholds=base_ps.thresholds,
                    max_rounds=1,
                    issuance_policy=base_ps.issuance_policy,
                )
            )
            single_ps_ids[domain] = temp_id

        result_cases: List[CommitteeBaselineCase] = []
        committee_correct_n = 0
        single_correct_n = 0
        committee_advantage = 0
        single_advantage = 0
        both_correct = 0
        both_wrong = 0

        for case in cases:
            co = self._run_single_case(case)                              # committee
            so = self._run_single_case(case, single_ps_ids[case.domain]) # single
            cc, sc = co.correct, so.correct
            if cc: committee_correct_n += 1
            if sc: single_correct_n += 1
            if cc and not sc:  committee_advantage += 1
            elif sc and not cc: single_advantage += 1
            elif cc and sc:    both_correct += 1
            else:               both_wrong += 1
            result_cases.append(
                CommitteeBaselineCase(
                    case_id=case.case_id,
                    expected_verdict=case.expected_verdict,
                    committee_escalated=co.actual_escalated,
                    single_juror_escalated=so.actual_escalated,
                    committee_correct=cc,
                    single_correct=sc,
                )
            )

        n = len(cases)
        return CommitteeBaselineComparison(
            suite_id=suite_id,
            single_profile_id=single_profile_id,
            total_cases=n,
            committee_accuracy=committee_correct_n / n if n > 0 else 0.0,
            single_juror_accuracy=single_correct_n / n if n > 0 else 0.0,
            committee_advantage_count=committee_advantage,
            single_advantage_count=single_advantage,
            both_correct_count=both_correct,
            both_wrong_count=both_wrong,
            cases=result_cases,
        )
