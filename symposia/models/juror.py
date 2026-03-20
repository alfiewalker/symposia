from __future__ import annotations

from pydantic import Field

from symposia.models.base import DeterministicModel


class JurorDecision(DeterministicModel):
    juror_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    subclaim_id: str = Field(min_length=1)
    supported: bool
    contradicted: bool
    sufficient: bool
    issuable: bool
    confidence: float = Field(ge=0.0, le=1.0)
