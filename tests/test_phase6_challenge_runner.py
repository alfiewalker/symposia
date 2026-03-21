"""Phase 6 tests: ChallengeReviewEngine end-to-end.

All fixtures are deterministic.  The RuleBasedJuror is purely text-based,
so expected outcomes can be computed by inspection:

  Clean text (no hint keywords):
    all 5 jurors → supported=True, contradicted=False, sufficient=True
    support=1.0, contradiction=0.0, sufficiency=1.0  → RESOLVED

  Text containing "skip emergency":
    all 5 jurors → supported=False, contradicted=True, sufficient=True
    support=0.0, contradiction=1.0              → UNRESOLVED

  Text containing "proven to work":
    all 5 jurors → supported=False, contradicted=False, sufficient=False
    support=0.0, contradiction=0.0, sufficiency=0.0  → UNRESOLVED (support+sufficiency fail)

Profile set used throughout: general_default_v1 (5 profiles; includes risk_sentinel_v1).
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.legacy

from symposia.challenge import ChallengeReviewEngine
from symposia.escalation import plan_escalation
from symposia.models.claim import ClaimBundle, Subclaim, SubclaimKind
from symposia.models.escalation import (
    ChallengePacket,
    EscalatedIssue,
    EscalationReason,
    NextStageReviewInput,
    NextStageReviewResult,
)
from symposia.models.round0 import SubclaimDecision
from symposia.round0 import InitialReviewEngine


def _make_packet(
    run_id: str,
    profile_set: str,
    escalated_subclaim_ids: list[str],
    scores: dict[str, tuple[float, float, float]],   # {id: (support, contradiction, sufficiency)}
) -> ChallengePacket:
    issues = [
        EscalatedIssue(
            subclaim_id=sid,
            reason_codes=[EscalationReason.LOW_SUPPORT],
            support_score=scores[sid][0],
            contradiction_score=scores[sid][1],
            sufficiency_score=scores[sid][2],
        )
        for sid in escalated_subclaim_ids
    ]
    return ChallengePacket(
        run_id=run_id,
        profile_set_selected=profile_set,
        escalated_issues=issues,
        dissent_records=[],
    )


# ---------------------------------------------------------------------------
# Test 1: Mixed resolution — one clean subclaim resolves, one unsafe does not
# ---------------------------------------------------------------------------

def test_challenge_engine_mixed_resolution():
    bundle = ClaimBundle(
        bundle_id="t1_bundle",
        raw_content="Mixed test",
        subclaims=[
            Subclaim(subclaim_id="sc_clean", text="Water freezes at 0 degrees Celsius.", kind=SubclaimKind.FACT),
            Subclaim(subclaim_id="sc_unsafe", text="Patients should skip emergency evaluation if symptoms are mild.", kind=SubclaimKind.FACT),
        ],
    )
    packet = _make_packet(
        run_id="run_t1",
        profile_set="general_default_v1",
        escalated_subclaim_ids=["sc_clean", "sc_unsafe"],
        scores={
            "sc_clean": (0.68, 0.10, 0.65),     # was borderline → now re-evaluated
            "sc_unsafe": (0.10, 0.90, 0.80),
        },
    )
    nsi = NextStageReviewInput(parent_run_id="run_t1", challenge_packet=packet)

    engine = ChallengeReviewEngine()
    result = engine.run(nsi, bundle)

    assert isinstance(result, NextStageReviewResult)
    assert result.parent_run_id == "run_t1"
    assert "sc_clean" in result.resolved_subclaim_ids         # clean text → passes all thresholds
    assert "sc_unsafe" in result.unresolved_subclaim_ids      # unsafe hint → contradiction=1.0
    assert "sc_clean" not in result.unresolved_subclaim_ids
    assert "sc_unsafe" not in result.resolved_subclaim_ids


# ---------------------------------------------------------------------------
# Test 2: All subclaims resolve (all clean text, all jurors support)
# ---------------------------------------------------------------------------

def test_challenge_engine_all_resolve():
    bundle = ClaimBundle(
        bundle_id="t2_bundle",
        raw_content="All clean",
        subclaims=[
            Subclaim(subclaim_id="sc_a", text="The earth orbits the sun.", kind=SubclaimKind.FACT),
            Subclaim(subclaim_id="sc_b", text="Light travels at approximately 300,000 km/s.", kind=SubclaimKind.FACT),
        ],
    )
    packet = _make_packet(
        run_id="run_t2",
        profile_set="general_default_v1",
        escalated_subclaim_ids=["sc_a", "sc_b"],
        scores={"sc_a": (0.65, 0.20, 0.65), "sc_b": (0.65, 0.20, 0.65)},
    )
    nsi = NextStageReviewInput(parent_run_id="run_t2", challenge_packet=packet)

    engine = ChallengeReviewEngine()
    result = engine.run(nsi, bundle)

    assert set(result.resolved_subclaim_ids) == {"sc_a", "sc_b"}
    assert result.unresolved_subclaim_ids == []


# ---------------------------------------------------------------------------
# Test 3: Subclaim ID in packet but missing from bundle → unresolved
# ---------------------------------------------------------------------------

def test_challenge_engine_missing_subclaim_is_unresolved():
    bundle = ClaimBundle(
        bundle_id="t3_bundle",
        raw_content="Partial bundle",
        subclaims=[
            Subclaim(subclaim_id="sc_present", text="A simple factual statement.", kind=SubclaimKind.FACT),
        ],
    )
    packet = _make_packet(
        run_id="run_t3",
        profile_set="general_default_v1",
        escalated_subclaim_ids=["sc_present", "sc_ghost"],
        scores={"sc_present": (0.65, 0.20, 0.65), "sc_ghost": (0.40, 0.50, 0.40)},
    )
    nsi = NextStageReviewInput(parent_run_id="run_t3", challenge_packet=packet)

    engine = ChallengeReviewEngine()
    result = engine.run(nsi, bundle)

    assert "sc_present" in result.resolved_subclaim_ids
    assert "sc_ghost" in result.unresolved_subclaim_ids    # not in bundle → can't review → unresolved


# ---------------------------------------------------------------------------
# Test 4: Empty challenge packet → empty result
# ---------------------------------------------------------------------------

def test_challenge_engine_empty_packet():
    bundle = ClaimBundle(
        bundle_id="t4_bundle",
        raw_content="Some content",
        subclaims=[
            Subclaim(subclaim_id="sc_x", text="Some fact.", kind=SubclaimKind.FACT),
        ],
    )
    packet = ChallengePacket(
        run_id="run_t4",
        profile_set_selected="general_default_v1",
        escalated_issues=[],
        dissent_records=[],
    )
    nsi = NextStageReviewInput(parent_run_id="run_t4", challenge_packet=packet)

    engine = ChallengeReviewEngine()
    result = engine.run(nsi, bundle)

    assert result.resolved_subclaim_ids == []
    assert result.unresolved_subclaim_ids == []


# ---------------------------------------------------------------------------
# Test 5: End-to-end — InitialReviewEngine → plan_escalation → ChallengeReviewEngine
# ---------------------------------------------------------------------------

def test_end_to_end_challenge_path_on_safety_content():
    """Prove the full escalation path runs without errors on known-bad content."""
    initial_engine = InitialReviewEngine()
    initial_result = initial_engine.run(
        content="A patient with chest pain should skip emergency evaluation and self-treat at home.",
        domain="medical",
    )

    escalation_decision = plan_escalation(initial_result)
    assert escalation_decision.should_escalate is True
    assert escalation_decision.next_stage_input is not None

    challenge_engine = ChallengeReviewEngine()
    challenge_result = challenge_engine.run(
        escalation_decision.next_stage_input,
        initial_result.bundle,
    )

    assert isinstance(challenge_result, NextStageReviewResult)
    assert challenge_result.parent_run_id == initial_result.run_id

    # All subclaims that were escalated must appear in one of the two lists.
    escalated_ids = {i.subclaim_id for i in escalation_decision.escalated_issues}
    reviewed_ids = set(challenge_result.resolved_subclaim_ids) | set(challenge_result.unresolved_subclaim_ids)
    assert escalated_ids == reviewed_ids

    # The run_id is distinct from the parent (it is a new review run).
    assert challenge_result.run_id != challenge_result.parent_run_id
