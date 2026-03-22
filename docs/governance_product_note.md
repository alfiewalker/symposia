# Governance Note: Holistic Synthesis Run Results

Status: current  
Last updated: 2026-03-22  
Scope: public-facing summary for run `2026-03-22-v2-rubric-holistic`

## Objective

This note reports the observed results from the latest holistic synthesis run. It is limited to the metrics and outcomes recorded in the run artifacts for `2026-03-22-v2-rubric-holistic`.

## Headline Result

The run produced the same top-line outcome on both development and holdout: `committee_opt_in_supported`.

## Results Summary

| Metric | Development | Holdout |
|---|---:|---:|
| Final decision | `committee_opt_in_supported` | `committee_opt_in_supported` |
| Cases scored | `25` | `25` |
| Agreement rate | `0.88` | `0.84` |
| Weighted agreement | `0.91` | `0.88` |
| Dissent rate | `0.24` | `0.32` |
| Critical dissent rate | `0.08` | `0.16` |
| Weighted rubric score | `1.5184` | `1.5632` |
| Rubric target match rate | `0.08` | `0.12` |
| Trace completeness | `1.0` | `1.0` |

## Interpretation

- The outcome was consistent across both splits.
- Agreement remained high on both development and holdout.
- Holdout showed more disagreement than development, with higher dissent and higher critical dissent.
- Trace completeness was perfect on both splits, indicating complete artifact capture for scored cases.
- This run should be read as a results snapshot for the tested configuration, not as a claim about every possible multi-juror setup.

## Public Summary Wording

- "In the latest holistic synthesis run, both development and holdout ended with `committee_opt_in_supported`."
- "Agreement remained high on both splits, while dissent was higher on holdout than on development."
- "The run was fully trace-complete across all scored cases."
- "These results apply to the tested run configuration and evidence tier."
- "A higher evidence tier would increase external credibility, but it does not change the observed outcome of this run."

## Claim Boundary

- This note reports the observed output of one run configuration.
- It does not claim that every multi-juror configuration will produce the same result.
- It does not treat this run as a blanket statement about all user-selected juror counts or routing choices.
- The evidence tier should be read as part of the run context, not as a reason to restate or suppress the observed result.
- Any broader product claim should be tied to additional runs or separately stated evidence.

## Provenance

- run_id: `2026-03-22-v2-rubric-holistic`
- generated_at_utc: `2026-03-22T03:52:03.077243+00:00`
- publication_scope: `synthesis`
- review_mode: `holistic_single_claim`
- execution_policy.decomposition_mode: `holistic`
- execution_policy.evidence_label_tier: `tier_b_silver`
- route_set_id: `default_initial_openai_nano`
- dataset_version: `trust_value_dataset_v2_2026_03_21`
- protocol_version: `trust_rubric_contract_v1_2026_03_21`
- development.case_count: `25`
- holdout.case_count: `25`
- development.final_decision: `committee_opt_in_supported`
- holdout.final_decision: `committee_opt_in_supported`
- source_artifact: `artifacts/trust_pipeline_runs/2026-03-22-v2-rubric-holistic/pipeline_summary.json`