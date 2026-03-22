from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field

from symposia.models.base import DeterministicModel
from symposia.models.claim import ClaimBundle
from symposia.models.juror import JurorDecision
from symposia.models.trace import CoreTrace, AdjudicationTrace


class SubclaimDecision(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    support_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    sufficiency_score: float = Field(ge=0.0, le=1.0)
    issuance_score: float = Field(ge=0.0, le=1.0)


class CompletionDecision(DeterministicModel):
    should_stop: bool
    reason: str = Field(min_length=1)


class InitialReviewResult(DeterministicModel):
    run_id: str = Field(min_length=1)
    bundle: ClaimBundle
    decisions: List[JurorDecision] = Field(default_factory=list)
    aggregated_by_subclaim: Dict[str, SubclaimDecision] = Field(default_factory=dict)
    completion: CompletionDecision
    core_trace: CoreTrace
    adjudication_trace: AdjudicationTrace | None = None
    execution_policy: Dict[str, Any] = Field(default_factory=dict)
    runtime_stats: Dict[str, Any] = Field(default_factory=dict)
