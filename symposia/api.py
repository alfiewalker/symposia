from __future__ import annotations

from symposia.config import resolve_profile_set
from symposia.models.round0 import InitialReviewResult
from symposia.models.profile import ProfileSet
from symposia.round0 import InitialReviewEngine


def validate(
    content: str,
    domain: str,
    profile_set: str | None = None,
    profile: str | None = None,
) -> InitialReviewResult:
    """Run one deterministic validation pass and return structured results.

    This is the primary day-one API: a single call that performs
    decomposition, profile-set resolution, juror voting, aggregation,
    early-stop decisioning, and trace construction.
    """
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
