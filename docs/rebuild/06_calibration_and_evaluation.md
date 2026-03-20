# Calibration and Evaluation

## Purpose

This document defines how Symposia earns credibility. The complementary document `15_testing_strategy.md` defines how that credibility is protected during build and release.

The system should not claim reputability merely because many jurors agree. It should earn reputability by showing that:
- its jurors track known truth
- its aggregation improves outcomes
- its certainty and caveat signals are meaningful

## Calibration doctrine

Consensus is not the ground truth.

Juror influence should be based primarily on:
- performance on seed sets with known answers
- domain-specific reliability
- stability across task families

## Calibration registry

Maintain a versioned registry keyed by:
- provider
- model
- model version
- domain
- task family
- prompt contract version

Each record should include:
- calibration score
- discrimination or informativeness score
- coverage
- last updated timestamp
- sample size

## Seed sets

A seed set is a collection of adjudication tasks with known or strongly agreed answers.

Recommended categories:
- medical guidance tasks
- legal procedural fact tasks
- finance factual and interpretive tasks
- general factual validation tasks

## Weight computation

A simple initial formula is enough:

`effective_weight = base_weight * calibration_weight * domain_fit_weight`

Later additions:
- retrieval quality factor
- freshness factor
- abstention penalty or reward
- diversity factor

## Evaluation levels

### 1. Juror level
How good is each juror?

Metrics:
- accuracy
- calibration
- false positive rate
- false negative rate
- abstention quality

### 2. Subclaim level
How good is the compiled decision per subclaim?

Metrics:
- precision
- recall
- contradiction detection
- insufficiency accuracy

### 3. System level
How good is the overall committee?

Metrics:
- accuracy against benchmark labels
- improvement over strongest single model
- escalation rate
- trace completeness
- cost per validated result

## Core benchmarks

Every release should report:
- baseline single-model performance
- unweighted committee performance
- calibrated committee performance
- strict-profile performance
- degraded-provider performance

## Success metrics

Recommended initial metrics:
- reduction in false validations
- improvement in benchmark accuracy over best single model
- precision of `validated` verdicts
- calibration of certainty labels
- percentage of high-risk outputs correctly marked with caveats or review requirements

## Calibration update cadence

Do not update weights on every live call by default.

Recommended:
- offline periodic calibration updates
- versioned registry snapshots
- controlled promotion to production

## What to avoid

Avoid:
- giving permanent weight increases for mere agreement with consensus
- hiding calibration criteria
- mixing benchmark-derived and ad hoc weights without versioning
- changing production weights without an auditable snapshot

## Evaluation artefacts to keep

- benchmark definitions
- seed set provenance
- model version registry
- scorecards per release
- error analysis notes
- domain comparison reports

## Launch bar

Before making serious institutional claims, Symposia should be able to show:
- calibrated committee > unweighted committee
- calibrated committee > strongest single baseline on at least one domain benchmark
- certainty labels correspond to real accuracy bands
- high-risk profiles reduce unsafe issuance errors

## Motto

Calibration is how Symposia earns the right to sound confident.
