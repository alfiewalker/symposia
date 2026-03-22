# Library API

## Goal

The library API must feel simple, unsurprising, and stable.

The user should feel that Symposia is:
- one object to configure
- one main method to call
- one result object to inspect

All the power should live behind profile sets, registries, and policies.

## Public surface doctrine

### Rule 1
Prefer one obvious way.

### Rule 2
Do not expose internal rounds, juror logic, or aggregation primitives unless the caller explicitly opts into advanced usage.

### Rule 3
Keep advanced extensibility behind:
- profiles
- profile sets
- hooks
- registries
- optional lower-level modules

## Recommended public objects

### `Symposia`
Primary entry point.

Responsibilities:
- load config
- bind providers
- bind profiles
- bind profile sets
- validate input
- orchestrate runs

### `ValidationResult`
Primary output.

Responsibilities:
- expose verdict
- expose certainty, issuance, risk
- expose summary and caveats
- optionally expose trace

### `Profile`
Reusable juror behaviour contract.

Examples:
- `balanced_reviewer`
- `sceptical_verifier`
- `evidence_maximalist`
- `literal_parser`
- `risk_sentinel`

### `ProfileSet`
Reusable committee composition and policy bundle.

Examples:
- `general_default_v1`
- `medical_strict_v1`
- `legal_strict_v1`
- `finance_strict_v1`

## Usage ladder

This is the intended build-up from simplest to most advanced use.

### Level 1 — simplest possible usage

```python
from symposia import Symposia

sp = Symposia()

result = sp.validate(
    content="...",
    domain="medical",
)
```

The library chooses the default domain profile set automatically.

### Level 2 — choose a named profile set

```python
result = sp.validate(
    content="...",
    domain="medical",
    profile_set="medical_strict_v1",
)
```

Use this when you want explicit reproducibility.

### Level 3 — construct a configured client

```python
sp = Symposia(
    profile_set="finance_strict_v1",
    trace=False,
)

result = sp.validate(content="...", domain="finance")
```

### Level 4 — override with one profile

```python
result = sp.validate(
    content="...",
    domain="medical",
    profile_set="medical_strict_v1",
    profile="risk_sentinel_v1",
)
```

This should be interpreted as an overlay or focal profile, not as a replacement for the whole committee.

### Level 5 — advanced registry usage

```python
from symposia.profiles import Profile, ProfileSet, register_profile_set

my_set = ProfileSet(...)
register_profile_set(my_set)
```

When constructing a `ProfileSet`, treat `juror_count` as derived from
`len(profiles)`. If you need custom prompt framing, set `domain_guidance` on
the profile set so juror prompts inherit it directly.

This should be available, but not featured in the README quickstart.

## Result usage

```python
result.verdict
result.agreement
result.caveats
result.trace
```

Current validate(...) returns InitialReviewResult and keeps the execution-level
fields available alongside the thin public surface:

```python
result.aggregated_by_subclaim
result.completion
result.core_trace
result.adjudication_trace
```

### Trace usage

```python
result.trace
```

## Recommended constructor shape

```python
sp = Symposia(
    profile_set=None,
    providers=[...],
    trace=False,
)
```

## Recommended high-level methods

### `validate(...)`
The main method.

### `with_profile_set(...)`
Return a configured or derived instance.

### `with_profile(...)`
Apply a narrow profile override to a derived instance.

### `result.trace`
Access structured trace data on the returned result object.

## Methods to avoid on the top-level surface

Avoid top-level public methods such as:
- `spawn_jurors`
- `run_round_two`
- `score_support_matrix`
- `compile_subclaim_graph`
- `build_default_profile_set`

Those belong inside the engine or in advanced modules.

## Advanced API layer

Expose advanced power under submodules such as:
- `symposia.profiles`
- `symposia.profile_sets`
- `symposia.calibration`
- `symposia.policies`
- `symposia.tracing`
- `symposia.experimental`

This preserves simplicity while giving serious users control.

## Result contract

The output object should be rich enough for institutions but still compact.

Required fields:
- `verdict`
- `certainty`
- `issuance`
- `risk`
- `agreement`
- `summary`
- `caveats`
- `rounds_used`
- `profile_set_used`

Optional fields:
- `subclaims`
- `dissent`
- `trace_id`
- `sources`

## Profile doctrine

A single profile should control a juror's posture, not the entire committee.

A profile set should control:
- juror composition
- thresholds
- max rounds
- domain policy
- escalation rules
- evidence rules
- trace richness

## Recommended defaults

### Default behaviour
- choose profile set from the domain
- keep trace off
- keep thresholds moderate

### Strict behaviour
- stronger support thresholds
- more conservative issuance
- stronger caveat surfacing

### High-stakes behaviour
- stricter escalation
- stronger trace requirements
- tighter domain controls

## API design principle

The library surface should fit in the README without looking crowded.
