# Profile Selection Strategy

## Purpose

This document proposes the next layer above fixed profile sets:
**selection before execution**.

It exists to answer one design discomfort:

> Why should the caller need to know the right profile set at call time?

For v1, that assumption is acceptable.
For a best-in-class system, it should not be the end state.

This document does **not** change the core spec yet.
It is a strategy and build-direction document.

## The problem

The current shape is:

```text
request -> resolve domain default or caller-selected profile set -> run adjudication
```

That is simple and good for first release.

But it assumes one of two things:
- the caller already knows the right profile set
- the domain default is always good enough

That is serviceable, but not ideal.

The stronger long-term shape is:

```text
request -> infer best profile set -> run adjudication
```

And later, if justified by evidence:

```text
request -> compose the best cohort dynamically -> run adjudication
```

## What must remain invariant

The selector layer should not turn Symposia into a vague adaptive blob.

The following should remain stable:
- the adjudication core
- the verdict schema
- the trace model
- the stop and escalation contract
- the profile contract
- the audit story

In other words:

```text
selection may change the cohort
selection must not change the meaning of the verdict
```

That is the guardrail.

## Build-up model

### Stage 1 — Fixed caller-visible profile sets

This is the current recommended model.

The library remains simple:

```python
result = sp.validate(content="...", domain="medical")
```

or, when reproducibility matters:

```python
result = sp.validate(content="...", domain="medical", profile_set="medical_strict_v1")
```

Why this stage matters:
- deterministic
- easy to test
- easy to explain
- good for benchmarks
- keeps the public surface small

This stage earns the right to go further.

### Stage 2 — Selector over a fixed registry

The system introduces a **selector** that chooses from a known registry of profile sets.

Shape:

```text
request -> one LLM routing call -> choose best named profile set -> run
```

For the recommended first implementation, the selector is **one constrained LLM call**.
No pretraining is required.
No separate routing model is required.
The existing LLM stack is reused as a bounded classifier.

The selector may consider:
- domain
- risk level
- claim type
- jurisdiction sensitivity
- instruction vs explanation
- evidence density
- ambiguity level

But the output remains one of a fixed set of known profile sets, such as:
- `general_default_v1`
- `medical_strict_v1`
- `legal_strict_v1`
- `finance_strict_v1`
- future narrower sets

The selector must be tightly bounded:
- it may **select**, not invent
- it must return strict structured output
- it must choose only from the fixed registry
- it must log its routing reason and confidence
- it must fall back to a safe default when uncertain

Why this is the right next step:
- simpler for users
- fast to build
- still bounded and auditable
- reproducible at the named-set level
- measurable against fixed baselines

This is the strongest medium-term design.

### Stage 3 — Constrained profile composition

The selector may begin to build a cohort from a fixed registry of profiles rather than only picking a whole set.

Shape:

```text
request -> infer task needs -> assemble constrained cohort -> run
```

Example:
- 2 balanced reviewers
- 2 sceptical verifiers
- 1 literal parser
- 1 risk sentinel
- 1 evidence maximalist

This is more adaptive, but riskier.

Requirements before attempting it:
- strong trace metadata
- clear composition rules
- reproducible cohort fingerprints
- benchmark evidence that it beats fixed selection

This stage should still use only **known, versioned profiles**.

### Stage 4 — Real-time profile synthesis

This is the most ambitious stage:

```text
request -> generate task-specific juror profiles -> run
```

This may become powerful.
It may also become arbitrary, brittle, and difficult to govern.

It should be attempted only if all of the following are true:
- fixed selection has been proven
- constrained composition has been proven
- synthesis is measurable and reproducible enough
- generated profiles can be inspected and versioned post hoc
- there is clear performance gain on real benchmark tasks

Strong recommendation:
**do not build this early**.

## Recommended doctrine

### The library surface should hide selection by default

The best default user experience is still:

```python
result = sp.validate(content="...", domain="medical")
```

The library should quietly do one of two things:
- resolve a domain default
- or, in a later phase, run a selector and choose the best profile set automatically

The user should not need to think about committee composition unless they want to.

### The selector should remain a router

The selector should not become a hidden profile author.
Its job is to route a request to the best existing named target.

In other words:

```text
infer != generate
```

That distinction keeps the system governable.

### Named profile sets should remain first-class

Even after a selector exists, named profile sets remain essential.

Why:
- reproducibility
- governance
- benchmarking
- regulatory comfort
- debugging

So the selector should choose a **named, inspectable target** whenever possible.

### Generated profiles should stay advanced

If real-time synthesis is ever added, it should live behind an advanced path.
It should not become the ordinary quickstart story.

That preserves trust.

## Best-in-class usage ladder

### Level 1 — frictionless default

```python
sp.validate(content="...", domain="finance")
```

The user knows nothing about profiles.
That is correct.

### Level 2 — explicit named set

```python
sp.validate(content="...", domain="finance", profile_set="finance_strict_v1")
```

This is the serious reproducible path.

### Level 3 — explain selected set

```python
sp.validate(
    content="...",
    domain="finance",
    explain_profile_selection=True,
)
```

The result includes which named set was chosen and why.

### Level 4 — advanced custom control

```python
sp.validate(
    content="...",
    domain="finance",
    profile_set=my_custom_profile_set,
)
```

This is for expert users only.

### Level 5 — experimental synthesis

```python
sp.validate(
    content="...",
    domain="finance",
    profile_strategy="experimental_dynamic",
)
```

This should remain clearly marked as experimental until proven.

## What the selector should optimise for

Not novelty.
Not drama.

It should optimise for:
- epistemic fit to the task
- risk-appropriate scrutiny
- bounded diversity of reasoning posture
- reproducibility
- calibration performance
- auditability

A selector is good if it chooses a cohort that improves outcomes while remaining legible.

## Risks

### 1. Hidden arbitrariness
The system may appear clever while quietly making hard-to-defend choices.

Mitigation:
- log the chosen set
- log why it was chosen
- keep selection over a fixed registry first

### 2. Evaluation drift
Dynamic selection may make benchmarks messy.

Mitigation:
- compare against fixed named baselines
- record selector version
- record selected cohort fingerprint

### 3. Governance discomfort
Institutions are more comfortable with named, versioned committees than invisible runtime invention.

Mitigation:
- keep named sets first-class
- make generated profiles inspectable
- require trace evidence for dynamic selection

### 4. Surface complexity creep
Selection features can pollute the public API.

Mitigation:
- keep the quickstart path minimal
- push advanced control behind explicit parameters

## Strong recommendation on build order

Build in this order:

### Phase A
Caller-visible fixed profile sets.

### Phase B
Automatic selection from a fixed registry of named sets.

### Phase C
Constrained composition from a fixed profile registry.

### Phase D
Real-time profile synthesis only if clearly justified by data.

This order is not just safer.
It is more prestigious.
It shows discipline.

## What success looks like

A best-in-class Symposia should eventually feel like this:
- simple for ordinary users
- reproducible for serious users
- inspectable for institutions
- adaptive where it helps
- conservative where trust matters

The winning shape is therefore:

```text
simple surface -> explicit named sets underneath -> selector over registry -> carefully bounded dynamic composition later
```

## Recommendation summary

- Yes, the current assumption is acceptable for v1.
- No, it should not be the final abstraction.
- The right next move is **selection over fixed named profile sets**.
- Dynamic generation should come only after fixed selection is benchmarked and governed.
- Keep the adjudication core invariant while making cohort choice more intelligent.

That is the disciplined way forward.
