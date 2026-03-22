# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Changed
- Default review mode is now holistic single-claim review; rule-based decomposition is explicit experimental opt-in.
- Comparison/trust/silver artifacts now include explicit mode metadata (`review_mode`, plus decomposition mode where applicable).
- Public-facing messaging is now explicitly claim-structure-dependent across:
  - [README.md](README.md)
  - [docs/governance_product_note.md](docs/governance_product_note.md)
  - [docs/benchmark-summary.md](docs/benchmark-summary.md)
- Added an evidence-at-a-glance table to [README.md](README.md) for quick public interpretation.
- Clarified canonical messaging authority to [docs/governance_product_note.md](docs/governance_product_note.md).
- Updated [docs/implementation/15_testing_strategy.md](docs/implementation/15_testing_strategy.md) with a ladder-only execution profile.

### Documentation
- Narrowed benchmark source tests to the experiment-ladder pack in [docs/benchmark-summary.md](docs/benchmark-summary.md).
- Added a concrete ladder-pack pytest command in:
  - [docs/benchmark-summary.md](docs/benchmark-summary.md)
  - [docs/implementation/15_testing_strategy.md](docs/implementation/15_testing_strategy.md)

### Added
- Dedicated ladder test runner script: [scripts/run_experiment_ladder_tests.sh](scripts/run_experiment_ladder_tests.sh).
- Dedicated CI workflow for ladder-only test scope: [.github/workflows/experiment-ladder-tests.yml](.github/workflows/experiment-ladder-tests.yml).

### Changed
- Ladder test execution guidance now points to `bash scripts/run_experiment_ladder_tests.sh -q` instead of long inline pytest commands.

## [0.1.1] - 2026-03-20

### Added
- Tiny primary public API via [symposia/api.py](symposia/api.py):
  - `validate(content, domain, profile_set=None, profile=None)`
  - `load_profile_set(domain, profile_set=None, profile=None)`
- Phase 9 primary-surface contract tests in [tests/test_phase9_primary_surface.py](tests/test_phase9_primary_surface.py).
- Profile weight parity suite in [tests/test_phase9_profile_weight.py](tests/test_phase9_profile_weight.py).
- Profile set selection guide in [docs/profile-set-selection-guide.md](docs/profile-set-selection-guide.md).
- Benchmark snapshot artifact in [docs/benchmark-summary.md](docs/benchmark-summary.md).
- Locked deterministic end-to-end example in [examples/locked_end_to_end.py](examples/locked_end_to_end.py).
- Release checklist in [docs/release-checklist.md](docs/release-checklist.md).

### Changed
- Top-level `__all__` is intentionally tiny in [symposia/__init__.py](symposia/__init__.py):
  - `validate`
  - `load_profile_set`
  - `Risk`
  - `InitialReviewResult`
- Aggregation weights are now owned by the profile model:
  - Added `Profile.weight` in [symposia/models/profile.py](symposia/models/profile.py).
  - Added explicit weights to built-in profiles in [symposia/profiles/defaults.py](symposia/profiles/defaults.py).
  - Replaced substring-based weighting with profile-registry lookup in [symposia/aggregation/initial.py](symposia/aggregation/initial.py).
- README rewritten for day-one usage around the tiny API in [README.md](README.md).
- Package metadata version and description updated in [setup.py](setup.py).

### Removed
- Obsolete legacy example path [examples/main.py](examples/main.py) that depended on the pre-Phase 9 committee API.

### Verified
- Full regression suite passes: `182 passed`.
- Release commit: `ccb780dcb7e431b158b5cd0f807a3ce649885fdc` (tag `v0.1.1`).
