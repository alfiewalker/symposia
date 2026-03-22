from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable

from symposia.models.juror import JurorDecision
from symposia.models.initial import CompletionDecision, SubclaimDecision
from symposia.models.profile import ProfileSet


def _profile_weight(profile_id: str) -> float:
    """Return the aggregation weight for a profile by reading Profile.weight.

    Falls back to 1.0 if the profile_id is not registered (e.g. in tests that
    construct JurorDecisions with synthetic profile IDs).
    """
    from symposia.profiles import get_profile  # late import — avoids circular
    try:
        return get_profile(profile_id).weight
    except KeyError:
        return 1.0


def aggregate_initial(
    decisions: Iterable[JurorDecision],
) -> Dict[str, SubclaimDecision]:
    groups: Dict[str, list[JurorDecision]] = defaultdict(list)
    for decision in decisions:
        groups[decision.subclaim_id].append(decision)

    aggregated: Dict[str, SubclaimDecision] = {}
    for subclaim_id, rows in groups.items():
        total_weight = sum(_profile_weight(row.profile_id) for row in rows)
        if total_weight == 0:
            total_weight = 1.0

        support = sum(
            _profile_weight(row.profile_id) for row in rows if row.supported
        ) / total_weight
        contradiction = sum(
            _profile_weight(row.profile_id) for row in rows if row.contradicted
        ) / total_weight
        sufficiency = sum(
            _profile_weight(row.profile_id) for row in rows if row.sufficient
        ) / total_weight
        issuance = sum(
            _profile_weight(row.profile_id) for row in rows if row.issuable
        ) / total_weight

        aggregated[subclaim_id] = SubclaimDecision(
            subclaim_id=subclaim_id,
            support_score=support,
            contradiction_score=contradiction,
            sufficiency_score=sufficiency,
            issuance_score=issuance,
        )

    return aggregated


def decide_early_stop(
    aggregated: Dict[str, SubclaimDecision],
    profile_set: ProfileSet,
) -> CompletionDecision:
    if not aggregated:
        return CompletionDecision(is_decisive=False, reason="no_subclaims")

    support_threshold = profile_set.thresholds.support
    confidence_threshold = profile_set.thresholds.confidence

    passes = all(
        row.support_score >= support_threshold
        and row.sufficiency_score >= confidence_threshold
        and row.contradiction_score < 0.35
        for row in aggregated.values()
    )
    if passes:
        return CompletionDecision(is_decisive=True, reason="initial_decisive")
    return CompletionDecision(is_decisive=False, reason="escalation_candidate")
