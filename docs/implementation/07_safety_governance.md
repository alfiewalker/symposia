# Safety and Governance

## Purpose

This document defines how Symposia becomes institution-grade.

A credible system for medicine, law, and finance needs more than strong model orchestration. It needs:
- policy boundaries
- domain controls
- auditability
- clear rules for review and refusal

## Governance principles

### 1. Domain-aware caution
The same verdict threshold should not apply everywhere.

### 2. Issuance is not the same as support
Something can be supported yet still require review or caveats.

### 3. Trace must exist before trust
In high-stakes domains, untraceable outputs should not be treated as serious outputs.

### 4. Degrade conservatively
When evidence or providers fail, the system should degrade toward caution, not toward false confidence.

## Domain governance

### Medical
Requirements:
- strong caveat surfacing
- emergency and dosing sensitivity
- localisation support
- stricter issuance rules

### Legal
Requirements:
- jurisdiction sensitivity
- procedural caution
- recommendation restraint
- strong trace for authorities and sources

### Finance
Requirements:
- distinction between factual validation and recommendation
- compliance-aware issuance
- conflict and recency sensitivity

## Human review triggers

Require human review when:
- issuance is `requires_expert_review`
- risk is `high` and certainty is below `high`
- critical dissent survives final aggregation
- legal or medical jurisdiction handling is unresolved
- evidence provenance is weak

## Refusal and containment

Symposia should support containment statuses such as:
- cannot_validate
- unsafe_to_issue
- requires_domain_review

These are not failures. They are serious outcomes.

## Audit requirements

A high-stakes run should be able to show:
- what was asked
- what subclaims were evaluated
- what evidence was considered
- how jurors voted
- what caveats were raised
- why escalation did or did not happen
- why the final verdict was compiled

## Policy versioning

Every run should be able to identify:
- profile version
- domain policy version
- calibration snapshot
- prompt contract version
- provider versions where available

## Release governance

Before releasing a new strict or high-stakes profile:
- run benchmarks
- compare to previous profile version
- document regressions
- record approval or promotion decision

## Organisational posture

Symposia should be presented as:
- a decision-support and validation engine
- not an unbounded autonomous authority

## Governance artefacts to maintain

- domain policy files
- profile registry
- calibration snapshots
- release scorecards
- benchmark reports
- incident and regression log
- open-risk register

## Committee value governance — current evidence boundary

The experimental ladder has produced the first family-scoped evidence on when mixed-family committees add trust-relevant value (as of 2026-03-21).

Governed position:

- **forecast-style claims**: mixed-family committee shows repeatable lift on target match and weighted score. This is the affirmative proof case.
- **low-risk clear factual claims**: no measurable committee diversity effect. Same-family and mixed-family committees converge to the same output.
- **underspecified legal/policy claims**: mixed-family committees increase critical dissent without improving verdict quality. This is a harm case and must not be presented as a diversity benefit.

Product and communications constraint:
- Do not claim that mixed-family committees are generally better than same-family committees.
- Do not claim that committee disagreement signals greater trust.
- Diversity benefit claims must be scoped explicitly to forecast-style or structurally similar claim types.

This boundary should be Updated when new ladder rungs are run or the dataset scope is extended.

## Credibility principle

Institutions trust systems that can say:
- this is supported
- this is not supported
- this is uncertain
- this must be reviewed

without pretending those are the same thing.
