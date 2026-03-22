from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field

from symposia.models.base import DeterministicModel
from symposia.models.claim import ClaimBundle
from symposia.models.juror import JurorDecision
from symposia.models.trace import CoreTrace, AdjudicationTrace


_SUPPORT_FLOOR = 0.70
_CONTRADICTION_CEILING = 0.35
_REJECTION_CONTRADICTION_THRESHOLD = 0.65
_SUFFICIENCY_FLOOR = 0.70


class SubclaimDecision(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    support_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    sufficiency_score: float = Field(ge=0.0, le=1.0)
    issuance_score: float = Field(ge=0.0, le=1.0)


class CompletionDecision(DeterministicModel):
    is_decisive: bool
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

    @property
    def trace(self) -> AdjudicationTrace | CoreTrace:
        return self.adjudication_trace or self.core_trace

    @property
    def verdict(self) -> str:
        scores = list(self.aggregated_by_subclaim.values())
        if not scores:
            return "insufficient"

        if any(score.contradiction_score >= _REJECTION_CONTRADICTION_THRESHOLD for score in scores):
            return "rejected"

        if any(score.sufficiency_score < _SUFFICIENCY_FLOOR for score in scores):
            return "insufficient"

        if self.completion.is_decisive and all(
            score.support_score >= _SUPPORT_FLOOR
            and score.contradiction_score < _CONTRADICTION_CEILING
            and score.sufficiency_score >= _SUFFICIENCY_FLOOR
            for score in scores
        ):
            return "validated"

        return "contested"

    @property
    def agreement(self) -> float:
        scores = list(self.aggregated_by_subclaim.values())
        if not scores:
            return 0.0

        return round(
            sum(max(0.0, score.support_score - score.contradiction_score) for score in scores)
            / len(scores),
            3,
        )

    @property
    def caveats(self) -> List[str]:
        scores = list(self.aggregated_by_subclaim.values())
        if not scores:
            return ["No scored claim units"]

        caveats: List[str] = []
        if any(score.sufficiency_score < _SUFFICIENCY_FLOOR for score in scores):
            caveats.append("Limited evidence")

        if any(score.contradiction_score >= _CONTRADICTION_CEILING for score in scores):
            caveats.append("Meaningful evidence against the claim")

        if not self.completion.is_decisive:
            caveats.append("Review did not reach a decisive outcome")

        if self.completion.reason == "escalation_candidate":
            caveats.append("Needs further review")

        return caveats
