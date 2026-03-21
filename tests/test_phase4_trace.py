import json
import pytest

pytestmark = pytest.mark.legacy

from pathlib import Path

from symposia.round0 import InitialReviewEngine
from symposia.tracing import (
    export_adjudication_trace_json,
    export_adjudication_trace_markdown,
    replay_aggregation_from_trace,
)


def test_phase4_trace_replay_matches_round0_aggregation():
    engine = InitialReviewEngine()
    result = engine.run(
        content="Water boils at lower temperatures at higher altitude due to lower atmospheric pressure.",
        domain="general",
    )

    assert result.adjudication_trace is not None
    replayed = replay_aggregation_from_trace(result.adjudication_trace)

    for subclaim_id, agg in result.aggregated_by_subclaim.items():
        assert subclaim_id in replayed
        assert replayed[subclaim_id]["support_score"] == agg.support_score
        assert replayed[subclaim_id]["contradiction_score"] == agg.contradiction_score
        assert replayed[subclaim_id]["sufficiency_score"] == agg.sufficiency_score
        assert replayed[subclaim_id]["issuance_score"] == agg.issuance_score


def test_phase4_trace_exports_are_deterministic(tmp_path):
    engine = InitialReviewEngine()
    result = engine.run(
        content="For suspected bacterial meningitis, urgent clinical evaluation is required.",
        domain="medical",
    )

    assert result.adjudication_trace is not None

    json_out = tmp_path / "trace.json"
    md_out = tmp_path / "trace.md"

    export_adjudication_trace_json(result.adjudication_trace, str(json_out))
    export_adjudication_trace_markdown(result.adjudication_trace, str(md_out))

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["run_id"] == result.run_id
    assert "events" in payload
    assert md_out.read_text(encoding="utf-8").startswith("# Adjudication Trace")


def test_phase4_trace_event_order_is_stable():
    engine = InitialReviewEngine()
    result = engine.run(
        content="Past performance does not guarantee future investment results.",
        domain="finance",
    )
    assert result.adjudication_trace is not None

    event_indices = [event.event_index for event in result.adjudication_trace.events]
    assert event_indices == sorted(event_indices)
    assert event_indices[0] == 1
    assert len(set(event_indices)) == len(event_indices)
