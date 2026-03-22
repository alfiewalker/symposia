# Committee Trust Decomposition Experiment v1

Status: proposed
Date: 2026-03-21
Purpose: isolate plurality effect and cross-family diversity effect under fixed trust-evaluation conditions.

## Program role

This is an evidence-accumulation experiment.

It is not a default-status experiment.

Primary objective:

Determine whether trust lift, if any, comes from:

- plurality itself
- cross-family model diversity beyond same-family plurality

Core decomposition:

- Arm 2 vs Arm 1: plurality effect
- Arm 3 vs Arm 2: cross-family diversity effect

## Thesis under test

Committee-based LLM judgement creates more trust than lone judgement.

This experiment sharpens that thesis into two narrower questions:

1. Does committee plurality improve trust-relevant judgement over a lone cheap judge?
2. Does cross-family model diversity improve trust-relevant judgement beyond same-family plurality?

## Experiment matrix

### Arm 1: single cheap baseline

- arm_id: arm1_single_cheap
- proposed_route_set_id: single_initial_openai_nano_balanced_v1
- composition:
  - balanced_reviewer_v1 on openai / gpt-5.4-nano
- intent:
  - baseline lone cheap judge

### Arm 2: same-family cheap committee

- arm_id: arm2_same_family_committee
- proposed_route_set_id: committee_initial_openai_nano_triplet_v1
- composition:
  - balanced_reviewer_v1 on openai / gpt-5.4-nano
  - sceptical_verifier_v1 on openai / gpt-5.4-nano
  - evidence_maximalist_v1 on openai / gpt-5.4-nano
- intent:
  - isolate plurality with role variation inside one model family

### Arm 3: mixed-family cheap committee

- arm_id: arm3_mixed_family_committee
- proposed_route_set_id: committee_initial_mixed_small_triplet_v1
- composition:
  - balanced_reviewer_v1 on openai / gpt-5.4-nano
  - sceptical_verifier_v1 on anthropic / claude-3-haiku-20240307
  - evidence_maximalist_v1 on google / gemini-2.5-flash-lite
- intent:
  - isolate cross-family diversity beyond plurality itself

### Escalation control

- fixed_escalation_route_set_id: escalation_high_risk_openai_mini
- rule:
  - use the same escalation route for every arm
  - do not vary escalation policy during this experiment

## Model-selection note

This spec uses the cheapest models already represented in the repository runtime and routing patterns.

For this v1 experiment, use:

- openai / gpt-5.4-nano
- anthropic / claude-3-haiku-20240307
- google / gemini-2.5-flash-lite

If a newer low-cost Claude or Gemini SKU is desired, treat that as a separate route revision and freeze it explicitly rather than changing this experiment in place.

## Fixed controls

The following must remain fixed across all arms:

- dataset version: trust_value_dataset_v2_2026_03_21
- rubric contract: trust_rubric_contract_v1_2026_03_21
- split structure: development and holdout
- evidence tier: tier_b_silver
- case families
- metric formulas
- aggregation logic
- escalation policy
- artifact schema

## Case families of interest

Report outcomes overall and by family:

- low_risk_clear_factual
- high_stakes_advice
- forecast_style_claim
- underspecified_legal_policy
- plausible_but_dangerous_recommendation

Interpretation priority should focus on the harder trust-discriminative families:

- high_stakes_advice
- forecast_style_claim
- underspecified_legal_policy
- plausible_but_dangerous_recommendation

## Primary trust-relevant outcomes

Use only trust-relevant outcomes for primary interpretation.

Primary metrics available from the current stack:

- rubric_target_match_rate
- rubric_average_weighted_score
- weighted_agreement_rate
- critical_dissent_rate
- trace_completeness_score
- rubric verdict distribution by split and by slice

Primary slice-level readout:

- rubric_target_match_rate by case family
- rubric_average_weighted_score by case family

Required qualitative review targets:

- dissent usefulness
- caveat quality
- calibration quality
- auditability of per-juror traces

If needed, qualitative review should be generated from existing per-case and per-juror artifacts rather than changing the rubric mid-run.

## Preregistered hypotheses

### H1: plurality effect

Arm 2 will outperform Arm 1 on trust-relevant judgement.

Interpretation target:

- plurality is supported if Arm 2 exceeds Arm 1 on both:
  - overall rubric_target_match_rate
  - overall rubric_average_weighted_score
- and does not degrade:
  - trace_completeness_score
  - safety-related hard-fail behavior

### H2: cross-family diversity effect

Arm 3 will outperform Arm 2 on trust-relevant judgement.

Interpretation target:

- cross-family diversity is supported if Arm 3 exceeds Arm 2 on both:
  - overall rubric_target_match_rate
  - overall rubric_average_weighted_score
- and the improvement appears in at least two hard case families
- and does not degrade:
  - trace_completeness_score
  - safety-related hard-fail behavior

## Preregistered null rules

- If Arm 2 does not beat Arm 1 on the preregistered primary metrics, do not claim plurality lift.
- If Arm 3 does not beat Arm 2 on the preregistered primary metrics, do not claim cross-family diversity lift.
- If results split by case family, report the split explicitly and do not collapse the outcome into a universal superiority claim.
- If an arm improves one primary metric but worsens another, report mixed evidence rather than forcing a directional conclusion.

## Interpretation matrix

### Outcome A

- Arm 2 > Arm 1
- Arm 3 > Arm 2

Interpretation:

- plurality helps
- cross-family diversity adds additional trust signal

### Outcome B

- Arm 2 > Arm 1
- Arm 3 approximately equals Arm 2

Interpretation:

- plurality matters more than provider diversity in the tested setup

### Outcome C

- Arm 2 approximately equals Arm 1
- Arm 3 approximately equals Arm 2

Interpretation:

- current committee design is not yet earning clear trust lift

### Outcome D

- Arm 2 > Arm 1 in some families only
- Arm 3 > Arm 2 in some families only

Interpretation:

- the thesis is conditional by case family
- report family-specific lift rather than system-wide lift

## Required artifacts

Per arm and per split, preserve the current artifact set:

- trust_summary.json
- rubric_summary.json
- rubric_per_case.json
- rubric_default_proof.json
- comparison.json
- per_case.json
- per_juror.json

Add experiment-level synthesis artifacts:

- arm_comparison_summary.json
- arm_slice_comparison.json
- experiment_readout.md

## Protocol and freeze note

Do not edit the frozen dataset manifest or frozen rubric contract in place.

Because the current protocol and dataset allowlists only enumerate existing OpenAI route sets, this experiment requires a sibling protocol artifact or protocol version bump that:

- keeps metric formulas unchanged
- keeps rubric contract unchanged
- keeps dataset unchanged
- expands allowed_route_sets only to the preregistered arm route_set_id values
- records the hypotheses and null rules above

## Minimal implementation plan

1. Add a single-juror route for Arm 1.
2. Add a three-juror same-family OpenAI nano route for Arm 2.
3. Add a three-juror mixed-provider small-model route for Arm 3.
4. Register the routes in juror_routing.yaml.
5. Create the experiment protocol artifact with expanded allowlists and fixed hypotheses.
6. Run development first, then holdout unchanged.
7. Produce experiment-level cross-arm comparison artifacts.

## Canonical experiment statement

A three-arm bounded experiment will test whether trust lift comes from committee plurality, cross-family model diversity, or neither, under fixed dataset, rubric, protocol, and escalation conditions.