from __future__ import annotations

from copy import deepcopy

from symposia.models.profile import ProfileSet
from symposia.profile_sets.defaults import BUILTIN_PROFILE_SETS, DOMAIN_DEFAULT_PROFILE_SET

_PROFILE_SET_REGISTRY = {k: deepcopy(v) for k, v in BUILTIN_PROFILE_SETS.items()}


def register_profile_set(profile_set: ProfileSet) -> None:
    _PROFILE_SET_REGISTRY[profile_set.profile_set_id] = deepcopy(profile_set)


def get_profile_set(profile_set_id: str) -> ProfileSet:
    if profile_set_id not in _PROFILE_SET_REGISTRY:
        raise KeyError(f"Unknown profile_set_id: {profile_set_id}")
    return deepcopy(_PROFILE_SET_REGISTRY[profile_set_id])


def get_default_profile_set(domain: str) -> ProfileSet:
    if domain not in DOMAIN_DEFAULT_PROFILE_SET:
        raise KeyError(f"Unknown domain: {domain}")
    return get_profile_set(DOMAIN_DEFAULT_PROFILE_SET[domain])


def list_profile_sets() -> list[str]:
    return sorted(_PROFILE_SET_REGISTRY.keys())


__all__ = [
    "register_profile_set",
    "get_profile_set",
    "get_default_profile_set",
    "list_profile_sets",
    "BUILTIN_PROFILE_SETS",
    "DOMAIN_DEFAULT_PROFILE_SET",
]
