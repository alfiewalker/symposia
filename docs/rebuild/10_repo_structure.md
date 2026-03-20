# Recommended Repository Structure

## Goal

Keep the repo clear, serious, and easy to navigate.

## Suggested layout

```text
symposia/
  README.md
  pyproject.toml
  src/
    symposia/
      __init__.py
      client.py
      profiles/
        __init__.py
        defaults.py
        medical.py
        legal.py
        finance.py
      profile_sets/
        __init__.py
        defaults.py
        medical.py
        legal.py
        finance.py
      policies/
      calibration/
      tracing/
      kernel/
      jurors/
      aggregation/
      escalation/
      evidence/
      verdicts/
      models/
  docs/
  tests/
    unit/
    integration/
    benchmarks/
  benchmarks/
    seed_sets/
    scorecards/
  examples/
  scripts/
```

## Package responsibilities

### `client.py`
Public entry point.

### `models/`
Typed data models:
- request
- subclaim
- juror decision
- verdict
- trace
- profile
- profile set

### `kernel/`
Claim decomposition and bundle handling.

### `jurors/`
Juror contracts and provider bindings.

### `aggregation/`
Support, contradiction, sufficiency, and issuance aggregation.

### `escalation/`
Round 1 challenge logic.

### `evidence/`
Evidence adapters and source normalisation.

### `verdicts/`
Verdict compilation and schema mapping.

### `calibration/`
Registry, scoring, snapshots, weights.

### `profiles/`
Named juror behaviour contracts.

### `profile_sets/`
Named committee composition bundles and defaults.

### `policies/`
Domain-specific rules.

### `tracing/`
Trace model and export.

## Docs layout

Suggested docs order:
- philosophy and positioning
- methodology
- spec
- public API
- profile sets
- verdict model
- evaluation
- governance
- phases
- examples

## Benchmark assets

Keep benchmark assets explicit and versioned:
- seed sets
- labels
- scorecards
- evaluation scripts
- profile-set comparisons

## Principle

The repo should make the architecture feel inevitable.
