# 22_experimental_ladder_and_testing_revamp.md

# Experimental Ladder and Testing Revamp

## Purpose

This document formalises the experimental ladder for Symposia and explains how the testing and governance story should be rebuilt around it.

The goal is to stop treating every experiment as a generic “committee vs single” comparison and instead test the thesis in the correct order.

Important runtime boundary:

- product default = holistic single-claim review
- decomposition = experimental evaluation path only

This separation is deliberate. A distorted decomposition layer can reduce truthfulness and blur experimental interpretation.

---

## Core thesis

Symposia is testing whether committee-based LLM judgement creates more trust than lone judgement.

This should be decomposed into two smaller questions:

1. **Plurality effect**
   - Does a committee of jurors create more trust-relevant value than a single juror of similar capability?

2. **Diversity effect**
   - Does cross-family model diversity add trust-relevant value beyond same-family committee plurality?

A third question follows after those:

3. **Quality–count frontier**
   - If committee value exists, how does juror capability trade against juror count?

This is the formal experimental ladder.

---

## The ladder

### Ladder Step 1 — Single weak baseline

**Purpose:** establish whether a weaker but still viable single judge is above the floor for the relevant task family.

Example:
- single `gpt-5.4-nano`

Question answered:

- Is the weak juror competent enough to be a meaningful baseline?
- Does it satisfy the modern Condorcet-style requirement of being better than chance on the relevant slice?

Expected use:
- calibration floor
- viability floor
- cost/latency floor

---

### Ladder Step 2 — Same-family weak committee

**Purpose:** test plurality effect without adding provider/model-family diversity.

Example:
- committee of `gpt-5.4-nano` jurors
- same model family
- profile variation only

Question answered:

- Does plurality itself improve trust-relevant judgement over a lone weak juror?

Interpretation:
- Step 2 vs Step 1 isolates **committee structure**.

---

### Ladder Step 3 — Cross-family weak committee

**Purpose:** test whether cross-family diversity adds trust-relevant value beyond same-family plurality.

Example:
- `gpt-5.4-nano`
- smallest viable Claude
- smallest viable Gemini
- fixed profile/rubric/protocol

Question answered:

- Does model-family diversity add trust-relevant signal beyond same-family committee plurality?

Interpretation:
- Step 3 vs Step 2 isolates **diversity effect**.

**Status (2026-03-21): first run complete.**

Results: diversity effect is **claim-structure-dependent**, not universal.

- `forecast_style_claim`: positive lift confirmed in dev and holdout (ΔTM dev +0.20 / hold +0.40; ΔWS dev +0.256 / hold +0.12)
- `low_risk_clear_factual`: null result — same-family and mixed-family committees converge identically
- `underspecified_legal_policy`: harmful — mixed committee increases critical dissent without quality gain

Adjacent family replication confirmed the boundary. The positive signal does not generalise beyond forecast-style and structurally similar inferential claim families.

These ladder results should therefore be read as evidence about committee behavior under the experimental decomposition path, not as justification for making decomposition the default runtime policy.

---

### Ladder Step 4 — Single stronger baseline

**Purpose:** test whether a stronger single judge closes the gap.

Example:
- single `gpt-5.4-mini`

Question answered:

- Is a stronger single judge enough to erase the committee advantage observed at weaker capability levels?

Interpretation:
- Step 4 vs Steps 2–3 tests whether committee lift is only a weak-model effect.

---

### Ladder Step 5 — Smaller stronger committee

**Purpose:** test the juror-quality versus juror-count trade-off.

Example:
- 2–3 stronger jurors instead of a larger weak committee

Question answered:

- Can higher juror capability reduce the number of jurors needed while preserving trust-relevant value?

Interpretation:
- This tests the practical frontier aligned with a modernised Condorcet intuition.

---

## What each step proves

### Step 1 vs Step 2
**Plurality effect**

If Step 2 beats Step 1 on trust-relevant metrics, committee structure is doing useful work.

### Step 2 vs Step 3
**Diversity effect**

If Step 3 beats Step 2, cross-family diversity adds value beyond mere committee plurality.

**First run result (2026-03-21):** Step 3 beats Step 2 **only on forecast-style claims**. On clear factual claims it is tied. On underspecified policy claims Step 2 outperforms Step 3. The global signal is weak; the family-scoped signal is strong and bounded.

### Step 3 vs Step 4
**Strong single challenge**

If Step 4 matches or beats Step 3, the committee advantage may be a weak-model phenomenon only.

### Step 4 vs Step 5
**Quality–count frontier**

If Step 5 preserves trust-relevant value at lower committee size, there is an efficient quality/count trade.

---

## Why this is better than the previous testing shape

The previous testing shape blurred several questions together:

- committee vs single
- same-family vs mixed-family
- cheap vs strong models
- trust vs efficiency
- runtime plumbing vs thesis proof

The ladder fixes that by turning one vague comparison into a sequence of controlled comparisons.

