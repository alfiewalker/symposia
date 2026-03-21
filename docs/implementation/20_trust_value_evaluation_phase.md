# Phase 12 — Trust Value Evaluation

## Purpose

Establish whether Symposia’s committee path creates enough additional trust value to justify its overhead, even when raw correctness lift is small or absent.

This phase exists because Symposia is not only an efficiency or error-minimisation system. Its core product thesis includes trust through plural, auditable judgement.

---

## Core question

Does committee-based adjudication provide enough additional trust signal to justify greater cost and latency relative to a single juror path?

This phase does **not** replace efficiency evaluation. It adds the missing trust layer.

---

## Relationship to existing protocol

- Committee-value protocol v1 remains the efficiency-oriented and error-oriented comparison layer.
- This phase defines the trust-oriented layer that sits alongside it.
- No runtime changes should be introduced while this phase is being specified and executed.
- Trust evaluation must be added as a protocol layer first, not as post-hoc narrative.

---

## Preregistration locks (required before development run)

The following must be frozen before any development run:

- exact metric formulas and denominators
- slice membership and case-to-slice mapping
- trust metric weights (if any composite is used)
- trust thresholds and decision boundaries
- conflict-resolution rule between efficiency and trust decisions

Any change to any item above requires:

- new trust protocol version
- explicit changelog
- reset of development and holdout interpretation under the new version

---

## Scope

### In scope

- trust metrics definition
- trust-oriented protocol gates
- agreement and dissent measurement
- independence and correlation interpretation
- trace completeness scoring
- committee vs single trust-value comparison
- decision criteria for committee-default vs committee-opt-in

### Out of scope

- runtime architecture changes
- provider expansion
- live escalation expansion
- new profile behaviour
- new routing logic
- new top-level API verbs

---

## Trust dimensions

Trust must be treated as a vector, not a single scalar.

### 1. Agreement signal

Measures whether multiple jurors converge on the same judgement.

Examples:

- agreement proportion
- weighted agreement
- slice-level agreement by case family

### 2. Dissent visibility

Measures whether disagreement is surfaced clearly rather than hidden.

Examples:

- dissent present / absent
- dissent severity
- minority rationale availability
- proportion of cases with visible disagreement records

### 3. Independence signal

Measures whether the committee behaves like genuinely plural judgement rather than repeated copies of one model path.

Examples:

- pairwise agreement
- same-error rate
- unique-correct contribution
- slice-level correlation diagnostics

### 4. Trace completeness

Measures whether the system gives enough audit information for a user or institution to inspect the basis of judgement.

Examples:

- per-juror execution record completeness
- parse/failure visibility
- policy metadata presence
- protocol artifact completeness
- decision interpretation completeness

### 5. Stability under ambiguity

Measures whether committee outputs remain coherent and interpretable on ambiguous or mixed-truth cases.

Examples:

- agreement drop under ambiguity
- dissent rate under ambiguity
- escalation consistency
- confidence spread or confidence dispersion if available

---

## Required metrics

The phase must define and report, at minimum:

- agreement_rate
- weighted_agreement_rate
- dissent_rate
- critical_dissent_rate
- pairwise_same_error_rate
- unique_contribution_rate
- trace_completeness_score
- trust_signal_score (composite only if fully defined and preregistered)

Metrics must be computed globally and by slice.

Exact minimum definitions:

- agreement_rate
	- numerator: number of cases where at least 75% of committee jurors share the same escalation decision
	- denominator: total evaluated cases
	- formula: agreement_rate = numerator / denominator

- weighted_agreement_rate
	- let p_majority be the fraction of committee jurors in the majority escalation decision for a case
	- numerator: sum over cases of p_majority
	- denominator: total evaluated cases
	- formula: weighted_agreement_rate = (sum p_majority) / denominator

- dissent_rate
	- numerator: number of cases with at least one committee juror dissenting from majority escalation decision
	- denominator: total evaluated cases
	- formula: dissent_rate = numerator / denominator

- critical_dissent_rate
	- critical dissent case: at least one dissenting juror with confidence >= 0.80 against majority escalation decision
	- numerator: number of critical dissent cases
	- denominator: total evaluated cases
	- formula: critical_dissent_rate = numerator / denominator

