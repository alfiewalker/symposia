"""Phase 7 boundary-case suite.

Tests the escalation threshold logic at exact numeric boundaries defined in
symposia.escalation.thresholds.  Cases are built from pre-computed
SubclaimDecision scores, bypassing the juror entirely.

This suite isolates the planner's THRESHOLD COMPARISON LOGIC from the juror's
CLASSIFICATION LOGIC.  It is a regression guard, not a quality benchmark.

Key boundaries tested:
  SUPPORT_FLOOR = 0.70:
    support=0.699, contradiction=0.10, sufficiency=0.80 → ESCALATE (LOW_SUPPORT)
    support=0.700, contradiction=0.10, sufficiency=0.80 → PASS

  CONTRADICTION_CEILING = 0.35:
    support=0.80, contradiction=0.349, sufficiency=0.80 → PASS
    support=0.80, contradiction=0.350, sufficiency=0.80 → ESCALATE (MATERIAL_CONTRADICTION)

  SUFFICIENCY_FLOOR = 0.70:
    support=0.80, contradiction=0.10, sufficiency=0.699 → ESCALATE (LOW_SUFFICIENCY)
    support=0.80, contradiction=0.10, sufficiency=0.700 → PASS

  Exact floor values across all three:
    support=0.70, contradiction=0.349, sufficiency=0.70 → PASS (all at or past boundary)

  All three fail simultaneously:
    support=0.699, contradiction=0.350, sufficiency=0.699 → ESCALATE (all three reasons)

  REVIEW_NOT_COMPLETE interaction:
    any score + should_stop=False → REVIEW_NOT_COMPLETE fires regardless
    all scores pass + should_stop=True → no triggers at all

Note: all fixtures set should_stop=True (where noted otherwise) to isolate
score-based triggers from the completion trigger.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.legacy

from symposia.escalation import plan_escalation
from symposia.escalation.thresholds import (
    CONTRADICTION_CEILING,
    SUFFICIENCY_FLOOR,
    SUPPORT_FLOOR,
)
from symposia.models.claim import ClaimBundle, Subclaim, SubclaimKind
from symposia.models.evaluation import ExpectedVerdict
from symposia.models.juror import JurorDecision
from symposia.models.initial import CompletionDecision, InitialReviewResult, SubclaimDecision
from symposia.models.trace import CoreTrace, MinimalTraceAggregation, MinimalTraceSubclaim


def _make_result(
    run_id: str,
    scores: dict[str, tuple[float, float, float]],  # {subclaim_id: (support, contradiction, sufficiency)}
    should_stop: bool = True,
    profile_set: str = "general_default_v1",
) -> InitialReviewResult:
    """Build a minimal InitialReviewResult from pre-computed scores.

    Bypasses the juror entirely.  Used for boundary tests that target the
    planner's threshold comparisons, not juror classification.
    """
    subclaims = [
        Subclaim(subclaim_id=sid, text=f"Boundary test subclaim {sid}.", kind=SubclaimKind.FACT)
        for sid in scores
    ]
    bundle = ClaimBundle(
        bundle_id=run_id,
        raw_content=f"Boundary fixture {run_id}",
        subclaims=subclaims,
    )
    aggregated = {
        sid: SubclaimDecision(
            subclaim_id=sid,
            support_score=sup,
            contradiction_score=con,
            sufficiency_score=suf,
            issuance_score=max(0.0, sup - con),
        )
        for sid, (sup, con, suf) in scores.items()
    }
    core_trace = CoreTrace(
        run_id=run_id,
        profile_set_selected=profile_set,
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[],
        aggregation_outcome=[
            MinimalTraceAggregation(
                subclaim_id=sid,
                support_score=sup,
                contradiction_score=con,
                sufficiency_score=suf,
            )
            for sid, (sup, con, suf) in scores.items()
        ],
    )
    return InitialReviewResult(
        run_id=run_id,
        bundle=bundle,
        decisions=[],
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(
            should_stop=should_stop,
            reason="boundary_test",
        ),
        core_trace=core_trace,
    )


# ---------------------------------------------------------------------------
# SUPPORT_FLOOR boundary
# ---------------------------------------------------------------------------

def test_support_below_floor_escalates():
    result = _make_result("bd_sup_below", {"sc": (SUPPORT_FLOOR - 0.001, 0.10, 0.80)})
    decision = plan_escalation(result)
    assert decision.should_escalate is True
    assert any(r.value == "low_support" for r in decision.trigger_reasons)


def test_support_at_floor_does_not_escalate_on_support():
    result = _make_result("bd_sup_at", {"sc": (SUPPORT_FLOOR, 0.10, 0.80)})
    decision = plan_escalation(result)
    # support at floor, contradiction clear, sufficiency clear → no triggers
    assert decision.should_escalate is False


# ---------------------------------------------------------------------------
# CONTRADICTION_CEILING boundary
# ---------------------------------------------------------------------------

def test_contradiction_below_ceiling_does_not_escalate_on_contradiction():
    result = _make_result("bd_con_below", {"sc": (0.80, CONTRADICTION_CEILING - 0.001, 0.80)})
    decision = plan_escalation(result)
    assert decision.should_escalate is False


def test_contradiction_at_ceiling_escalates():
    result = _make_result("bd_con_at", {"sc": (0.80, CONTRADICTION_CEILING, 0.80)})
    decision = plan_escalation(result)
    assert decision.should_escalate is True
    assert any(r.value == "material_contradiction" for r in decision.trigger_reasons)


# ---------------------------------------------------------------------------
# SUFFICIENCY_FLOOR boundary
# ---------------------------------------------------------------------------

def test_sufficiency_below_floor_escalates():
    result = _make_result("bd_suf_below", {"sc": (0.80, 0.10, SUFFICIENCY_FLOOR - 0.001)})
    decision = plan_escalation(result)
    assert decision.should_escalate is True
    assert any(r.value == "low_sufficiency" for r in decision.trigger_reasons)


def test_sufficiency_at_floor_does_not_escalate_on_sufficiency():
    result = _make_result("bd_suf_at", {"sc": (0.80, 0.10, SUFFICIENCY_FLOOR)})
    decision = plan_escalation(result)
    assert decision.should_escalate is False


# ---------------------------------------------------------------------------
# All three exactly at boundary → PASS
# ---------------------------------------------------------------------------

def test_all_scores_at_exact_boundary_pass():
    result = _make_result(
        "bd_all_exact",
        {"sc": (SUPPORT_FLOOR, CONTRADICTION_CEILING - 0.001, SUFFICIENCY_FLOOR)},
    )
    decision = plan_escalation(result)
    assert decision.should_escalate is False


# ---------------------------------------------------------------------------
# All three fail simultaneously
# ---------------------------------------------------------------------------

def test_all_scores_fail_escalates_all_three_reasons():
    result = _make_result(
        "bd_all_fail",
        {"sc": (
            SUPPORT_FLOOR - 0.001,
            CONTRADICTION_CEILING,
            SUFFICIENCY_FLOOR - 0.001,
        )},
    )
    decision = plan_escalation(result)
    assert decision.should_escalate is True
    reason_values = {r.value for r in decision.trigger_reasons}
    assert "low_support" in reason_values
    assert "material_contradiction" in reason_values
    assert "low_sufficiency" in reason_values


# ---------------------------------------------------------------------------
# REVIEW_NOT_COMPLETE interaction: fires only when should_stop=False
# ---------------------------------------------------------------------------

def test_review_not_complete_fires_when_should_stop_false():
    # Even if all scores pass, should_stop=False fires REVIEW_NOT_COMPLETE.
    result = _make_result(
        "bd_rnc_fires",
        {"sc": (0.90, 0.10, 0.90)},
        should_stop=False,
    )
    decision = plan_escalation(result)
    assert decision.should_escalate is True
    assert any(r.value == "review_not_complete" for r in decision.trigger_reasons)


def test_review_not_complete_absent_when_should_stop_true_and_scores_pass():
    result = _make_result(
        "bd_rnc_absent",
        {"sc": (0.90, 0.10, 0.90)},
        should_stop=True,
    )
    decision = plan_escalation(result)
    assert decision.should_escalate is False
    assert not any(r.value == "review_not_complete" for r in decision.trigger_reasons)


# ---------------------------------------------------------------------------
# Multi-subclaim: one passes, one fails — escalation fires on failing one only
# ---------------------------------------------------------------------------

def test_multi_subclaim_partial_boundary():
    result = _make_result(
        "bd_multi",
        {
            "sc_pass": (0.90, 0.10, 0.90),                           # clean
            "sc_fail": (SUPPORT_FLOOR - 0.001, 0.10, SUFFICIENCY_FLOOR - 0.001),  # two reasons
        },
    )
    decision = plan_escalation(result)
    assert decision.should_escalate is True
    escalated_ids = {i.subclaim_id for i in decision.escalated_issues}
    assert escalated_ids == {"sc_fail"}
    assert "sc_pass" not in escalated_ids


# ---------------------------------------------------------------------------
# Verify threshold imports match the planner's actual comparison
# ---------------------------------------------------------------------------

def test_threshold_values_match_expected_constants():
    """Regression: verify the imported constants have not drifted from expected values.

    If this fails, a threshold was changed without updating this test.
    Update both the threshold and this assertion together.
    """
    assert SUPPORT_FLOOR == pytest.approx(0.70)
    assert CONTRADICTION_CEILING == pytest.approx(0.35)
    assert SUFFICIENCY_FLOOR == pytest.approx(0.70)
