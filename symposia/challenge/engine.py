"""Challenge review engine — Phase 6.

Consumes a NextStageReviewInput and the original ClaimBundle, runs jurors
on the escalated subclaims only, and returns a NextStageReviewResult that
classifies each escalated subclaim as resolved or unresolved.

Resolution criterion: a subclaim is resolved when its post-challenge scores
pass *all* thresholds imported from symposia.escalation.thresholds.  This
deliberately mirrors the planner's trigger conditions — a subclaim is
resolved iff it would no longer be escalated.

Constraints (Phase 6 scope):
  - One pass only (max_rounds respected but challenge always runs one round).
  - Uses the same profile set that was recorded in the ChallengePacket.
  - Rule-based jurors only; no LLM or inference involved.
  - Subclaim IDs present in the packet but absent from the bundle are
    classified as unresolved (cannot review what is not there).
"""
from __future__ import annotations

import hashlib
from typing import List

from symposia.aggregation.round0 import aggregate_round0
from symposia.escalation.thresholds import (
    CONTRADICTION_CEILING,
    SUFFICIENCY_FLOOR,
    SUPPORT_FLOOR,
)
from symposia.jurors.rule_based import RuleBasedJuror
from symposia.models.claim import ClaimBundle, Subclaim
from symposia.models.escalation import NextStageReviewInput, NextStageReviewResult
from symposia.models.juror import JurorDecision
from symposia.models.round0 import SubclaimDecision
from symposia.profile_sets import get_profile_set


def _make_run_id(parent_run_id: str, profile_set_id: str) -> str:
    raw = f"challenge:{parent_run_id}:{profile_set_id}"
    return "challenge_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _is_resolved(decision: SubclaimDecision) -> bool:
    """Return True iff the subclaim no longer breaches any escalation threshold."""
    return (
        decision.support_score >= SUPPORT_FLOOR
        and decision.contradiction_score < CONTRADICTION_CEILING
        and decision.sufficiency_score >= SUFFICIENCY_FLOOR
    )


# Phase 6 resolution note:
# The current engine proves that an escalated subclaim can pass the same
# threshold set under fresh juror evaluation (same profile set, same rules).
# It does NOT yet incorporate:
#   - new evidence supplied externally
#   - explicit challenge rebuttals
#   - revised subclaim text or context
# Those capabilities belong to a future revision once the basic resolution
# path is validated by real usage.  Keep this engine scope-stable until then.


class ChallengeReviewEngine:
    """Narrow second-pass reviewer for subclaims flagged by the escalation planner."""

    def run(
        self,
        next_stage_input: NextStageReviewInput,
        bundle: ClaimBundle,
    ) -> NextStageReviewResult:
        packet = next_stage_input.challenge_packet
        escalated_ids = {issue.subclaim_id for issue in packet.escalated_issues}

        run_id = _make_run_id(next_stage_input.parent_run_id, packet.profile_set_selected)

        # Subclaims we can actually review (present in the bundle).
        reviewable: List[Subclaim] = [
            s for s in bundle.subclaims if s.subclaim_id in escalated_ids
        ]
        found_ids = {s.subclaim_id for s in reviewable}
        missing_ids = escalated_ids - found_ids   # cannot review → always unresolved

        if not reviewable:
            return NextStageReviewResult(
                run_id=run_id,
                parent_run_id=next_stage_input.parent_run_id,
                resolved_subclaim_ids=[],
                unresolved_subclaim_ids=sorted(missing_ids),
            )

        profile_set = get_profile_set(packet.profile_set_selected)
        jurors = [
            RuleBasedJuror(
                juror_id=f"challenge_juror_{idx + 1}",
                profile_id=profile_id,
            )
            for idx, profile_id in enumerate(profile_set.profiles)
        ]

        decisions: List[JurorDecision] = [
            juror.decide(subclaim)
            for subclaim in reviewable
            for juror in jurors
        ]

        aggregated = aggregate_round0(decisions)

        resolved_ids: List[str] = []
        unresolved_ids: List[str] = list(sorted(missing_ids))

        for subclaim_id in sorted(aggregated):
            if _is_resolved(aggregated[subclaim_id]):
                resolved_ids.append(subclaim_id)
            else:
                unresolved_ids.append(subclaim_id)

        return NextStageReviewResult(
            run_id=run_id,
            parent_run_id=next_stage_input.parent_run_id,
            resolved_subclaim_ids=resolved_ids,
            unresolved_subclaim_ids=unresolved_ids,
        )
