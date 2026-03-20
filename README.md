# Symposia

Symposia is a deterministic committee-style validation library.

Phase 9 release intent: keep the day-one interface very small.

## Primary API

Most users should start with exactly one call:

```python
from symposia import validate

result = validate(
    content="This treatment is guaranteed to work for all patients.",
    domain="medical",
)

print(result.completion.should_stop)
print(result.core_trace.profile_set_selected)
```

Optional helper to inspect profile-set resolution before running validation:

```python
from symposia import load_profile_set

resolved = load_profile_set(domain="finance")
print(resolved.profile_set_id)
print(resolved.profiles)
```

Primary public surface is intentionally small:

- `validate(...)`
- `load_profile_set(...)`
- `InitialReviewResult`
- `Risk`

Advanced modules remain available by explicit module imports.

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Locked End-To-End Example

Run the deterministic locked example:

```bash
python examples/locked_end_to_end.py
```

Reference script: [examples/locked_end_to_end.py](examples/locked_end_to_end.py).

## Profile-Set Guidance

Use domain defaults unless you have a strong reason to override.

- general content: `general_default_v1`
- medical content: `medical_strict_v1`
- legal content: `legal_strict_v1`
- finance content: `finance_strict_v1`

Detailed guide: [docs/profile-set-selection-guide.md](docs/profile-set-selection-guide.md).

## Benchmark Snapshot

Current release snapshot is in [docs/benchmark-summary.md](docs/benchmark-summary.md).

## Development

Run tests:

```bash
pytest -q
```

## Documentation

- [docs/rebuild/08_build_phases.md](docs/rebuild/08_build_phases.md)
- [docs/specifications.md](docs/specifications.md)
- [docs/architecture-diagram.md](docs/architecture-diagram.md)

## License

MIT. See [LICENSE](LICENSE).

