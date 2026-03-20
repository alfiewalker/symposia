# Benchmark Summary (Phase 9)

This artifact summarizes the deterministic benchmark and acceptance suites that currently gate release quality.

## Current Snapshot

- Full test suite: `178 passed`
- Benchmark suite: `8/8 cases correct`
- Boundary suite: threshold boundary behavior locked by regression tests
- Committee vs single baseline on benchmark cases:
  - committee advantage: `0`
  - single advantage: `0`
  - both correct: all cases

## Interpretation

Current results are expected for the rule-based juror implementation:

- Accuracy is high on deterministic suites because cases map to explicit hint rules.
- Zero committee advantage on these suites is informative, not a failure.
- Committee advantage should be re-measured after replacing or upgrading juror behavior.

## Current Limits

- The adjudication signal is rule-based and phrase-triggered, not semantic retrieval-backed reasoning.
- Accuracy values are strongest on deterministic acceptance/benchmark fixtures and do not imply broad real-world calibration.
- Committee advantage is currently case-family dependent and should not be generalized beyond the tested suites.
- Confidence values are trace fields only in the current aggregation path and are not used in score computation.

## Source Tests

- `tests/test_phase7_evaluation_harness.py`
- `tests/test_phase7_benchmark_suite.py`
- `tests/test_phase7_boundary_suite.py`
- `tests/test_phase8_profile_diversity.py`
- `tests/test_phase8_robustness.py`
- `tests/test_phase9_profile_weight.py`
- `tests/test_phase9_primary_surface.py`

## Release Gate Reminder

Treat this document as a release snapshot, not a claims paper. Keep language factual and tied to executable tests.
