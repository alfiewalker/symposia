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
