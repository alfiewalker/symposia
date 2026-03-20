from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import Field

from symposia.models.base import DeterministicModel

# ---------------------------------------------------------------------------
# Boundary definition (frozen)
#
#   dissent  — an *objection record*: captures that jurors disagreed during
#              review.  A dissent is observational; it does not mandate action.
#
#   challenge — an *actionable item* packaged into a ChallengePacket and
#               forwarded to next-stage review.  Every challenge is derived
#               from escalated issues + dissents, but not every dissent
#               becomes a challenge (only MATERIAL or CRITICAL ones are
#               promoted by the planner).
# ---------------------------------------------------------------------------


class DissentSeverity(str, Enum):
    MINOR = "minor"
    MATERIAL = "material"
    CRITICAL = "critical"


class EscalationReason(str, Enum):
    LOW_SUPPORT = "low_support"
    MATERIAL_CONTRADICTION = "material_contradiction"
    LOW_SUFFICIENCY = "low_sufficiency"
    CRITICAL_DISSENT = "critical_dissent"
    REVIEW_NOT_COMPLETE = "review_not_complete"


class EscalatedIssue(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    reason_codes: List[EscalationReason] = Field(min_length=1)
    support_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    sufficiency_score: float = Field(ge=0.0, le=1.0)


class DissentRecord(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    severity: DissentSeverity
    summary: str = Field(min_length=1)
    supporting_jurors: List[str] = Field(default_factory=list)
    contradicting_jurors: List[str] = Field(default_factory=list)


class ChallengePacket(DeterministicModel):
    run_id: str = Field(min_length=1)
    profile_set_selected: str = Field(min_length=1)
    escalated_issues: List[EscalatedIssue] = Field(default_factory=list)
    dissent_records: List[DissentRecord] = Field(default_factory=list)


class NextStageReviewInput(DeterministicModel):
    parent_run_id: str = Field(min_length=1)
    mode: str = Field(min_length=1, default="challenge")
    challenge_packet: ChallengePacket
    max_rounds: int = Field(ge=1, default=1)


class NextStageReviewResult(DeterministicModel):
    """Result returned by ChallengeReviewEngine after a challenge-review pass.

    Subclaims that pass all thresholds after the challenge are listed in
    resolved_subclaim_ids.  Those that still breach any threshold, or were
    absent from the bundle, appear in unresolved_subclaim_ids.
    """

    run_id: str = Field(min_length=1)
    parent_run_id: str = Field(min_length=1)
    resolved_subclaim_ids: List[str] = Field(default_factory=list)
    unresolved_subclaim_ids: List[str] = Field(default_factory=list)


class EscalationDecision(DeterministicModel):
    should_escalate: bool
    trigger_reasons: List[EscalationReason] = Field(default_factory=list)
    escalated_issues: List[EscalatedIssue] = Field(default_factory=list)
    dissent_records: List[DissentRecord] = Field(default_factory=list)
    challenge_packet: ChallengePacket | None = None
    next_stage_input: NextStageReviewInput | None = None
