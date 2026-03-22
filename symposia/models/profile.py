from __future__ import annotations

from typing import List

from pydantic import Field

from symposia.models.base import DeterministicModel


class ProfileBehavior(DeterministicModel):
    stance: str = Field(min_length=1)
    literalism: str = Field(min_length=1)
    evidence_demand: str = Field(min_length=1)
    safety_bias: str = Field(min_length=1)


class Profile(DeterministicModel):
    profile_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    behavior: ProfileBehavior
    weight: float = Field(default=1.0, gt=0.0)
    failure_modes: List[str] = Field(default_factory=list)
    compatible_domains: List[str] = Field(default_factory=list)
    version: str = Field(min_length=1)


class ProfileSetThresholds(DeterministicModel):
    support: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class ProfileSet(DeterministicModel):
    profile_set_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    domain_guidance: str = Field(default="", min_length=0)
    profiles: List[str] = Field(min_length=1)

    @property
    def juror_count(self) -> int:
        return len(self.profiles)
    thresholds: ProfileSetThresholds
    max_rounds: int = Field(ge=1)
    issuance_policy: str = Field(min_length=1)
    calibration_snapshot: str | None = None
    version: str = Field(default="v1", min_length=1)
    trace_level: str = Field(default="standard", min_length=1)
    notes: str | None = None
