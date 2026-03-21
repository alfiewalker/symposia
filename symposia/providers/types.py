from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from symposia.models.base import DeterministicModel

ProviderName = Literal["openai", "anthropic", "google"]


class ProviderConfig(DeterministicModel):
    provider: ProviderName
    api_key: str = Field(min_length=1)


class ProviderRegistry(DeterministicModel):
    providers: list[ProviderConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_providers(self) -> "ProviderRegistry":
        names = [p.provider for p in self.providers]
        if len(names) != len(set(names)):
            raise ValueError("ProviderRegistry must not contain duplicate providers")
        return self

    def get_api_key(self, provider: ProviderName) -> str | None:
        for config in self.providers:
            if config.provider == provider:
                return config.api_key
        return None
