#!/usr/bin/env python3
"""Locked end-to-end example for Phase 9.

This script is intentionally deterministic and uses only the day-one API.
It does not depend on external LLM providers.
"""
from __future__ import annotations

import json

from symposia import validate


def main() -> None:
    content = (
        "You can skip emergency services entirely and rely on this supplement, "
        "which is guaranteed to resolve the issue."
    )

    result = validate(content=content, domain="general")

    escalated = [
        d.subclaim_id
        for d in result.aggregated_by_subclaim.values()
        if (d.support_score < 0.70) or (d.contradiction_score >= 0.35) or (d.sufficiency_score < 0.70)
    ]

    summary = {
        "run_id": result.run_id,
        "profile_set": result.core_trace.profile_set_selected,
        "subclaims": len(result.bundle.subclaims),
        "is_decisive": result.completion.is_decisive,
        "completion_reason": result.completion.reason,
        "escalated_subclaims": escalated,
    }

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
