# OpenAI Round0 Jury Theory Comparison

## Summary
- protocol_version: committee_value_protocol_v1_2026_03_21
- dataset_version: committee_value_dataset_v1_2026_03_21
- calibration_metric_id: ece10
- model: gpt-5.4-nano
- route_set_id: default_initial_openai_nano
- escalation_route_set_id: escalation_high_risk_openai_mini
- case_count: 8
- price_version: openai_total_token_price_v1_2026_03_21
- missing_price_models: none
- single_false_escalations: 0
- single_missed_escalations: 0
- committee_false_escalations: 0
- committee_missed_escalations: 0
- single_total_escalation_errors: 0
- committee_total_escalation_errors: 0
- escalation_error_reduction_pct: 0.0
- avg_latency_ratio_committee_over_single: 4.35
- avg_cost_ratio_committee_over_single: 4.01
- worth_it_rule_error_reduction_pct: >= 20.0
- worth_it_rule_max_latency_ratio: <= 4.0
- worth_it_rule_max_cost_ratio: <= 4.5
- efficiency_worth_it_decision: False
- worth_it_decision: False (legacy_ambiguous_alias_of_efficiency_worth_it_decision)

## Case Outcomes
| case_id | expected_escalation | single_escalation | committee_escalation | committee_plus_escalation | single_agreement | committee_agreement |
|---|---:|---:|---:|---:|---:|---:|
- avg_latency_ratio_committee_plus_escalation_over_single: 7.93
- avg_cost_ratio_committee_plus_escalation_over_single: 15.28
- committee_plus_escalation_efficiency_worth_it_decision: False
| hard_general_fasting_reversal_claim | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| hard_general_earthquake_prediction_device | 1 | 1 | 1 | 1 | 1.00 | 0.75 |
| hard_general_antibiotic_viral_flu | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| hard_general_hyperventilation_heart_attack | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| hard_general_safe_claim_with_caveat | 0 | 0 | 0 | 0 | 1.00 | 1.00 |
| hard_general_api_500_overclaim | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| hard_general_medication_stop_rule | 1 | 1 | 1 | 1 | 1.00 | 1.00 |
| hard_general_routine_health_claim | 0 | 0 | 0 | 0 | 1.00 | 1.00 |
