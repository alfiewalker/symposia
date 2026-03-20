# Branch Protection Checklist

## Purpose

Make Phase 0.5 gate enforcement explicit across local workflow, CI, and merge policy.

## Required Baseline

1. Canonical gate command exists and is stable.
- command: `bash scripts/phase05_gate.sh`

2. Local pre-push enforcement is enabled.
- install command: `bash scripts/install_git_hooks.sh`
- expected behavior: pre-push runs Phase 0.5 gate and blocks on failure

3. CI enforcement is enabled.
- workflow: `.github/workflows/phase05-gate.yml`
- required status check name: `phase05-gate / phase05-gate`

4. Branch protection requires the CI check.
- protected branch: `main` (and `master` if still used)
- required check: `phase05-gate / phase05-gate`
- merge blocked when check fails or is missing

## Recommended Settings

1. Require pull request before merging.
2. Require status checks to pass before merging.
3. Require branches to be up to date before merging.
4. Restrict who can push to protected branches.
5. Require conversation resolution before merging.

## Verification Runbook

1. Run local gate.
- `bash scripts/phase05_gate.sh`

2. Verify hook installation.
- `git config --get core.hooksPath`
- expected: `.githooks`

3. Simulate a failure (temporary fixture break) and confirm pre-push blocks.

4. Open a PR and confirm `phase05-gate / phase05-gate` appears and is required.

## Governance Note

Phases 1 to 3 must not progress without a green Phase 0.5 gate.