- pairwise_same_error_rate
	- for each juror pair (i, j): numerator_ij = number of cases both i and j are wrong versus label
	- denominator_ij: total evaluated cases for which both i and j produced a parsed decision
	- formula per pair: same_error_rate_ij = numerator_ij / denominator_ij
	- report global metric as arithmetic mean across all juror pairs

- unique_contribution_rate
	- unique contribution case for juror i: i is correct versus label and committee majority flips to wrong if i is removed
	- numerator: number of unique contribution cases across all jurors
	- denominator: total evaluated cases
	- formula: unique_contribution_rate = numerator / denominator

- trace_completeness_score
	- required fields per case:
		- per-juror execution records
		- parsed_ok and error_code visibility
		- run policy metadata
		- protocol_version, dataset_version, and route_set_id
		- decision interpretation section present
	- numerator: number of required fields present across all case records
	- denominator: total required fields across all case records
	- formula: trace_completeness_score = numerator / denominator

- trust_signal_score (optional composite)
	- allowed only if preregistered with explicit weights w_k summing to 1.0
	- formula: trust_signal_score = sum over k of (w_k * normalized_metric_k)
	- if not preregistered, this field must be omitted

---

## Slice requirements

Trust metrics must be reported by case family, not only globally.

Minimum slice classes:

- low-risk clear factual
- high-risk overclaim
- ambiguous / mixed-truth
- domain-sensitive nuance
- plausible but dangerous recommendation

The protocol must define case membership explicitly through the dataset manifest.

Target matrix for evidence scaling (minimum):

- development split:
	- low-risk clear factual: >= 25
	- high-risk overclaim: >= 25
	- ambiguous / mixed-truth: >= 25
	- domain-sensitive nuance: >= 25
	- plausible but dangerous recommendation: >= 25
	- total minimum: >= 125
- holdout split:
	- low-risk clear factual: >= 25
	- high-risk overclaim: >= 25
	- ambiguous / mixed-truth: >= 25
	- domain-sensitive nuance: >= 25
	- plausible but dangerous recommendation: >= 25
	- total minimum: >= 125

Gate application semantics:

- sample-size gates apply to each evaluated split independently
- development passing gates does not imply holdout passes gates
- holdout decision claims are valid only if holdout gates pass

---

## Comparison arms

At minimum:

- single-juror live path
- committee live path

Optional later:

- weighted committee
- heterogeneous committee
- deterministic baseline path

Single vs committee trust comparison must use the same provider/model family unless the protocol explicitly allows otherwise.

---

## Decision rules

Trust evaluation must not rely on post-hoc interpretation.

The protocol must preregister:

- minimum acceptable trace completeness
- minimum acceptable agreement signal for low-risk slices
- minimum acceptable dissent visibility for ambiguous slices
- maximum acceptable same-error rate on high-risk slices
- required exclusion of zero for key trust deltas where statistical confidence is used

The protocol must clearly distinguish:

- efficiency_worth_it_decision
- trust_worth_it_decision

These are not the same thing.

Conflict-resolution rule (required):

- if efficiency_worth_it_decision=false and trust_worth_it_decision=true, output must be committee_opt_in_supported unless a stricter preregistered rule upgrades to committee_default_supported
- if efficiency_worth_it_decision=true and trust_worth_it_decision=false, output must not be committee_default_supported
- committee_default_supported requires trust_worth_it_decision=true and no preregistered safety regression flags
- if sample-size gates fail, output must be insufficient_trust_evidence regardless of point estimates

---

## Trust-aware decision output

A run must be able to conclude one of:

1. committee_default_supported
2. committee_opt_in_supported
3. single_default_supported
4. insufficient_trust_evidence

The output must explain whether committee value is being justified by:

- correctness lift
- trust lift
- both
- neither

Evidence-tier policy:

- Tier A + Tier B evidence may support bounded product decisions:
	- committee opt-in supported
	- narrowly scoped low-risk committee-default recommendations with explicit caveats
	- provisional trust positioning
- Tier C evidence is required only for strongest claims:
	- universal committee-default
	- institutional superiority claims
	- strongest trust claims

---

## Statistical requirements

If sample size allows, report:

- bootstrap confidence intervals for trust deltas
- slice-level intervals where feasible

If sample size is too small, the run must say so explicitly and avoid false precision.

Minimum sample-size gates:

