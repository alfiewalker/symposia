from __future__ import annotations

from copy import deepcopy

from symposia.models.profile import Profile
from symposia.profiles.defaults import BUILTIN_PROFILES

_PROFILE_REGISTRY = {k: deepcopy(v) for k, v in BUILTIN_PROFILES.items()}


def register_profile(profile: Profile) -> None:
    _PROFILE_REGISTRY[profile.profile_id] = deepcopy(profile)


def get_profile(profile_id: str) -> Profile:
    if profile_id not in _PROFILE_REGISTRY:
        raise KeyError(f"Unknown profile_id: {profile_id}")
    return deepcopy(_PROFILE_REGISTRY[profile_id])


def list_profiles() -> list[str]:
    return sorted(_PROFILE_REGISTRY.keys())


__all__ = ["register_profile", "get_profile", "list_profiles", "BUILTIN_PROFILES"]
