# governance product note

Status: current
Last updated: 2026-03-22
Scope: permitted messaging for synthesis run `2026-03-22-trust-v2`
Process authority: `docs/governance-update-process.md`

## objective

Bound product and governance messaging to the current synthesis artifact set for run `2026-03-22-trust-v2` only.

This note is derived from the current run artifacts for:

- publication scope `synthesis`
- review mode `holistic_single_claim`
- requested decomposition mode `holistic`
- artifact decomposition mode `no_decomposition`
- route set `default_round0_openai_nano`
- escalation route set `escalation_high_risk_openai_mini`
- dataset `trust_value_dataset_v2_2026_03_21`
- evidence tier `tier_b_silver`

## what this run established

- Both development and holdout ended with `final_decision: committee_opt_in_supported` and `overall_default_status: committee_opt_in`.
- Both development and holdout recorded `trust_worth_it_decision: true` while also recording `efficiency_worth_it_decision: false`.
- The run produced complete trace coverage in both splits: `trace_completeness_score: 1.0`.
- Sample-size gates passed in both splits at the current protocol threshold: `case_count=25`.
- The current run captured non-trivial committee-process signals in both splits:
	- development: weighted agreement `0.76`, dissent rate `0.64`, critical dissent rate `0.24`
	- holdout: weighted agreement `0.78`, dissent rate `0.72`, critical dissent rate `0.28`
- The run showed worse measured efficiency than the single baseline in both splits:
	- development: committee false escalations `8` vs single false escalations `5`; escalation-error reduction `-60.0%`; latency ratio `x3.87`; cost ratio `x4.1`
	- holdout: committee false escalations `7` vs single false escalations `5`; escalation-error reduction `-40.0%`; latency ratio `x4.15`; cost ratio `x4.1`
- The protocol therefore supports an opt-in trust position for committee in this run, not a default recommendation.

## what this run did not establish

- Committee default support was not established. `trust_default_support` is `false` in both splits.
- Committee efficiency superiority was not established. The measured escalation-error reduction is negative in both splits and runtime overhead is materially higher.
- Final committee-default proof was not established. `rubric_default_proof.all_required_passed` is `false` in both splits because the current evidence tier is not human-grade.
- Pairwise same-error and unique-contribution claims are unavailable in the current run outputs because those fields are `null`.
- Claim not supported by current run artifacts.
	- Mixed-family lift claims.
	- Family-specific forecast, policy, or danger-family superiority claims.
	- Stronger-single comparator claims.
	- Decomposition findings.

## claim boundary

- This note applies only to the synthesis of development and holdout for run `2026-03-22-trust-v2`.
- It applies only to the current dataset, route setup, protocol versions, and evidence tier recorded in the provenance section below.
- It is a holistic same-family OpenAI nano committee run with OpenAI mini escalation, not a mixed-family run, not a decomposition experiment, and not a full ladder result.
- It supports bounded statements about this run's trust-protocol outcome and efficiency boundary.
- It does not support cross-family, cross-mode, or cross-run generalization.

## permitted messaging

- "In the current holistic synthesis run, committee is supported as an opt-in path, not as the default."
- "Under the preregistered trust protocol, committee was trust-worth-it in both development and holdout, while failing the efficiency-worth-it test in both splits."
- "Current silver-label evidence supports provisional trust assessment, not final committee-default proof."
- "This run showed strong auditability and complete traces, but it did not show a reduction in escalation errors relative to the single baseline."

## next evidence condition

- Reach the evidence condition required for committee-default proof: `tier_c_human` rather than `tier_b_silver`.
- Add per-juror correctness labels so pairwise same-error rate and unique-contribution rate can be measured rather than left `null`.
- Run the canonical ladder to test whether committee value survives stronger-single and different committee-composition comparisons.
- Run separately labeled mixed-family and decomposition experiments before making any family-specific or decomposition-specific product claims.

## provenance

- run_id: `2026-03-22-trust-v2`
- generated_at_utc: `2026-03-22T02:06:40.005721+00:00`
- publication_scope: `synthesis`
- review_mode: `holistic_single_claim`
- requested_decomposition_mode: `holistic`
- artifact_decomposition_mode: `no_decomposition`
- route_set_id: `default_round0_openai_nano`
- committee_route_set_id: `default_round0_openai_nano`
- single_route_set_id: `default_round0_openai_nano`
- escalation_route_set_id: `escalation_high_risk_openai_mini`
- dataset_version: `trust_value_dataset_v2_2026_03_21`
- trust_protocol_version: `trust_rubric_contract_v1_2026_03_21`
- comparison_protocol_version: `committee_value_protocol_v1_2026_03_21`
- evidence_tier: `tier_b_silver`
- git_commit: `6caa468b4078df484b4989ca78cd95073b740eba`
- source_artifacts:
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/v2_pipeline_summary.json`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/development/trust_summary.json`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/holdout/trust_summary.json`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/development/decision.md`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/holdout/decision.md`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/development/trust_decision.md`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/holdout/trust_decision.md`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/development/resolved_protocol.json`
	- `artifacts/trust_pipeline_runs/2026-03-22-trust-v2/holdout/resolved_protocol.json`
