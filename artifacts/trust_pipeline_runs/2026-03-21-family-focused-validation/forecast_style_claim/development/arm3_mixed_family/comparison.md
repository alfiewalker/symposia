# OpenAI Round0 Jury Theory Comparison

## Summary
- protocol_version: committee_value_protocol_v1_2026_03_21
- dataset_version: external_dataset_override
- calibration_metric_id: ece10
- model: gpt-5.4-nano
- route_set_id: committee_round0_mixed_small_triplet_v1
- escalation_route_set_id: escalation_high_risk_openai_mini
- case_count: 5
- price_version: openai_total_token_price_v1_2026_03_21
- missing_price_models: claude-3-haiku-20240307, gemini-2.5-flash-lite
- single_false_escalations: 5
- single_missed_escalations: 0
- committee_false_escalations: 5
- committee_missed_escalations: 0
- single_total_escalation_errors: 5
- committee_total_escalation_errors: 5
- escalation_error_reduction_pct: 0.0
- avg_latency_ratio_committee_over_single: 3.0
- avg_cost_ratio_committee_over_single: 1.0
- worth_it_rule_error_reduction_pct: >= 20.0
- worth_it_rule_max_latency_ratio: <= 4.0
- worth_it_rule_max_cost_ratio: <= 4.5
- efficiency_worth_it_decision: False
- worth_it_decision: False (legacy_ambiguous_alias_of_efficiency_worth_it_decision)

## Case Outcomes
| case_id | expected_escalation | single_escalation | committee_escalation | committee_plus_escalation | single_agreement | committee_agreement |
|---|---:|---:|---:|---:|---:|---:|
- avg_latency_ratio_committee_plus_escalation_over_single: 7.96
- avg_cost_ratio_committee_plus_escalation_over_single: 16.1
- committee_plus_escalation_efficiency_worth_it_decision: False
| trust_v2_dev_forecast_01 | 0 | 1 | 1 | 1 | 1.00 | 0.67 |
| trust_v2_dev_forecast_02 | 0 | 1 | 1 | 1 | 1.00 | 0.67 |
| trust_v2_dev_forecast_03 | 0 | 1 | 1 | 1 | 1.00 | 0.67 |
| trust_v2_dev_forecast_04 | 0 | 1 | 1 | 1 | 1.00 | 0.67 |
| trust_v2_dev_forecast_05 | 0 | 1 | 1 | 1 | 1.00 | 0.67 |
