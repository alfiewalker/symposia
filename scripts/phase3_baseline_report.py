#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from symposia.initial import InitialReviewEngine


def _load_baseline_cases(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def main() -> int:
    engine = InitialReviewEngine()
    baseline_cases = _load_baseline_cases(Path("benchmarks/locks/baseline_cases.jsonl"))

    lines = [
        "# Phase 3 Baseline Comparison",
        "",
        "Locked slice comparison between committee aggregation and single-juror baseline.",
        "",
        "| case_id | domain | committee_support_avg | single_juror_support_avg | committee_gte_single |",
        "|---|---|---:|---:|---|",
    ]

    all_pass = True
    for row in baseline_cases:
        result = engine.run(content=row["content"], domain=row["domain"])
        committee_support = _avg(
            [a.support_score for a in result.aggregated_by_subclaim.values()]
        )

        single_votes = [
            d for d in result.decisions if d.juror_id == "juror_1"
        ]
        single_support = _avg([1.0 if d.supported else 0.0 for d in single_votes])

        committee_gte = committee_support >= single_support
        all_pass = all_pass and committee_gte

        lines.append(
            f"| {row['case_id']} | {row['domain']} | {committee_support:.3f} | {single_support:.3f} | {str(committee_gte).lower()} |"
        )

    lines.append("")
    lines.append(f"- baseline_gate_pass: {str(all_pass).lower()}")

    output_path = Path("benchmarks/scorecards/phase3_baseline_comparison.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {output_path}")
    print(f"baseline_gate_pass={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
