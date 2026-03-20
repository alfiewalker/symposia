"""Evaluation models for the Phase 7 calibration harness.

An EvaluationCase is a labeled input: content + domain + the expected verdict
(should the committee escalate, or should it pass cleanly?).

An EvaluationOutcome records what the pipeline actually produced for one case.

An EvaluationSuiteResult aggregates outcomes across a labeled suite and
computes domain-level correctness metrics.

All types are deterministic-serialisable.  None carry model outputs or
heuristically derived fields; all aggregation is arithmetic.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field

from symposia.models.base import DeterministicModel


class ExpectedVerdict(str, Enum):
    """The ground-truth label for an evaluation case."""

    PASS = "pass"           # committee should NOT escalate
    ESCALATE = "escalate"   # committee SHOULD escalate


class SuiteKind(str, Enum):
    """Characterises the epistemic claim made by an evaluation suite.

    ACCEPTANCE: deterministic, keyword/rule-based inputs.  Proves the
                pipeline does not break and basic rules fire.  Not evidence
                of adjudication quality.

    BENCHMARK:  realistic-wording cases intended to probe system quality.
                With the current rule-based juror this is structurally
                identical to ACCEPTANCE; it becomes meaningfully different
                when a probabilistic or profile-differentiated juror exists.

    BOUNDARY:   threshold-focused cases typically built from pre-computed
                SubclaimDecision scores.  Tests the planner threshold logic
                in isolation from the juror.  A BOUNDARY suite is not a
                quality benchmark — it is a regression guard on the
                numeric comparisons in plan_escalation().
    """

    ACCEPTANCE = "acceptance"
    BENCHMARK = "benchmark"
    BOUNDARY = "boundary"


class EvaluationCase(DeterministicModel):
    """A single labeled evaluation input.

    case_id must be unique within a suite.  domain must match a key in
    DOMAIN_DEFAULT_PROFILE_SET so the harness can resolve the right profile set.
    rationale is free text explaining why the expected_verdict was assigned.
    """

    case_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    expected_verdict: ExpectedVerdict
    rationale: str = Field(min_length=1)
    tags: List[str] = Field(default_factory=list)


class EvaluationOutcome(DeterministicModel):
    """What the pipeline actually produced for one EvaluationCase."""

    case_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    expected_verdict: ExpectedVerdict
    actual_escalated: bool
    correct: bool                       # actual_escalated == (expected == ESCALATE)
    trigger_reasons: List[str] = Field(default_factory=list)
    escalated_subclaim_count: int = Field(ge=0, default=0)
    run_id: str = Field(min_length=1)


class DomainSummary(DeterministicModel):
    """Aggregated correctness metrics for one domain across a suite."""

    domain: str = Field(min_length=1)
    total: int = Field(ge=0)
    correct: int = Field(ge=0)
    accuracy: float = Field(ge=0.0, le=1.0)
    false_escalation_rate: float = Field(ge=0.0, le=1.0)   # PASS cases incorrectly escalated
    missed_escalation_rate: float = Field(ge=0.0, le=1.0)  # ESCALATE cases not caught
    profile_set_used: str = Field(min_length=1)


class EvaluationSuiteResult(DeterministicModel):
    """Full result of running an evaluation suite through the harness."""

    suite_id: str = Field(min_length=1)
    suite_kind: SuiteKind = SuiteKind.ACCEPTANCE
    outcomes: List[EvaluationOutcome] = Field(default_factory=list)
    domain_summaries: Dict[str, DomainSummary] = Field(default_factory=dict)
    total_cases: int = Field(ge=0)
    total_correct: int = Field(ge=0)
    overall_accuracy: float = Field(ge=0.0, le=1.0)


class CommitteeBaselineCase(DeterministicModel):
    """Per-case committee vs single-juror comparison record."""

    case_id: str = Field(min_length=1)
    expected_verdict: ExpectedVerdict
    committee_escalated: bool
    single_juror_escalated: bool
    committee_correct: bool
    single_correct: bool


class CommitteeBaselineComparison(DeterministicModel):
    """Committee accuracy report against a single-juror baseline.

    committee_advantage_count: cases where committee was correct and single
    was wrong.  With the current rule-based juror (keyword-binary, all
    profiles fire identically) this will be 0.  It becomes non-zero when a
    profile-differentiated or probabilistic juror is introduced.

    single_advantage_count: cases where single was correct and committee
    was wrong.  Indicates committee over-escalation relative to baseline.

    The counts satisfy:
        committee_advantage + single_advantage + both_correct + both_wrong
        == total_cases
    """

    suite_id: str = Field(min_length=1)
    single_profile_id: str = Field(min_length=1)
    total_cases: int = Field(ge=0)
    committee_accuracy: float = Field(ge=0.0, le=1.0)
    single_juror_accuracy: float = Field(ge=0.0, le=1.0)
    committee_advantage_count: int = Field(ge=0)
    single_advantage_count: int = Field(ge=0)
    both_correct_count: int = Field(ge=0)
    both_wrong_count: int = Field(ge=0)
    cases: List[CommitteeBaselineCase] = Field(default_factory=list)
