from __future__ import annotations

from dataclasses import dataclass

from symposia.models.profile import ProfileSet
from symposia.profile_sets import get_default_profile_set, get_profile_set
from symposia.profiles import get_profile


@dataclass(frozen=True)
class ResolutionMetadata:
    source: str
    overlay_applied: bool


@dataclass(frozen=True)
class ResolvedProfileSet:
    profile_set: ProfileSet
    metadata: ResolutionMetadata


def resolve_profile_set(
    domain: str,
    profile_set: str | None = None,
    profile: str | None = None,
) -> ResolvedProfileSet:
    """Deterministically resolve a profile set for a run.

    Rules:
    - explicit profile_set wins
    - else domain default profile set
    - optional profile overlay is appended if not present and domain-compatible
    """

    if profile_set:
        resolved = get_profile_set(profile_set)
        source = "explicit"
    else:
        resolved = get_default_profile_set(domain)
        source = "domain_default"

    if resolved.domain != domain:
        raise ValueError(
            f"Resolved profile set domain mismatch: requested={domain}, got={resolved.domain}"
        )

    overlay_applied = False
    if profile:
        profile_obj = get_profile(profile)
        if domain not in profile_obj.compatible_domains:
            raise ValueError(
                f"Profile '{profile}' is not compatible with domain '{domain}'"
            )
        if profile not in resolved.profiles:
            resolved.profiles.append(profile)
            overlay_applied = True

    return ResolvedProfileSet(
        profile_set=resolved,
        metadata=ResolutionMetadata(source=source, overlay_applied=overlay_applied),
    )
