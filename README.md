# Symposia

> Validation is not a single answer. It is disciplined collective judgement.

Symposia is a Python library for validating whether content is sufficiently supported to rely on. It combines independent juror review, deterministic escalation, and traceable adjudication behind a deliberately small public interface.

It is designed for teams that want a clean library surface without giving up methodological seriousness.

> **Current status**
> - Repository is currently private.
> - PyPI publishing is planned once the first stable public release is ready.
> - The primary surface is intentionally small and may grow slowly.

---

## Why Symposia

Most validation systems either return a single opaque answer or expose too much internal machinery.

Symposia takes a different path:

- **One small entry point** for day-one use
- **Profile-set based review** when you want tighter control
- **Escalation only when needed**, not by default
- **Traceable outputs** when you need to inspect how a verdict was reached

The result is a library that feels simple at the surface and disciplined underneath.

---

## The smallest useful example

```python
from symposia import validate

result = validate(
    content=(
        "If you're experiencing chest pain, shortness of breath, and dizziness, "
        "these could be signs of a heart attack. You should immediately call 911 "
        "or go to the nearest emergency room."
    ),
    domain="medical",
)

print(result.verdict)
print(result.risk)
print(result.agreement)
```

In Symposia, `validate(...)` means: assess whether content is sufficiently supported, credible, and safe to rely on under the chosen review setup.

---

## Three ideas. Everything else stays behind the curtain.

### 1. Validate
Ask Symposia to review content and return an adjudicated result.

### 2. Load a profile set
Optionally inspect or preselect the profile set that will be used for review.

### 3. Inspect when needed
Go deeper only when you need trace, escalation, or methodology detail.

That is the intended shape of the library.

---

## Installation

### Local development

```bash
pip install -e .
```

### Requirements

- Python 3.11+
- See `setup.py` for the current package metadata and dependencies.

> PyPI installation instructions will be added once Symposia is published publicly.

---

## Quickstart

### Validate content

```python
from symposia import validate

result = validate(
    content="Some evidence suggests this supplement is completely safe and has no side effects.",
    domain="medical",
)

print(result.verdict)
print(result.risk)
```

Library env-loading is explicit by design. Importing Symposia does not auto-load `.env`.

If you want development convenience from code, opt in explicitly:

```python
from symposia.env import load_env
from symposia import validate

load_env()

result = validate(content="...", domain="medical")
```

### Resolve a profile set first

```python
from symposia import load_profile_set, validate

profile_set = load_profile_set(domain="finance")

result = validate(
    content="Early findings suggest this strategy could be beneficial with no known risks.",
    domain="finance",
    profile_set=profile_set.id,
)
```

### Use a specific profile when needed

```python
from symposia import validate

result = validate(
    content="This clause always transfers liability away from the buyer.",
    domain="legal",
    profile="legal_specialist_v1",
)
```

---

## Public API

Symposia’s root surface is intentionally small.

### `validate(...)`

```python
validate(
    content,
    domain,
    profile_set=None,
    profile=None,
    model=None,
    escalation_model=None,
    routing=None,
    provider_config=None,
)
```

Validate content for a given domain and return an `InitialReviewResult`.

Use this for almost all first-day library usage.

Customization ladder:

1. Default

```python
validate(content, domain="medical")
```

2. Simple BYOM

```python
validate(content, domain="medical", model="openai:gpt-4.1-mini")
```

Optional escalation override:

```python
validate(
    content,
    domain="medical",
    model="openai:gpt-4.1-mini",
    escalation_model="openai:gpt-4.1",
)
```

3. Advanced routing

```python
validate(content, domain="medical", routing="default_round0")
```

Precedence and conflict contract:

- `routing` > `model` / `escalation_model` > built-in defaults
- passing `routing` together with `model` or `escalation_model` raises an error
- `model` and `escalation_model` must be in `provider:model` format

Execution boundary note:

- The API ladder and validation contract are wired.
- Live LLM juror execution remains a separate integration phase.

### `load_profile_set(...)`

```python
load_profile_set(domain, profile_set=None, profile=None)
```

Resolve the profile set that would be used for a given domain or explicit selection.

Use this when you want to inspect or preflight profile choice before validation.

### Top-level result types

The top-level package also exposes:

- `InitialReviewResult`
- `Risk`

Everything else should generally be treated as advanced usage and imported from explicit module paths.

---

## What the library is doing underneath

At a high level, Symposia follows this path:

1. **Decompose** the input into adjudicable subclaims
2. **Run an initial review** using a fixed profile set
3. **Aggregate judgments** into a result
4. **Escalate only when needed**
5. **Emit traceable outputs** for inspection and governance

The internal machinery is more detailed than the public API suggests by design.

---

## Profile sets

Profile sets are how Symposia controls review posture without forcing the user to assemble a committee manually.

A profile set defines things such as:

- which profiles participate
- domain defaults
- thresholds
- review posture
- escalation sensitivity

For most users, specifying `domain` is enough.

For more control, choose a named profile set explicitly.

See:

- `docs/profile-set-selection-guide.md`

---

## Domains

Current domain-oriented usage focuses on:

- **general**
- **medical**
- **legal**
- **finance**

The intent is not to claim absolute truth. The library aims to determine whether content is sufficiently supported to rely on under the current review setup.

---

## Methodology

Symposia is built around a calibrated adjudication approach:

- independent juror review first
- escalation only when initial review is not sufficient
- deterministic thresholds
- traceability and replayability
- small public surface, stronger internal discipline

For deeper detail, see the documentation set and methodology files in the repository.

Recommended starting points:

- `docs/implementation/02_methodology_v2.md`
- `docs/implementation/03_system_spec.md`
- `docs/implementation/06_calibration_and_evaluation.md`
- `docs/implementation/13_profile_sets.md`
- `docs/implementation/14_profile_selection_strategy.md`
- `docs/implementation/15_testing_strategy.md`

---

## Benchmarking and limits

Symposia includes evaluation and benchmark tooling, but it is important to interpret results carefully.

Current version notes:

- benchmark and acceptance suites are useful, but not the same thing as universal proof
- committee advantage depends on meaningful profile diversity
- profile behaviour is still partly code-defined and will be externalised carefully over time
- domain-specific behaviour should be treated as controlled review posture, not as absolute authority

See:

- `docs/benchmark-summary.md`

---

## Repository status

This repository is currently private while the first stable public release shape is being finalised.

The immediate priorities are:

- stabilise the release surface
- complete GitHub release hygiene
- prepare profile-set externalisation
- continue tightening documentation-to-code parity

When the package is ready for broader release, the repository will be made public and PyPI installation instructions will be promoted to the main installation path.

---

## Development notes

For contributors and future maintainers:

- keep policy separate from behaviour
- avoid making configuration a second hidden codebase
- preserve deterministic contracts wherever possible
- prefer contract-first expansion over feature sprawl

If a field’s meaning is still enforced by string matching or spread across multiple logic sites, it is not ready to move into configuration yet.

---

## Documentation

Key reference files:

- `CHANGELOG.md`
- `RELEASE_NOTES_0.1.1.md`
- `docs/release-checklist.md`
- `docs/profile-set-selection-guide.md`
- `docs/benchmark-summary.md`
- `examples/locked_end_to_end.py`

And in `docs/implementation/`:

- methodology
- system specification
- build phases
- testing strategy
- profile sets
- profile selection strategy

---

## Version

Current release line: **0.1.1**

---

## License

Add your chosen license here once the repository is public.
