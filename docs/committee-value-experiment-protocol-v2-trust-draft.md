# Committee Value Experiment Protocol (v2 Trust Draft)

Status: draft
Date: 2026-03-21
Scope: trust-value measurement only

## Purpose

This draft is intentionally separate from runtime behavior. It defines trust-oriented evaluation metrics for committee judgement without introducing any runtime adjudication changes.

Runtime freeze rule:

- no runtime schema changes
- no runtime routing policy changes
- no runtime guardrail changes

## Trust Objective

Primary question:

- Does committee judgement increase trust-relevant signal quality compared with single-juror execution?

## Proposed Trust Metrics

1. Agreement Level
- committee internal agreement distribution
- stability of agreement across slices

2. Dissent Visibility
- dissent incidence rate
- explicit minority-vs-majority trace capture
- dissent persistence across repeated runs

3. Independence / Correlation
- pairwise same-error rate
- disagreement diversity index
- unique-correct contribution per juror

4. Trace Completeness
- required trace fields present per case
- missing-field rate
- adjudication path completeness score

5. Optional User Trust Signal
- blinded preference between single vs committee outputs
- confidence-in-reliance rating

## Evaluation Design

- Keep existing dataset manifest lock discipline.
- Keep existing development/holdout split discipline.
- Add trust metrics as parallel outputs, not replacements for existing efficiency metrics.

## Output Artifacts (Draft)

- trust_summary.json
- trust_per_case.json
- trust_dissent.json
- trust_correlation.json
- trust_trace_completeness.json
- trust_decision.md

## Governance

- This is a draft protocol and does not alter current runtime.
- Any adoption requires explicit review and a versioned protocol release.

---

## First bounded run results (2026-03-21)

The first runs under this framework (using the trust value dataset v2 and the experimental ladder Step 2 vs Step 3 decomposition) produced the following:

**Plurality effect (Step 1 vs Step 2):** not yet isolated in a clean run. Same-family committee plurality was used as the baseline for diversity evaluation.

**Diversity effect (Step 2 vs Step 3):** confirmed as claim-structure-dependent.

- Strongest positive signal: `forecast_style_claim` — consistent target-match and weighted-score lift in both development and holdout splits.
- Null result: `low_risk_clear_factual` — no measurable diversity effect.
- Harmful result: `underspecified_legal_policy` — critical dissent spikes with no quality gain.

**What the dissent signal means on forecast-style claims:**

Agreement falls ~0.267 on both splits when moving from same-family to mixed-family. This is expected: models from different families disagree more on inferentially uncertain questions. The disagreement is productive — quality metrics improve despite lower consensus. This supports the independence signal dimension of this protocol.

**Implications for this draft:**

- Dissent visibility metrics (section 2) are confirmed as meaningful on forecast-style claims. Higher dissent correlates with higher quality on those cases, not lower.
- Independence signal (section 3) is the likely mechanism: cross-family models make different errors, and the committee resolves them better than any single-family combination.
- Agreement metrics should always be reported alongside quality metrics, not treated as a quality proxy in isolation.

These findings should inform the preregistration requirements for any full v2 protocol run. Specifically: all metric gates must be defined per slice, not globally.
