from __future__ import annotations

import os
from typing import Callable

from symposia.config.models import LLMServiceConfig
from symposia.core.providers.base import LLMService
from symposia.models.routing import JurorRouteAssignment, JurorRoutingConfig
from symposia.providers import ProviderRegistry


def _resolve_provider_service_class(provider: str):
    if provider == "openai":
        from symposia.core.providers.openai_service import OpenAIService

        return OpenAIService
    if provider == "anthropic":
        from symposia.core.providers.claude_service import ClaudeService

        return ClaudeService
    if provider == "google":
        from symposia.core.providers.gemini_service import GeminiService

        return GeminiService
    return None

_PROVIDER_ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def _resolve_provider_key(
    provider: str,
    provider_registry: ProviderRegistry | None,
) -> str | None:
    if provider_registry is not None:
        key = provider_registry.get_api_key(provider)  # type: ignore[arg-type]
        if key:
            return key
    env_name = _PROVIDER_ENV_MAP.get(provider)
    if env_name is None:
        raise ValueError(f"Unsupported provider in routed LLM runtime: {provider}")
    return os.getenv(env_name)


def _build_assignment_service(
    assignment: JurorRouteAssignment,
    provider_registry: ProviderRegistry | None,
) -> LLMService:
    service_class = _resolve_provider_service_class(assignment.provider)
    if service_class is None:
        raise ValueError(f"Unsupported provider in routed LLM runtime: {assignment.provider}")

    api_key = _resolve_provider_key(assignment.provider, provider_registry)
    if not api_key:
        env_name = _PROVIDER_ENV_MAP[assignment.provider]
        raise ValueError(
            "Missing provider credentials for routed LLM runtime: expected "
            f"{env_name} via environment variable or provider_config"
        )

    return service_class(
        LLMServiceConfig(
            provider=assignment.provider,
            model=assignment.model,
            cost_per_token=0.0,
            api_key=api_key,
        )
    )


def build_routed_llm_service_factory(
    route_set: JurorRoutingConfig,
    *,
    provider_registry: ProviderRegistry | None = None,
) -> Callable[[str, str], LLMService]:
    assignments_by_profile: dict[str, JurorRouteAssignment] = {}
    services_by_profile: dict[str, LLMService] = {}

    for assignment in route_set.assignments:
        if assignment.profile_id in assignments_by_profile:
            raise ValueError(
                "Routed LLM runtime requires unique profile_id assignments per route set; "
                f"duplicate profile_id='{assignment.profile_id}' in route_set_id='{route_set.route_set_id}'"
            )
        assignments_by_profile[assignment.profile_id] = assignment
        services_by_profile[assignment.profile_id] = _build_assignment_service(
            assignment,
            provider_registry,
        )

    def factory(profile_id: str, domain: str) -> LLMService:
        if route_set.domain not in {"all", domain}:
            raise ValueError(
                "Route set domain mismatch for routed LLM runtime: "
                f"route_domain='{route_set.domain}', requested_domain='{domain}'"
            )

        if profile_id not in services_by_profile:
            raise ValueError(
                "No routed LLM assignment for profile_id='"
                f"{profile_id}' in route_set_id='{route_set.route_set_id}'"
            )

        return services_by_profile[profile_id]

    return factory


def routed_llm_timeout_seconds(route_set: JurorRoutingConfig) -> float:
    return float(max(assignment.timeout_seconds for assignment in route_set.assignments))