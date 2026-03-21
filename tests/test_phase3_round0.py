import json
import pytest

pytestmark = pytest.mark.legacy

from pathlib import Path

import jsonschema

from symposia.round0 import InitialReviewEngine


def _load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_trace_schema():
    schema_path = Path("benchmarks/locks/trace_snapshots/schema_v1.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def test_round0_engine_end_to_end_on_locked_golden_cases():
    engine = InitialReviewEngine()
    schema = _load_trace_schema()
    golden_rows = _load_jsonl(Path("benchmarks/locks/golden_cases.jsonl"))

    for row in golden_rows:
        result = engine.run(content=row["content"], domain=row["domain"])

        assert result.decisions
        assert result.aggregated_by_subclaim
        assert isinstance(result.completion.should_stop, bool)

        for agg in result.aggregated_by_subclaim.values():
            assert 0.0 <= agg.support_score <= 1.0
            assert 0.0 <= agg.contradiction_score <= 1.0
            assert 0.0 <= agg.sufficiency_score <= 1.0
            assert 0.0 <= agg.issuance_score <= 1.0

        jsonschema.validate(result.core_trace.to_canonical_dict(), schema)


def test_round0_engine_end_to_end_on_locked_safety_cases():
    engine = InitialReviewEngine()
    schema = _load_trace_schema()
    safety_rows = _load_jsonl(Path("benchmarks/locks/safety_slices.jsonl"))

    for row in safety_rows:
        result = engine.run(content=row["content"], domain=row["domain"])
        jsonschema.validate(result.core_trace.to_canonical_dict(), schema)
        # Safety fixtures should produce at least one contradiction signal in current heuristics.
        assert any(a.contradiction_score > 0.0 for a in result.aggregated_by_subclaim.values())


def test_round0_engine_is_deterministic_for_same_input():
    engine = InitialReviewEngine()
    content = "Water boils at lower temperatures at higher altitude due to lower atmospheric pressure."

    first = engine.run(content=content, domain="general")
    second = engine.run(content=content, domain="general")

    assert first.to_canonical_json() == second.to_canonical_json()
