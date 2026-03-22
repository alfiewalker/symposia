# Profile Sets

## Purpose

This document defines how Symposia should represent, use, and expose juror profiles and profile sets.

It is structured as a build-up:
1. why profiles exist
2. what a single profile is
3. what a profile set is
4. what the defaults should be
5. how the library should expose them
6. how advanced users may extend them without cluttering the main API

## 1. Why profiles exist

Symposia uses many jurors, but the committee should not be a bag of identical copies.

Jurors should vary in **scrutiny posture**, not in truth standard.

That means variation in:
- scepticism
- literalness
- safety emphasis
- evidence strictness
- operational pragmatism

It does **not** mean variation in:
- verdict schema
- public truth standard
- domain policy floor

A profile therefore exists to make juror variation:
- explicit
- testable
- calibrated
- auditable

## 2. What a profile is

A **Profile** is a named, versioned juror behaviour contract.

A profile should define:
- identity
- purpose
- behavioural stance
- evidence posture
- safety posture
- known failure modes
- compatibility constraints

### Example shape

```yaml
id: sceptical_verifier_v1
label: Sceptical Verifier
purpose: Challenge overclaiming and weak support
behaviour:
  stance: sceptical
  literalism: medium
  evidence_demand: high
  safety_bias: moderate
failure_modes:
  - may escalate borderline claims too often
compatible_domains:
  - general
  - medical
  - legal
  - finance
```

## 3. What a profile set is

A **ProfileSet** is the full committee composition and policy bundle for a run.

A profile set should define:
- set identity
- domain
- purpose
- juror count
- juror composition
- stop thresholds
- escalation policy
- issuance policy
- trace policy
- calibration policy

### Core rule

The library should choose a **profile set**, not a loose bag of profiles.

That is what keeps the public API simple.

### Example shape

```yaml
id: medical_strict_v1
domain: medical
purpose: High-risk medical validation
profiles:
  - balanced_reviewer_v1
  - sceptical_verifier_v1
  - evidence_maximalist_v1
  - literal_parser_v1
  - risk_sentinel_v1
thresholds:
  support: 0.80
  confidence: 0.82
max_rounds: 2
issuance_policy: conservative
trace_policy: standard
calibration_snapshot: medical_2026_q1
```

`juror_count` is derived from `len(profiles)` rather than stored in the YAML.

## 4. Build-up from simple to advanced

### Stage A — one hidden default set

For first-time users, Symposia should feel like this:

```python
result = sp.validate(content="...", domain="medical")
```

The library silently resolves:
- domain = `medical`
- profile set = `medical_default_v1` or `medical_strict_v1`

This is the right default.

### Stage B — named profile-set selection

A serious user may want reproducibility.

```python
result = sp.validate(
    content="...",
    domain="medical",
    profile_set="medical_strict_v1",
)
```

This is the most important advanced feature.

### Stage C — profile overlay

A more advanced user may want to emphasise one juror posture.

```python
result = sp.validate(
    content="...",
    domain="medical",
    profile_set="medical_strict_v1",
    profile="risk_sentinel_v1",
)
```

This should behave as an overlay or biasing instruction, not as a replacement of the committee.

### Stage D — custom registry authoring

Only advanced users should register custom profile sets.

```python
from symposia.profile_sets import register_profile_set

register_profile_set(my_profile_set)
```

This should live outside the main quickstart path.

## 5. Default profiles for v1

A best-in-class v1 should ship with a small, serious set.

### `balanced_reviewer_v1`
Default neutral juror.

### `sceptical_verifier_v1`
Looks for overclaiming and missing support.

### `evidence_maximalist_v1`
Demands stronger corroboration and source quality.

### `literal_parser_v1`
Focuses on exact wording, scope, and claim decomposition.

### `risk_sentinel_v1`
Focuses on harm, caveats, and issuance safety.

### `domain_pragmatist_v1`
Focuses on whether the content is usable in practice.

## 6. Default profile sets for v1

### `general_default_v1`
General factual validation.

Suggested composition:
- 5 jurors
- balanced, sceptical, literal, evidence, pragmatist

### `medical_strict_v1`
High-risk medical validation.

Suggested composition:
- 9 jurors
- heavier weighting of evidence and risk profiles
- conservative issuance policy

### `legal_strict_v1`
Jurisdiction-sensitive legal validation.

Suggested composition:
- 7 jurors
- stronger literal and jurisdiction-sensitive posture
- strong caveat surfacing

### `finance_strict_v1`
Finance research and recommendation scrutiny.

Suggested composition:
- 7 jurors
- stronger contradiction and issuance controls
- recommendation caution enabled

## 7. How the library should expose profiles

### Default doctrine
Profiles should be **present but quiet**.

The README should showcase:
- default usage
- named profile-set selection

It should not showcase:
- hand-assembling juror panels
- per-juror personality tuning
- raw prompt hacking

### Public exposure ladder

#### First-class in docs
Yes.

#### First-class in engine
Yes.

#### First-class in README quickstart
Only profile-set selection.

#### First-class in advanced API
Yes.

## 8. Best-in-class simplicity rule

The caller should usually choose **zero or one thing**:
- nothing, and accept the default domain set
- one named profile set, for reproducibility

Everything beyond that should be optional.

That means the mental model is:

```text
basic use      -> choose domain
serious use    -> choose profile set
expert use     -> author profile sets
```

## 9. Recommended Python surface

### Simplest use

```python
sp = Symposia()
result = sp.validate(content="...", domain="general")
```

### Best serious use

```python
sp = Symposia(profile_set="medical_strict_v1")
result = sp.validate(content="...", domain="medical")
```

### Advanced use

```python
from symposia.profiles import Profile
from symposia.profile_sets import ProfileSet, register_profile_set
```

## 10. Recommended file layout

```text
src/symposia/
  profiles/
    defaults.py
    medical.py
    legal.py
    finance.py
  profile_sets/
    defaults.py
    medical.py
    legal.py
    finance.py
```

## 11. Governance rule

Every shipped profile and profile set should be:
- versioned
- documented
- benchmarked
- attributable to a release

No silent behavioural drift.

## 12. Build guidance

Implement profiles in this order:
1. profile object
2. profile-set object
3. default registry
4. profile-set resolution
5. domain defaults
6. custom registration
7. benchmark and calibration reporting by profile set

## Principle

Profiles should make the engine richer.
Profile sets should keep the library simpler.
