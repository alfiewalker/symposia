from __future__ import annotations

from copy import deepcopy

from symposia.models.routing import JurorRoutingConfig
from symposia.routing.loader import load_juror_routing
from symposia.routing.runtime import (
    build_routed_llm_service_factory,
    routed_llm_timeout_seconds,
)

_LOADED = load_juror_routing()
ROUTING_VERSION = _LOADED.version
ROUTING_OUTPUT_SCHEMA = _LOADED.output_schema
_ROUTES = deepcopy(_LOADED.routes)


def list_route_sets() -> list[str]:
    return sorted(_ROUTES.keys())


def get_route_set(route_set_id: str) -> JurorRoutingConfig:
    if route_set_id not in _ROUTES:
        raise KeyError(f"Unknown route_set_id: {route_set_id}")
    return deepcopy(_ROUTES[route_set_id])


__all__ = [
    "ROUTING_VERSION",
    "ROUTING_OUTPUT_SCHEMA",
    "list_route_sets",
    "get_route_set",
    "build_routed_llm_service_factory",
    "routed_llm_timeout_seconds",
]
