from __future__ import annotations

from symposia.models.round0 import InitialReviewResult
from symposia.models.trace import (
    AdjudicationTrace,
    TraceEvent,
    ExplainabilityRecord,
)


def build_adjudication_trace(initial_review_result: InitialReviewResult) -> AdjudicationTrace:
    events = []
    event_idx = 1

    events.append(
        TraceEvent(
            event_index=event_idx,
            event_type="run_started",
            entity_id=initial_review_result.run_id,
            message="Round 0 run started.",
            metadata={"subclaim_count": len(initial_review_result.bundle.subclaims)},
        )
    )
    event_idx += 1

    for subclaim in initial_review_result.bundle.subclaims:
        events.append(
            TraceEvent(
                event_index=event_idx,
                event_type="subclaim_registered",
                entity_id=subclaim.subclaim_id,
                message="Subclaim registered for adjudication.",
                metadata={"text": subclaim.text, "kind": subclaim.kind.value},
            )
        )
        event_idx += 1

    for decision in initial_review_result.decisions:
        events.append(
            TraceEvent(
                event_index=event_idx,
                event_type="juror_decision",
                entity_id=f"{decision.juror_id}:{decision.subclaim_id}",
                message="Juror decision recorded.",
                metadata={
                    "juror_id": decision.juror_id,
                    "subclaim_id": decision.subclaim_id,
                    "supported": decision.supported,
                    "contradicted": decision.contradicted,
                    "sufficient": decision.sufficient,
                    "confidence": decision.confidence,
                },
            )
        )
        event_idx += 1

    explanations = []
    for subclaim_id, agg in initial_review_result.aggregated_by_subclaim.items():
        events.append(
            TraceEvent(
                event_index=event_idx,
                event_type="aggregation",
                entity_id=subclaim_id,
                message="Subclaim aggregation computed.",
                metadata={
                    "subclaim_id": subclaim_id,
                    "support_score": agg.support_score,
                    "contradiction_score": agg.contradiction_score,
                    "sufficiency_score": agg.sufficiency_score,
                    "issuance_score": agg.issuance_score,
                },
            )
        )
        event_idx += 1

        if agg.contradiction_score >= 0.35:
            verdict_hint = "contested_or_rejected"
            reason = "material contradiction score present"
        elif agg.sufficiency_score < 0.70:
            verdict_hint = "insufficient"
            reason = "sufficiency score below deterministic floor"
        elif agg.support_score >= 0.70:
            verdict_hint = "validated_candidate"
            reason = "support and sufficiency satisfy deterministic thresholds"
        else:
            verdict_hint = "contested"
            reason = "mixed support signals"

        explanations.append(
            ExplainabilityRecord(
                subclaim_id=subclaim_id,
                verdict_hint=verdict_hint,
                reason=reason,
            )
        )

    events.append(
        TraceEvent(
            event_index=event_idx,
            event_type="early_stop",
            entity_id=initial_review_result.run_id,
            message="Early stop decision recorded.",
            metadata={
                "should_stop": initial_review_result.completion.should_stop,
                "reason": initial_review_result.completion.reason,
            },
        )
    )

    return AdjudicationTrace(
        run_id=initial_review_result.run_id,
        profile_set_selected=initial_review_result.core_trace.profile_set_selected,
        core_trace=initial_review_result.core_trace,
        events=events,
        explainability=explanations,
    )
