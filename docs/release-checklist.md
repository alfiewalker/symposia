# Release Checklist

This checklist is for Phase 10 release hardening and governance polish.

## 1. Versioning

- [x] Bump version in [setup.py](setup.py).
- [x] Bump version in [symposia/__init__.py](symposia/__init__.py).
- [x] Add a dated entry in [CHANGELOG.md](CHANGELOG.md).

## 2. Public Surface Freeze

- [x] Confirm top-level `__all__` remains tiny in [symposia/__init__.py](symposia/__init__.py).
- [x] Confirm day-one docs only advertise:
  - `validate(...)`
  - `load_profile_set(...)`
- [x] Confirm advanced internals are documented as module-path imports.

## 3. Docs/Code Parity

- [x] README quickstart runs as written.
- [x] Example scripts match current API.
- [x] Benchmark summary is current in [docs/benchmark-summary.md](docs/benchmark-summary.md).
- [x] Profile guidance is current in [docs/profile-set-selection-guide.md](docs/profile-set-selection-guide.md).

## 4. Obsolete Path Cleanup

- [x] Remove or archive stale examples that rely on legacy API paths.
- [x] Remove stale docs that contradict frozen day-one surface.

## 5. Packaging Sanity

- [x] `python -m build` completes successfully.
- [x] `python -m twine check dist/*` passes.
- [x] `pip install -e .` succeeds in a clean environment.

## 6. Test and Gate Validation

- [x] Run full test suite (`pytest -q`).
- [x] Confirm phase gate checks still pass if applicable.

## 7. Governance Notes

- [x] Document current known limits and non-goals in release notes.
- [x] Ensure benchmark claims remain factual and bounded to executable tests.

## Final Sign-Off

- Date: 2026-03-20
- Version: 0.1.1
- Checklist status: complete
- Release commit: `ccb780dcb7e431b158b5cd0f807a3ce649885fdc`
- Tag: `v0.1.1` → peels to `ccb780dcb7e431b158b5cd0f807a3ce649885fdc`
- Author email on all commits: `alphamatrix59@hotmail.com`
- Scope clarification: 0.1.1 shipped with release-safe cleanup only (obsolete example removal, docs/code parity fixes, and release artifact completion). Deeper historical legacy-code deletion remains post-release work under gated cleanup phases.
- Verification snapshots:
  - Packaging: `python -m build`, `python -m twine check dist/*`, `pip install -e .`
  - Tests: full suite pass (`182 passed, 1 warning`)
  - API freeze: top-level `__all__` unchanged for 0.1.1 (`validate`, `load_profile_set`, `Risk`, `InitialReviewResult`)
