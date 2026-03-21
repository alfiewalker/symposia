# Symposia

> Plural judgement, visible dissent, traceable adjudication.

Symposia is a committee-based judgement engine for trust-sensitive questions — claims, forecasts, and LLM outputs where a single opaque answer is not enough.

It brings plural review, controlled escalation, and auditable adjudication to questions where reliability matters.

Symposia provides structured decision support, not proof of truth or guarantees of real-world outcomes.

It is designed for teams that want a clean library surface without giving up methodological seriousness.

What Symposia is:

- structured committee judgement for trust-sensitive reliance decisions
- a system that makes dissent visible, not hidden
- a traceable adjudication layer for forecast-style, advisory, and high-stakes claims

What Symposia is not:

- a truth engine
- a prophecy engine
- a replacement for domain experts
- universally better than a single strong judge on all question types

> **Current status**
> - Repository is currently private.
> - PyPI publishing is planned once the first stable public release is ready.
> - The primary surface is intentionally small and may grow slowly.

## Evidence at a glance

| Claim structure | Mixed-family committee effect | Current reading |
|---|---|---|
| Forecast-style claims | Positive | Better target-match and weighted-score performance in development and holdout |
| Clear factual claims | Neutral | No meaningful quality lift versus same-family committee |
| Underspecified policy claims | Harmful | More critical dissent without quality gain |

This is a bounded evidence statement, not a universal committee-superiority claim. For permitted external messaging, use `docs/governance_product_note.md`.

---

## Why Symposia

Most validation systems either return a single opaque answer or expose too much internal machinery.

Symposia takes a different path:

- **Structured committee judgement is central** because trust is stronger when evaluation is plural, auditable, and dissent-aware.
- **Dissent is a first-class output**, not a side effect to suppress.
- **One small entry point** for day-one use
- **Profile-set based review** when you want tighter control
- **Escalation only when needed**, not by default
- **Traceable outputs** when you need to inspect how a verdict was reached

The result is a library that feels simple at the surface while delivering trust-oriented adjudication you can rely on.

