from __future__ import annotations

from pathlib import Path

from symposia.models.trace import AdjudicationTrace


def export_adjudication_trace_json(trace: AdjudicationTrace, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(trace.to_canonical_json() + "\n", encoding="utf-8")


def export_adjudication_trace_markdown(trace: AdjudicationTrace, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Adjudication Trace {trace.run_id}",
        "",
        f"- profile_set_selected: {trace.profile_set_selected}",
        f"- event_count: {len(trace.events)}",
        "",
        "## Explainability",
    ]
    for item in trace.explainability:
        lines.append(f"- {item.subclaim_id}: {item.verdict_hint} ({item.reason})")

    lines.append("")
    lines.append("## Events")
    for event in trace.events:
        lines.append(
            f"- [{event.event_index}] {event.event_type} {event.entity_id}: {event.message}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