It simplifies interpretation because each rung has one main explanatory job.

---

## What “trust-relevant value” means in this ladder

The ladder should not be judged mainly by binary correctness.

It should be judged by a trust-relevant rubric.

At minimum:

- agreement quality
- dissent usefulness
- caveat quality
- calibration
- auditability
- safety framing where relevant
- rubric target-match for bounded-ambiguity cases

Efficiency still matters, but it is a secondary constraint, not the central thesis target.

---

## Required controls

Every ladder experiment should keep the following fixed unless the step explicitly changes them:

- dataset
- rubric
- protocol version
- escalation policy
- output schema
- artifact set

If the step is testing model diversity, do not also change rubric or escalation.

If the step is testing juror count, do not also change providers.

## Interpretation boundaries

### Mechanism evidence versus product readiness

- Early ladder rungs are designed to establish mechanism direction under controlled conditions.
- Step 2 > Step 1 indicates plurality signal at low capability.
- Step 3 > Step 2 indicates cross-family signal beyond same-family plurality.
- These outcomes are thesis evidence and should not be presented as default-deployment proof.

### Cross-family inference discipline

- Step 2 and Step 3 should be matched on tier (`small_capable`) and committee size.
- Interpretation is bounded to the tested route/model set.
- Robustness replication should rotate provider-slot assignments before broad generalisation.

### Strong single as a planned comparator

- Step 4 explicitly tests whether stronger single-judge capability closes the committee gap.
- If strong single matches or exceeds committee outcomes, claim scope should narrow accordingly.

### Governance claim boundary

- Ladder outcomes are evidence for the committee-trust thesis.
- Product-default support remains blocked unless Tier C human-labeled proof gates are satisfied.

## Least-capable working model policy

For Step 3 mixed-family runs, pick the least-capable currently working model per provider family.

Selection rule:

1. Candidate model is available for the current key and API version.
2. Candidate passes preflight prompt/parse checks under current output schema.
3. Candidate is in small_capable tier for the route set.
4. If multiple candidates pass, choose the lowest expected cost/latency.

Current v1 pinned choices:

- Anthropic: claude-3-haiku-20240307
- Google: gemini-2.5-flash-lite

Operational rule:

- Do not silently swap these inside a frozen experiment run.
- If provider catalogs change, create a new route revision and document the change.

---

## Dataset implications

The ladder requires a dataset that is:

- bounded in ambiguity
- rich in caveat-sensitive judgement
- not clone-padded
- slice-balanced
- scored by deterministic rubric

Good case families include:

- mixed-truth claims
- underspecified claims
- high-stakes advice
- forecast-like questions
- ambiguous but bounded reliance decisions

Bad case families include:

- trivial factual lookups
- clone-padded paraphrase grids
- cases with weak or mushy labels
- questions whose scoring depends on taste rather than rubric

---

## Testing revamp

The testing story should now be rebuilt around the ladder.

### 1. Split tests into two layers

#### A. System integrity tests
These remain as they are:
- contracts
- loaders
- trace
- parser
- routing
- protocol validation
- artifact writing

These prove that Symposia runs correctly.

#### B. Thesis tests
These are ladder-specific:
- Step 1 vs Step 2
- Step 2 vs Step 3
- Step 3 vs Step 4
- Step 4 vs Step 5

These prove or weaken the committee-trust thesis.

---

### 2. Replace generic “committee vs single” tests with rung comparisons

Testing should no longer ask only:
- does committee beat single?

Instead it should ask:
- does same-family plurality beat single?
- does cross-family diversity beat same-family plurality?
- does strong single erase weak-committee advantage?
- does smaller stronger committee preserve trust lift?

That is a much cleaner interpretation framework.

---

### 3. Introduce ladder-specific artifact outputs

Each ladder run should emit:

- `ladder_summary.json`
- `ladder_summary.md`
- `rung_comparison.json`
- `trust_metrics.json`
- `efficiency_metrics.json`
- `resolved_protocol.json`

Optional:
- `hypothesis_decision.md`

These should complement, not replace, the current protocol artifacts.

---

### 4. Keep runtime and governance separate

The ladder is an **evaluation and evidence** structure.

It should not leak into:

- runtime adjudication logic
- normal `validate(...)`
- product defaults
- route loading rules

In other words:

- runtime stays stable
- experiments move around it

---

## Governance impact

This ladder should become the main story for:

- trust-thesis evaluation
- bounded product claims
- evidence accumulation
- future protocol revisions

It simplifies governance because each step has a defined claim boundary.

### Example claim boundaries

- **Step 2 success**  
  supports saying plurality may matter

- **Step 3 success**  
  supports saying diversity may add value beyond plurality

- **Step 4 success**  
  supports saying strong single can rival committee on some slices

- **Step 5 success**  
  supports saying capability can trade off against committee size

This makes the governance language more precise and less emotional.

### Locked evidence boundary — Step 3 (2026-03-21)

