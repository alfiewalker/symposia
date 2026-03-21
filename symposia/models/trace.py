from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field

from symposia.models.base import DeterministicModel


class MinimalTraceSubclaim(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class MinimalTraceVote(DeterministicModel):
    juror_id: str = Field(min_length=1)
    subclaim_id: str = Field(min_length=1)
    supported: bool | None = None
    contradicted: bool | None = None
    sufficient: bool | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    provider_model: str | None = None
    parsed_ok: bool | None = None
    error_code: str | None = None


class MinimalTraceAggregation(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    support_score: float | None = Field(default=None, ge=0.0, le=1.0)
    contradiction_score: float | None = Field(default=None, ge=0.0, le=1.0)
    sufficiency_score: float | None = Field(default=None, ge=0.0, le=1.0)


class CoreTrace(DeterministicModel):
    run_id: str = Field(min_length=1)
    profile_set_selected: str = Field(min_length=1)
    subclaims: List[MinimalTraceSubclaim] = Field(default_factory=list)
    juror_votes: List[MinimalTraceVote] = Field(default_factory=list)
    aggregation_outcome: List[MinimalTraceAggregation] = Field(default_factory=list)


class TraceEvent(DeterministicModel):
    event_index: int = Field(ge=1)
    event_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExplainabilityRecord(DeterministicModel):
    subclaim_id: str = Field(min_length=1)
    verdict_hint: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class AdjudicationTrace(DeterministicModel):
    run_id: str = Field(min_length=1)
    profile_set_selected: str = Field(min_length=1)
    core_trace: CoreTrace
    events: List[TraceEvent] = Field(default_factory=list)
    explainability: List[ExplainabilityRecord] = Field(default_factory=list)
