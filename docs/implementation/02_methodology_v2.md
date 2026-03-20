# Methodology v2

## Overview

Symposia v2 is built on four pillars:

1. **Condorcet-style independent first-pass voting**
2. **Calibration-weighted juror influence**
3. **Evidence grading**
4. **Audit governance**

This is the methodology that gives both elegance and clout.

## Theoretical posture

### Condorcet spirit
The first pass should retain the spirit of the jury theorem:
- many jurors
- independent review
- binary judgments
- aggregation into a committee result

### Where pure Condorcet stops
Pure Condorcet does not tell us:
- how to decompose compound content
- how to handle caveats and safety
- how to weight jurors credibly
- how to escalate uncertainty
- how to produce institution-grade outputs

So Symposia keeps the theorem in the kernel, then layers a practical adjudication system above it.

## Core methodological move

Do not ask jurors to vote directly on:
- validated
- rejected
- insufficient
- contested

Instead, for each subclaim, ask hidden binary tests.

## Internal binary tests

For each subclaim `c`, each juror `j` returns:

- `supported(j, c)` -> is the claim supported by reliable evidence?
- `contradicted(j, c)` -> is there material evidence against it?
- `sufficient(j, c)` -> is there enough evidence to decide?
- `issuable(j, c)` -> is it safe to issue as advice or guidance without further caveat?

Optional domain-specific tests may be added, but these four form the common core.

## Verdict compilation

The public verdict is then compiled from the internal tests.

Example mapping:

- **validated**
  - support passes
  - contradiction does not pass
  - sufficiency passes

- **rejected**
  - contradiction passes strongly

- **insufficient**
  - sufficiency fails

- **contested**
  - mixed support and contradiction, or unresolved dissent remains high

## Certainty

Certainty is distinct from verdict.

Suggested levels:
- high
- moderate
- low
- very_low

Certainty should reflect:
- source quality
- agreement quality
- calibration quality
- evidence coverage
- dissent severity

## Issuance

Issuance is also separate.

Suggested levels:
- safe_to_issue
- issue_with_caveats
- requires_expert_review
- unsafe_to_issue

This is crucial in medicine, law, and finance.

A statement may be supported yet still require caveats or review.

## Escalation model

### Round 0
Independent adjudication only.

### Trigger escalation if any of these hold:
- support is below threshold
- contradiction is materially present
- sufficiency is not met
- certainty is too low
- a critical objection is raised
- a high-risk domain rule requires review

### Round 1
One structured challenge round:
- strongest pro argument
- strongest con argument
- targeted evidence correction
- one revision pass

By default, stop after one escalation round.

## Juror weighting

Jurors should not be weighted by consensus alignment alone.

Weights should be driven by:
- calibration against known-answer sets
- domain fit
- retrieval quality
- freshness or version suitability
- optional diversity contribution

Consensus alignment may be stored as metadata, but not used as the primary truth proxy.

## Traceability

Each adjudication should be able to produce:
- subclaims
- sources
- juror votes
- confidence and rationale
- caveats
- dissent
- final compiled verdict

## Domain posture

The methodology is domain-neutral at the kernel level, but domain-aware at the policy layer.

That means:
- same kernel
- different domain profiles
- different escalation and issuance rules

## One-line doctrine

Symposia should behave like a calibrated committee, not a chorus.
