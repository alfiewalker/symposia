from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from symposia.models.base import DeterministicModel


ModelTier = Literal["small_capable", "medium", "premium"]
RoutingStage = Literal["initial", "escalation"]


class JurorRouteFallback(DeterministicModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    model_family: str = Field(min_length=1)


class JurorRouteAssignment(DeterministicModel):
    slot_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    model_family: str = Field(min_length=1)
    tier: ModelTier
    timeout_seconds: int = Field(ge=1)
    max_output_tokens: int = Field(ge=1)
    fallback: JurorRouteFallback


class JurorRoutingGuardrails(DeterministicModel):
    max_premium_jurors_per_run: int = Field(ge=0)
    require_provider_diversity: bool = True
    require_model_family_diversity: bool = True
    premium_allowed_in_initial: bool = False


class JurorRoutingConfig(DeterministicModel):
    version: str = Field(min_length=1)
    route_set_id: str = Field(min_length=1)
    stage: RoutingStage
    domain: str = Field(min_length=1)
    output_schema: str = Field(min_length=1)
    assignments: list[JurorRouteAssignment] = Field(min_length=1)
    guardrails: JurorRoutingGuardrails
    notes: str | None = None

    @model_validator(mode="after")
    def validate_policy(self) -> "JurorRoutingConfig":
        slot_ids = [a.slot_id for a in self.assignments]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("Routing config contains duplicate slot_id values")

        premium_count = sum(1 for a in self.assignments if a.tier == "premium")
        if premium_count > self.guardrails.max_premium_jurors_per_run:
            raise ValueError(
                "Routing config exceeds max_premium_jurors_per_run guardrail"
            )

        if (
            self.stage == "initial"
            and not self.guardrails.premium_allowed_in_initial
            and premium_count > 0
        ):
            raise ValueError("Round0 routing must not include premium jurors")

        if self.guardrails.require_provider_diversity:
            providers = {a.provider for a in self.assignments}
            if len(providers) < 2:
                raise ValueError("Routing config must include at least two providers")

        if self.guardrails.require_model_family_diversity:
            families = {a.model_family for a in self.assignments}
            if len(families) < 2:
                raise ValueError("Routing config must include at least two model families")

        return self


class JurorRoutingIndex(DeterministicModel):
    version: str = Field(min_length=1)
    route_files: list[str] = Field(min_length=1)