- global trust comparison gate: at least 100 evaluated cases total
- per-slice reporting gate: at least 25 evaluated cases per slice
- pairwise correlation gate: at least 50 co-evaluated cases per juror pair

If a gate fails:

- metric is reported as insufficient_sample
- no threshold pass/fail claim is allowed for that metric
- final decision must downgrade to insufficient_trust_evidence unless all preregistered critical gates are satisfied

Pairwise gate interpretation:

- if per-pair co-evaluated minimum is not met, pairwise_same_error_rate must be marked insufficient_sample
- insufficient pairwise coverage blocks committee_default_supported

---

## Artifact requirements

Each trust evaluation run must emit:

- trust_summary.json
- trust_summary.md
- agreement.json
- dissent.json
- independence.json
- trace_completeness.json
- trust_decision.md
- resolved_protocol.json
- dataset manifest reference

`dataset manifest reference` must include at minimum:

- dataset_version
- manifest_path
- manifest_sha256
- split_id
- case_ids

These artifacts must not replace the committee-value artifacts. They extend them.

---

## Governance rules

- protocol must be frozen before live reruns
- dataset manifest must be frozen before live reruns
- trust thresholds must be preregistered
- any change to trust metrics, weighting, or thresholds requires a new protocol version
- no runtime changes during trust evaluation execution
- development run is not permitted until preregistration locks in this document are frozen

Dataset expansion workflow (required):

1. draft candidate cases
2. assign provisional slice
3. dual-label expected outcome with provenance
4. adjudicate label disagreements
5. compute/update manifest hashes
6. lock manifest batch
7. run development protocol
8. run holdout protocol unchanged

Case intake template (required fields):

- case_id
- content
- expected_escalation
- split_id (development|holdout)
- slice_ids
- source_type (benchmark|adversarial|real_output|high_stakes_advice|mixed_truth)
- provenance_reference
- labeler_a
- labeler_b
- adjudicator
- label_confidence (high|medium|low)
- label_provenance_hash

---

## Observed boundary condition (2026-03-21)

The first bounded runs against this phase's framework have produced a confirmed family-scoped finding. This is now part of the evidence stack for the trust thesis.

**Family-specific trust lift is real and claim-structure-dependent.**

From Step 2 vs Step 3 decomposition (same-family vs cross-family weak committee), trust value dataset v2:

| Case family | Trust quality effect | Evidence |
|---|---|---|
| `forecast_style_claim` | **Positive lift** — target match and weighted score improve in both splits | Confirmed; consistent dev and holdout |
| `low_risk_clear_factual` | **Neutral** — no target-match lift, agreement unchanged | Confirmed null; committees converge regardless of family mix |
| `underspecified_legal_policy` | **Harmful** — weighted score falls, critical dissent spikes | Confirmed harm; diverse models fragment without resolving |

**Implication for this phase's success criteria:**

The question "does committee produce stronger trust signals than single-juror output?" now has a conditional answer: yes, on forecast-style claims; no on clear factual claims; negatively on underspecified policy claims.

This means the success criteria below must be evaluated **per slice**, not globally. A global positive or global negative would obscure the real signal.

Family-scoped trust lift (on `forecast_style_claim`) is the first positive proof case for the trust thesis. It is Tier B evidence (5 cases per family per split). Tier A thresholds require dataset expansion to ≥25 cases per slice.

Artifact references:
- `artifacts/trust_pipeline_runs/2026-03-21-family-focused-validation/family_lift_and_focused_validation_summary.json`
- `artifacts/trust_pipeline_runs/2026-03-21-adjacent-family-validation/adjacent_family_validation_summary.json`

---

## Success criteria for this phase

This phase is complete when Symposia can say, with protocol-backed evidence:

- whether committee produces stronger trust signals than single-juror output
- on which slices this holds
- whether that trust lift justifies committee-default status
- whether the current system supports committee as default, opt-in, or not yet justified

---

## Immediate next steps

1. define machine-readable trust protocol
2. define trust dataset slices in the manifest
3. add trust artifact schema
4. implement trust metrics runner
5. execute development set
6. execute locked holdout set
7. issue trust-aware decision

---

## Non-goal reminder

This phase does not prove truth.
It evaluates whether committee judgement creates enough additional trust value to justify its role in Symposia.

That is the correct frame.
