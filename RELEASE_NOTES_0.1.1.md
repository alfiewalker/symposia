# Symposia 0.1.1 Release Notes

Release date: 2026-03-20

## Summary

Symposia 0.1.1 hardens the release around a frozen day-one API, packaging sanity, and docs/code parity. This cut prioritizes stability and reproducibility over further surface redesign.

## What Changed

### Added

- Tiny primary API entrypoints:
  - `validate(content, domain, profile_set=None, profile=None)`
  - `load_profile_set(domain, profile_set=None, profile=None)`
- Contract and parity test coverage for primary surface and profile weighting.
- Profile set selection guide.
- Benchmark summary snapshot and release checklist artifacts.
- Locked deterministic end-to-end example.

### Changed

- Top-level package export surface remains intentionally tiny:
  - `validate`
  - `load_profile_set`
  - `Risk`
  - `InitialReviewResult`
- Aggregation profile weighting now resolves via profile registry (`Profile.weight`) rather than substring matching.
- README and examples aligned to day-one usage.
- Packaging metadata updated for 0.1.1 and deterministic validation positioning.

### Removed

- Obsolete legacy example path `examples/main.py` that depended on pre-Phase-9 committee API.

## Verification

- Full regression suite: `182 passed`.
- Packaging checks:
  - `python -m build`
  - `python -m twine check dist/*`
  - `pip install -e .`
- Runtime version check confirms `0.1.1`.

## Known Limits and Non-Goals

- Current adjudication signal is rule-based and phrase-triggered, not retrieval-backed semantic reasoning.
- Accuracy claims are bounded to deterministic acceptance/benchmark fixtures.
- Committee advantage should not be generalized beyond tested suites in the current release.
- Confidence values are trace-level fields and are not currently used in aggregation score computation.

## Compatibility and Surface Policy

For 0.1.1, `Risk` and `InitialReviewResult` remain top-level exports for compatibility and release safety. Further surface slimming can be considered in a later minor release with explicit deprecation planning.
