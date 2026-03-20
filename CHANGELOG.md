# Changelog

All notable changes to this project are documented in this file.

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
  - Replaced substring-based weighting with profile-registry lookup in [symposia/aggregation/round0.py](symposia/aggregation/round0.py).
- README rewritten for day-one usage around the tiny API in [README.md](README.md).
- Package metadata version and description updated in [setup.py](setup.py).

### Removed
- Obsolete legacy example path [examples/main.py](examples/main.py) that depended on the pre-Phase 9 committee API.

### Verified
- Full regression suite passes: `182 passed`.
- Release commit: `ccb780dcb7e431b158b5cd0f807a3ce649885fdc` (tag `v0.1.1`).
