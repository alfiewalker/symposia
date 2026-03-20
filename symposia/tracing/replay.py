from __future__ import annotations

from symposia.models.trace import AdjudicationTrace


def replay_aggregation_from_trace(trace: AdjudicationTrace) -> dict[str, dict[str, float]]:
    """Replay aggregation snapshot deterministically from trace events."""
    replayed: dict[str, dict[str, float]] = {}
    for event in trace.events:
        if event.event_type != "aggregation":
            continue
        subclaim_id = str(event.metadata["subclaim_id"])
        replayed[subclaim_id] = {
            "support_score": float(event.metadata["support_score"]),
            "contradiction_score": float(event.metadata["contradiction_score"]),
            "sufficiency_score": float(event.metadata["sufficiency_score"]),
            "issuance_score": float(event.metadata["issuance_score"]),
        }
    return replayed
