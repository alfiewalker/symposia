#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from symposia.env import load_env
from symposia.smoke import run_openai_initial_comparison


def main() -> None:
    load_env()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is required for examples/openai_initial_comparison.py"
        )

    output_dir = Path("artifacts/live_comparison/openai_initial")
    report = run_openai_initial_comparison(output_dir=str(output_dir))
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()