> **When does mixed-family committee judgement help?**  
> Current evidence shows committee diversity is most valuable on **forecast-style claims** (inferential, structured uncertainty), neutral on clear factual claims, and harmful on underspecified policy claims. This is the evidence-backed boundary. See [Benchmarking and limits](#benchmarking-and-limits).

---

## What Symposia is built on

Sympoia's validation layer draws on four established frameworks:

- **Condorcet / jury theorems** — many decent judges can outperform one, provided they review independently and their errors are not correlated. This grounds the plurality logic.
  *Example: five careful reviewers can be more trustworthy than one lone reviewer, as long as they are not all making the same mistake.*

- **Cooke's Classical Model** — not all judges should count equally. Experts should be weighted by calibration against known-answer sets, not by prestige or agreement. This grounds the expert weighting logic.
  *Example: if one juror has consistently been better calibrated in the past, their judgement should carry more weight.*

- **GRADE / RAND-UCLA evidence judgement** — evidence quality matters, not just the answer. Recommendation strength should follow evidence strength. This grounds the evidence and judgement logic.
  *Example: "probably true from weak evidence" should be treated differently from "strongly supported by multiple good sources".*

- **NIST-style governance** — trust requires auditability, clear risk awareness, and institutional boundaries. This grounds the governance and trustworthiness logic.
  *Example: you should be able to inspect why a judgement was reached, where dissent came from, and what the system's limits are.*

For a deeper treatment, see [`docs/implementation/02_methodology_v2.md`](docs/implementation/02_methodology_v2.md).

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

In Symposia, `validate(...)` means: structured adjudication for trust, not only binary correctness checks.

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

Product category note: Symposia is a structured committee judgement engine; `validate(...)` is the primary API verb for invoking that adjudication flow.

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
    live=False,
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

4. Explicit live mode

```python
validate(
    content,
    domain="medical",
    live=True,
)
```

This defaults to a single OpenAI live juror (`openai:gpt-5.4-mini`) for round0.

Single-juror live model override:

```python
validate(
    content,
    domain="medical",
    model="openai:gpt-4o-mini",
    live=True,
)
```

Committee live path (experimental, opt-in):

```python
validate(
    content,
    domain="medical",
    routing="default_round0_openai",
    live=True,
)
```

Precedence and conflict contract:

- `routing` > `model` / `escalation_model` > built-in defaults
- passing `routing` together with `model` or `escalation_model` raises an error
- `model` and `escalation_model` must be in `provider:model` format
- `live=True` is required for real LLM execution; default `validate(...)` remains deterministic
- `live=True` with no explicit routing/model defaults to single-juror OpenAI round0
- current live path is round0-only; live escalation is not wired yet
- committee live path is experimental and requires explicit `routing=...`

Execution boundary note:

- The API ladder and validation contract are wired.
- The public `validate(...)` surface still defaults to the deterministic path.
- The explicit live path is now wired behind `live=True`, defaulting to a single OpenAI juror.
- The committee live path remains available as an explicit experimental opt-in via routing.
- The OpenAI smoke path remains the validated narrow slice via `examples/openai_round0_live_smoke.py` and `default_round0_openai`.

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
- committee structure when plural judgement adds measurable value
- escalation only when initial review is not sufficient
- deterministic thresholds
- traceability and replayability
- small public surface, stronger internal discipline

The experimental ladder (see `docs/implementation/22_experimental_ladder_and_testing_revamp.md`) governs how committee advantage is evaluated: plurality effect first, cross-family diversity effect second, quality–count frontier last. Claims follow the evidence; each rung must be earned.

For deeper detail, see the documentation set and methodology files in the repository.

Recommended starting points:

- `docs/implementation/02_methodology_v2.md`
- `docs/implementation/03_system_spec.md`
- `docs/implementation/06_calibration_and_evaluation.md`
- `docs/implementation/13_profile_sets.md`
- `docs/implementation/14_profile_selection_strategy.md`
- `docs/implementation/15_testing_strategy.md`
- `docs/implementation/22_experimental_ladder_and_testing_revamp.md`
- `docs/governance_product_note.md`

---

## Benchmarking and limits

Symposia includes evaluation and benchmark tooling, but it is important to interpret results carefully.

Current version notes:

- benchmark and acceptance suites are useful, but not the same thing as universal proof
- committee advantage depends on meaningful profile diversity
- profile behaviour is still partly code-defined and will be externalised carefully over time
- domain-specific behaviour should be treated as controlled review posture, not as absolute authority

### Current experimental evidence boundary (2026-03-21)

Controlled decomposition experiments (Steps 2 vs 3 on the experimental ladder) show a clear boundary:

| Case family | Mixed-family committee vs same-family | Notes |
|---|---|---|
| **forecast-style claims** | **positive lift** — target match and weighted score improve in both splits | Consistent across development and holdout |
| low-risk clear factual | neutral — no measurable lift | Committees converge regardless of family; diversity adds nothing |
| underspecified legal/policy | **harmful** — weighted score falls, critical dissent spikes | Diversity increases disagreement without improving judgement |

The bounded claim is:

> **Symposia's mixed-family committee value is claim-structure-dependent. It appears strongest on forecast-style questions, neutral on clear factual questions, and harmful on underspecified policy questions.**

This is the first positive proof case for the diversity-adds-value thesis. It is family-scoped and does not generalize across all claim types.

For public positioning and permitted messaging, use `docs/governance_product_note.md` as the canonical reference.

Detailed evidence sources:

- `docs/benchmark-summary.md`
- `artifacts/trust_pipeline_runs/2026-03-21-family-focused-validation/family_lift_and_focused_validation_summary.json`
- `artifacts/trust_pipeline_runs/2026-03-21-adjacent-family-validation/adjacent_family_validation_summary.json`

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
- `docs/governance_product_note.md`
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
