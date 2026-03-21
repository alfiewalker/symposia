# Methodology v2

## Overview

Symposia v2 is built on four pillars:

1. **Condorcet-style independent first-pass voting**
2. **Calibration-weighted juror influence**
3. **Evidence grading**
4. **Audit governance**

This is the methodology that gives both elegance and clout.

## Theoretical posture

Sympoia's validation layer draws on four framework families. Each one provides a distinct piece of the adjudication design.

### 1. Condorcet / jury theorems → plurality logic

The Condorcet jury theorem shows that a majority of independent judges, each more likely than not to be correct, tends toward the right answer as the committee grows. The first-pass review retains the spirit of this:
- many jurors
- independent review
- binary judgements per subclaim
- aggregation into a committee result

**Where pure Condorcet stops.** The theorem does not tell us how to decompose compound content, weight jurors credibly, handle uncertainty escalation, or produce institution-grade outputs. Symposia keeps Condorcet in the kernel and layers practical adjudication above it.

### 2. Cooke's Classical Model → expert weighting / calibration logic

Cooke's Classical Model (Structured Expert Elicitation) establishes that expert weights should be derived from calibration performance on seed variables with known answers — not from seniority, prestige, or agreement with the majority. This grounds Symposia's juror weighting design:
- jurors are weighted by calibration against known-answer sets
- consensus alignment is stored as metadata but not used as the primary truth proxy
- a consistently well-calibrated juror earns more influence over time

### 3. GRADE / RAND-UCLA evidence judgement → evidence and judgement logic

GRADE (Grading of Recommendations, Assessment, Development, and Evaluation) and the RAND-UCLA Appropriateness Method both formalise the idea that evidence quality and recommendation strength must be treated as distinct dimensions. Symposia applies this by:
- distinguishing verdict (what the evidence supports) from certainty (how strongly)
- distinguishing certainty from issuance safety (whether it is appropriate to act on)
- flagging when evidence is insufficient rather than forcing a binary verdict

### 4. NIST-style governance → governance and trustworthiness logic

NIST AI Risk Management and related frameworks establish that trustworthy AI systems need auditability, boundary clarity, and risk-aware operation. Symposia applies this by:
- making dissent a first-class output, not a side effect to suppress
- producing traceable adjudication: subclaims, juror votes, rationale, caveats, dissent
- drawing explicit capability boundaries (what the system can and cannot claim)
- separating governance policy from runtime behaviour

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