Controlled decomposition experiments comparing Step 2 (same-family weak committee) vs Step 3 (cross-family weak committee), run across development and holdout splits on the trust value dataset v2, produced the following confirmed finding:

**Positive case (confirmed):**
- `forecast_style_claim` — mixed-family committee improves target match and weighted score in both splits. Development: ΔTM +0.20, ΔWS +0.256. Holdout: ΔTM +0.40, ΔWS +0.12. Agreement falls ~0.267 both splits.

**Null case:**
- `low_risk_clear_factual` — no target-match lift in either split. Small weighted score gain in holdout only (+0.096). Committees converge regardless of model family.

**Harmful case:**
- `underspecified_legal_policy` — weighted score falls and critical dissent spikes. Development: ΔWS -0.072, Δdissent +0.200. Holdout: ΔWS -0.048, Δdissent +0.400, Δagreement -0.267.

**Bounded claim:**
> Symposia's mixed-family committee value is claim-structure-dependent. It is strongest on forecast-style questions (inferential uncertainty), neutral on clear factual questions, and harmful on underspecified policy questions.

This is the first positive proof case for the diversity thesis. Do not generalise beyond `forecast_style_claim` and structurally similar families until further ladder rungs are completed.

Artifacts:
- `artifacts/trust_pipeline_runs/2026-03-21-family-focused-validation/family_lift_and_focused_validation_summary.json`
- `artifacts/trust_pipeline_runs/2026-03-21-adjacent-family-validation/adjacent_family_validation_summary.json`

---

## Suggested document changes

The following docs should be updated to align with the ladder:

- trust phase docs
- committee-value protocol docs
- benchmark summary
- governance/product note
- README methodology section

Key change:
stop telling the story as “committee vs single in general”.
Start telling it as “plurality effect, diversity effect, and quality–count frontier”.

---

## Recommended immediate revamp plan

### Phase A — freeze the ladder
- add this document
- reference it from trust evaluation docs
- define rung names and claim boundaries

### Phase B — rebuild experiment docs around it
- update protocols to refer to rung comparisons
- define which protocol version applies to which rung
- define allowed datasets per rung

### Phase C — rebuild thesis tests
- retire generic comparison framing
- create one experiment matrix per rung
- align artifacts and summaries with rung interpretation

### Phase D — run only the first rung that matters
Start with:
- Step 1 vs Step 2

Do not run all rungs at once.
Learn in order.

### Phase D0 — provider readiness gate (must pass before rung runs)

Before running any rung containing Anthropic or Google jurors:

- verify model availability for the key
- verify one real prompt succeeds with parseable response
- verify fallback path succeeds for each slot

Record readiness artifact:

- `provider_readiness.json`

Only then run ladder rungs.

---

## Practical conclusion

This ladder simplifies the project.

Instead of trying to answer everything at once, Symposia now asks:

1. Does plurality help?
2. Does diversity help beyond plurality?
3. Does stronger single erase the advantage?
4. Can stronger jurors reduce required committee size?

That is a much cleaner and more faithful test of the thesis.

---

## One-line summary

**The experimental ladder turns Symposia’s testing from a vague committee-versus-single comparison into a sequence of controlled tests for plurality, diversity, and quality–count trade-offs.**
---

## Cycle close — 2026-03-21

### What was run in this cycle

- Step 2 vs Step 3 (same-family committee vs cross-family committee) on trust value dataset v2
- Family-scoped decomposition across 5 families × 5 cases × 2 splits

### What was found

- **Step 2 (plurality) vs single**: same-family plurality does not show measurable quality lift with current weak jurors on tested families. Committee overhead is real (4× cost/latency). Worth-it gate: failed for same-family.
- **Step 3 (diversity) vs Step 2 (plurality)**: cross-family diversity shows bounded positive lift on `forecast_style_claim` (ΔTM +0.20/+0.40, ΔWS +0.256/+0.12). Neutral on `low_risk_clear_factual`. Harmful on `underspecified_legal_policy`.

### What is now settled

- Same-family plurality: weak evidence with current setup. Steps 1 vs 2 should be run formally before a stronger claim is warranted.
- Mixed-family diversity: positive case confirmed on forecast-style claims. Bounded to that family. Does not generalise.
- Testing architecture: ladder-partitioned. Core + ladder runs in CI. Legacy is on-demand.
- Mesaging: governance note and README reflect current evidence boundary.

### What remains open

- Step 1 vs Step 2 not yet formally run (single weak vs same-family committee). This is the next required rung.
- Same-family plurality effect is unconfirmed. May be null with current weak-model setup.
- Step 4 (stronger single baseline) not yet run. Diversity lift may not survive a stronger comparator.
- Dataset too small for Tier A claims (needs ≥25 per family per split; current: 5).

### Next rung

**Step 1 vs Step 2**: single weak juror vs same-family committee of weak jurors.

This is the required next run. Do not skip to Step 4 or adjacent families until Step 1 vs Step 2 is resolved.

Preregister before running. Use protocol v2 as the governing document.