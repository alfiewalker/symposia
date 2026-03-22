# Examples

This directory provides example assets for the current Phase 9 API surface.

## Notebooks

- [getting_started.ipynb](getting_started.ipynb)
	- Minimal walkthrough of deterministic and live execution modes with friendly output.
- [single_vs_committee_use_cases.ipynb](single_vs_committee_use_cases.ipynb)
	- Rich side-by-side notebook comparing single-juror and committee behavior on seven claims.

## Day-One Example

Run the locked deterministic example:

```bash
python examples/locked_end_to_end.py
```

This script uses only:

- `validate(...)`

and prints a stable summary object containing run metadata and escalated subclaims.

## OpenAI Initial Live Smoke

Run the narrow live smoke slice:

```bash
python examples/openai_initial_live_smoke.py
```

This script:

- loads `.env` explicitly via `load_env()`
- uses the OpenAI-only `default_initial_openai` route
- runs a small bounded Initial-stage LLM slice
- writes trace artifacts to `artifacts/live_smoke/openai_initial/`

## OpenAI Initial Comparison Runner

Run the dedicated jury-theory comparison artifact runner:

```bash
python examples/openai_initial_comparison.py
```

This runner stays narrow by design:

- OpenAI-only
- Initial-stage only
- 5-10 curated cases
- single-juror vs committee comparison on the same model

Artifacts are written to `artifacts/live_comparison/openai_initial/`:

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