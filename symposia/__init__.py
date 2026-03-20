"""Symposia package root.

Primary day-one surface is intentionally tiny:
    - validate(...)
    - load_profile_set(...)

Advanced internals remain importable by module path.
"""

from symposia.api import load_profile_set, validate
from symposia.kernel import RuleBasedSubclaimDecomposer, SubclaimDecomposer
from symposia.config import resolve_profile_set
from symposia.round0 import InitialReviewEngine
from symposia.challenge import ChallengeReviewEngine
from symposia.escalation import plan_escalation
from symposia.evaluation import EvaluationHarness
from symposia.tracing import (
    build_adjudication_trace,
    export_adjudication_trace_json,
    export_adjudication_trace_markdown,
    replay_aggregation_from_trace,
)
from symposia.models import (
    SubclaimDecision,
    Certainty,
    ClaimBundle,
    CompiledSubclaimVerdict,
    CompletionDecision,
    DomainSummary,
    EscalationReason,
    DissentSeverity,
    EscalatedIssue,
    DissentRecord,
    ChallengePacket,
    NextStageReviewInput,
    NextStageReviewResult,
    EscalationDecision,
    EvaluationCase,
    EvaluationOutcome,
    EvaluationSuiteResult,
    ExpectedVerdict,
    Issuance,
    JurorDecision,
    CoreTrace,
    AdjudicationTrace,
    ExplainabilityRecord,
    Risk,
    InitialReviewResult,
    Profile,
    ProfileBehavior,
    ProfileSet,
    ProfileSetThresholds,
    Subclaim,
    SubclaimKind,
    ValidationResult,
    VerdictClass,
)

__version__ = "0.1.1"
__author__ = "Symposia Team"

__all__ = [
    "validate",
    "load_profile_set",
    "Risk",
    "InitialReviewResult",
]