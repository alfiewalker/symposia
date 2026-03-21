# Examples

This directory provides example assets for the current Phase 9 API surface.

## Day-One Example

Run the locked deterministic example:

```bash
python examples/locked_end_to_end.py
```

This script uses only:

- `validate(...)`

and prints a stable summary object containing run metadata and escalated subclaims.

## OpenAI Round0 Live Smoke

Run the narrow live smoke slice:

```bash
python examples/openai_round0_live_smoke.py
```

This script:

- loads `.env` explicitly via `load_env()`
- uses the OpenAI-only `default_round0_openai` route
- runs a small bounded Round0 LLM slice
- writes trace artifacts to `artifacts/live_smoke/openai_round0/`

## OpenAI Round0 Comparison Runner

Run the dedicated jury-theory comparison artifact runner:

```bash
python examples/openai_round0_comparison.py
```

This runner stays narrow by design:

- OpenAI-only
- Round0-only
- 5-10 curated cases
- single-juror vs committee comparison on the same model

Artifacts are written to `artifacts/live_comparison/openai_round0/`:

- `comparison.json`
- `comparison.md`
- `per_case.json`
- `per_juror.json`
- `correlation.json`
- `frontier.json`
- `decision.md`
- `resolved_protocol.json`

## Configuration Files

Legacy YAML files are kept for advanced or historical workflows, but they are
not part of the day-one public story.