from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import Field

from symposia.models.base import DeterministicModel


class VerdictClass(str, Enum):
    VALIDATED = "validated"
    REJECTED = "rejected"
    INSUFFICIENT = "insufficient"
    CONTESTED = "contested"


class Certainty(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class Issuance(str, Enum):
    SAFE_TO_ISSUE = "safe_to_issue"
    ISSUE_WITH_CAVEATS = "issue_with_caveats"
    REQUIRES_EXPERT_REVIEW = "requires_expert_review"
    UNSAFE_TO_ISSUE = "unsafe_to_issue"


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CompiledSubclaimVerdict(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    verdict: VerdictClass
    certainty: Certainty
    issuance: Issuance
    risk: Risk
    caveats: List[str] = Field(default_factory=list)
    agreement: float = Field(ge=0.0, le=1.0)


class ValidationResult(DeterministicModel):
    run_id: str = Field(min_length=1)
    verdict: VerdictClass
    certainty: Certainty
    issuance: Issuance
    risk: Risk
    agreement: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1)
    caveats: List[str] = Field(default_factory=list)
    subclaims: List[CompiledSubclaimVerdict] = Field(default_factory=list)
    profile_set_used: Optional[str] = None
    rounds_used: int = Field(ge=1, default=1)
    trace_id: Optional[str] = None
