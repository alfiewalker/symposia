#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

git config core.hooksPath .githooks

echo "Git hooks installed via core.hooksPath=.githooks"
echo "Phase 0.5 gate will now run on pre-push."
