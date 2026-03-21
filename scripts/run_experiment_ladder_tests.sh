#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if [[ -f ".venv/bin/activate" ]]; then
  # Use project venv when available.
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

PYTHONPATH=. pytest \
PYTHONPATH=. pytest -m "core or ladder" "$@"
