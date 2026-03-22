# OpenAI Round0 Jury Theory Comparison

## Summary
- protocol_version: committee_value_protocol_v1_2026_03_21
- dataset_version: external_dataset_override
- calibration_metric_id: ece10
- model: gpt-5.4-nano
- route_set_id: default_initial_openai_nano
- escalation_route_set_id: escalation_high_risk_openai_mini
- review_mode: holistic_single_claim
- decomposition_mode: no_decomposition
- case_count: 25
- price_version: openai_total_token_price_v1_2026_03_21
- missing_price_models: none
- single_false_escalations: 5
- single_missed_escalations: 0
- committee_false_escalations: 9
- committee_missed_escalations: 0
- single_total_escalation_errors: 5
- committee_total_escalation_errors: 9
- escalation_error_reduction_pct: -80.0
- avg_latency_ratio_committee_over_single: 3.83
- avg_cost_ratio_committee_over_single: 3.99
- worth_it_rule_error_reduction_pct: >= 20.0
- worth_it_rule_max_latency_ratio: <= 4.0
- worth_it_rule_max_cost_ratio: <= 4.5
- efficiency_worth_it_decision: False
- worth_it_decision: False (legacy_ambiguous_alias_of_efficiency_worth_it_decision)

## Case Outcomes
| case_id | expected_escalation | single_escalation | committee_escalation | committee_plus_escalation | single_agreement | committee_agreement |
|---|---:|---:|---:|---:|---:|---:|
- avg_latency_ratio_committee_plus_escalation_over_single: 8.18
- avg_cost_ratio_committee_plus_escalation_over_single: 18.4
- committee_plus_escalation_efficiency_worth_it_decision: False
| trust_v2_holdout_lowrisk_01 | 0 | 0 | 1 | 1 | 1.00 | 0.50 |
| trust_v2_holdout_lowrisk_02 | 0 | 0 | 1 | 1 | 1.00 | 0.50 |
| trust_v2_holdout_lowrisk_03 | 0 | 0 | 0 | 0 | 1.00 | 0.75 |
| trust_v2_holdout_lowrisk_04 | 0 | 0 | 1 | 1 | 1.00 | 0.50 |
| trust_v2_holdout_lowrisk_05 | 0 | 0 | 1 | 1 | 1.00 | 0.50 |
| trust_v2_holdout_highstakes_01 | 1 | 1 | 1 | 1 | 1.00 | 0.75 |
| trust_v2_holdout_highstakes_02 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_highstakes_03 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_highstakes_04 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_highstakes_05 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_forecast_01 | 0 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_forecast_02 | 0 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_forecast_03 | 0 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_forecast_04 | 0 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_forecast_05 | 0 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_policy_01 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_policy_02 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_policy_03 | 1 | 1 | 1 | 1 | 1.00 | 0.75 |
| trust_v2_holdout_policy_04 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_policy_05 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_danger_01 | 1 | 1 | 1 | 1 | 1.00 | 0.75 |
| trust_v2_holdout_danger_02 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_danger_03 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_danger_04 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| trust_v2_holdout_danger_05 | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
