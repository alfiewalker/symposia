from __future__ import annotations

import os

from symposia.models.routing import JurorRoutingConfig

from symposia.config import resolve_profile_set
from symposia.models.round0 import InitialReviewResult
from symposia.models.profile import ProfileSet
from symposia.providers import ProviderConfig, ProviderRegistry
from symposia.round0 import InitialReviewEngine
from symposia.routing import get_route_set


_PROVIDER_ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def _parse_provider_model(value: str, field_name: str) -> tuple[str, str]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"{field_name} must be in 'provider:model' format; got '{value}'"
        )

    provider, model = parts[0].strip(), parts[1].strip()
    if not provider or not model:
        raise ValueError(
            f"{field_name} must be in 'provider:model' format; got '{value}'"
        )

    if provider not in _PROVIDER_ENV_MAP:
        allowed = ", ".join(sorted(_PROVIDER_ENV_MAP.keys()))
        raise ValueError(
            f"Unsupported provider '{provider}' in {field_name}. Allowed: {allowed}"
        )

    return provider, model


def _resolve_provider_registry(
    provider_config: ProviderConfig | ProviderRegistry | None,
) -> ProviderRegistry | None:
    if provider_config is None:
        return None
    if isinstance(provider_config, ProviderRegistry):
        return provider_config
    if isinstance(provider_config, ProviderConfig):
        return ProviderRegistry(providers=[provider_config])
    raise TypeError("provider_config must be ProviderConfig, ProviderRegistry, or None")


def _resolve_provider_key(
    provider: str,
    provider_registry: ProviderRegistry | None,
) -> str | None:
    if provider_registry is not None:
        key = provider_registry.get_api_key(provider)  # type: ignore[arg-type]
        if key:
            return key
    return os.getenv(_PROVIDER_ENV_MAP[provider])


def _require_provider_key(
    provider: str,
    *,
    context: str,
    provider_registry: ProviderRegistry | None,
) -> None:
    key = _resolve_provider_key(provider, provider_registry)
    if key:
        return

    env_name = _PROVIDER_ENV_MAP[provider]
    raise ValueError(
        f"Missing provider credentials for {context}: expected {env_name} via "
        "environment variable or provider_config"
    )


def validate(
    content: str,
    domain: str,
    profile_set: str | None = None,
    profile: str | None = None,
    model: str | None = None,
    escalation_model: str | None = None,
    routing: str | JurorRoutingConfig | None = None,
    provider_config: ProviderConfig | ProviderRegistry | None = None,
) -> InitialReviewResult:
    """Run one deterministic validation pass and return structured results.

    In Symposia, ``validate(...)`` means assessing whether content is
    sufficiently supported, credible, and safe to rely on under the chosen
    review setup.

    This function does not mean "fact-check only" and does not claim to
    establish absolute truth. It adjudicates support quality under explicit
    profile-set policy and domain constraints.

    Different user intents map to the same validation act. Prompts such as
    "is this true?", "is this credible?", "is this safe?", "is this likely
    sound?", and "should I trust this?" all normalize to this API call.

    This is the primary day-one API: a single call that performs
    decomposition, profile-set resolution, juror voting, aggregation,
    early-stop decisioning, and trace construction.

    Routing precedence:
    - routing
    - model / escalation_model
    - built-in defaults

    Contract:
    - If routing is provided together with model or escalation_model,
      a ValueError is raised.
    - model and escalation_model must be provider:model.
    - default mode is OpenAI-first and fails fast when credentials are missing.
    """

    if routing is not None and (model is not None or escalation_model is not None):
        raise ValueError(
            "Conflicting options: routing cannot be combined with model or escalation_model"
        )

    provider_registry = _resolve_provider_registry(provider_config)

    if routing is not None:
        route_set = get_route_set(routing) if isinstance(routing, str) else routing
        for provider_name in {a.provider for a in route_set.assignments}:
            _require_provider_key(
                provider_name,
                context=f"routing route_set_id='{route_set.route_set_id}'",
                provider_registry=provider_registry,
            )

    elif model is not None or escalation_model is not None:
        if model is not None:
            provider_name, _ = _parse_provider_model(model, "model")
            _require_provider_key(
                provider_name,
                context=f"model='{model}'",
                provider_registry=provider_registry,
            )

        if escalation_model is not None:
            provider_name, _ = _parse_provider_model(
                escalation_model, "escalation_model"
            )
            _require_provider_key(
                provider_name,
                context=f"escalation_model='{escalation_model}'",
                provider_registry=provider_registry,
            )

    else:
        _require_provider_key(
            "openai",
            context="default OpenAI-first mode",
            provider_registry=provider_registry,
        )

    engine = InitialReviewEngine()
    return engine.run(
        content=content,
        domain=domain,
        profile_set=profile_set,
        profile=profile,
    )


def load_profile_set(
    domain: str,
    profile_set: str | None = None,
    profile: str | None = None,
) -> ProfileSet:
    """Resolve and return the effective profile set for a run.

    Use this when callers want to inspect the exact resolved committee
    composition before calling validate().
    """
    return resolve_profile_set(
        domain=domain,
        profile_set=profile_set,
        profile=profile,
    ).profile_set
