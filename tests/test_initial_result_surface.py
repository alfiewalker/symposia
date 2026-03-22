from __future__ import annotations

import pytest

from symposia.models.claim import ClaimBundle, Subclaim, SubclaimKind
from symposia.models.initial import CompletionDecision, InitialReviewResult, SubclaimDecision
from symposia.models.trace import (
    AdjudicationTrace,
    CoreTrace,
    MinimalTraceAggregation,
    MinimalTraceSubclaim,
)


pytestmark = pytest.mark.legacy


def _make_result(
    *,
    run_id: str = "surface_run",
    scores: dict[str, tuple[float, float, float]] | None = None,
    is_decisive: bool = True,
    completion_reason: str = "initial_decisive",
    with_adjudication_trace: bool = False,
) -> InitialReviewResult:
    score_map = scores if scores is not None else {"sc_001": (0.8, 0.1, 0.8)}
    subclaims = [
        Subclaim(subclaim_id=subclaim_id, text=f"Subclaim {subclaim_id}", kind=SubclaimKind.FACT)
        for subclaim_id in score_map
    ]
    bundle = ClaimBundle(bundle_id=run_id, raw_content="Surface test claim.", subclaims=subclaims)
    aggregated = {
        subclaim_id: SubclaimDecision(
            subclaim_id=subclaim_id,
            support_score=support,
            contradiction_score=contradiction,
            sufficiency_score=sufficiency,
            issuance_score=max(0.0, support - contradiction),
        )
        for subclaim_id, (support, contradiction, sufficiency) in score_map.items()
    }
    core_trace = CoreTrace(
        run_id=run_id,
        profile_set_selected="general_default_v1",
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[],
        aggregation_outcome=[
            MinimalTraceAggregation(
                subclaim_id=subclaim_id,
                support_score=support,
                contradiction_score=contradiction,
                sufficiency_score=sufficiency,
            )
            for subclaim_id, (support, contradiction, sufficiency) in score_map.items()
        ],
    )
    adjudication_trace = None
    if with_adjudication_trace:
        adjudication_trace = AdjudicationTrace(
            run_id=run_id,
            profile_set_selected="general_default_v1",
            core_trace=core_trace,
            events=[],
            explainability=[],
        )

    return InitialReviewResult(
        run_id=run_id,
        bundle=bundle,
        decisions=[],
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(is_decisive=is_decisive, reason=completion_reason),
        core_trace=core_trace,
        adjudication_trace=adjudication_trace,
    )


def test_trace_prefers_adjudication_trace_when_present():
    result = _make_result(with_adjudication_trace=True)

    assert result.trace is result.adjudication_trace


def test_trace_falls_back_to_core_trace():
    result = _make_result(with_adjudication_trace=False)

    assert result.trace is result.core_trace


def test_verdict_validated_for_clean_decisive_scores():
    result = _make_result(scores={"sc_001": (0.8, 0.1, 0.8)}, is_decisive=True)

    assert result.verdict == "validated"


def test_verdict_rejected_for_heavy_contradiction():
    result = _make_result(scores={"sc_001": (0.2, 0.7, 0.9)}, is_decisive=False)

    assert result.verdict == "rejected"


def test_verdict_insufficient_for_low_sufficiency():
    result = _make_result(scores={"sc_001": (0.9, 0.1, 0.6)}, is_decisive=False)

    assert result.verdict == "insufficient"


def test_verdict_contested_for_non_decisive_mixed_case():
    result = _make_result(
        scores={"sc_001": (0.75, 0.2, 0.8)},
        is_decisive=False,
        completion_reason="escalation_candidate",
    )

    assert result.verdict == "contested"


def test_agreement_is_average_net_support_signal():
    result = _make_result(
        scores={
            "sc_001": (0.8, 0.1, 0.8),
            "sc_002": (0.7, 0.2, 0.9),
        }
    )

    assert result.agreement == 0.6


def test_caveats_capture_low_sufficiency_contradiction_and_non_decisive_state():
    result = _make_result(
        scores={"sc_001": (0.65, 0.35, 0.6)},
        is_decisive=False,
        completion_reason="escalation_candidate",
    )

    assert result.caveats == [
        "Limited evidence",
        "Meaningful evidence against the claim",
        "Review did not reach a decisive outcome",
        "Needs further review",
    ]


def test_caveats_report_missing_scores_cleanly():
    result = _make_result(scores={})

    assert result.caveats == ["No scored claim units"]
    assert result.agreement == 0.0
    assert result.verdict == "insufficient"