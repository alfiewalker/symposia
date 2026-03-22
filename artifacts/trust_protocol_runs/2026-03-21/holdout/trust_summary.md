# Trust Summary

## Protocol
- protocol_version: trust_value_protocol_v2_2026_03_21
- dataset_version: trust_value_dataset_v1_2026_03_21
- route_set_id: default_initial_openai
- case_count: 4

## Trust Metrics
- agreement_rate: 1.0
- weighted_agreement_rate: 1.0
- dissent_rate: 0.0
- critical_dissent_rate: 0.0
- pairwise_same_error_rate: None
- unique_contribution_rate: None
- trace_completeness_score: 1.0

## Decision
- efficiency_worth_it_decision: False
- trust_worth_it_decision: False
- final_decision: insufficient_trust_evidence

## Sample Size Gates
- global_min_cases: passed=False (case_count=4, required>=100)
- per_slice_min_cases: passed=False (insufficient slices: ['ambiguous_mixed_truth', 'domain_sensitive_nuance', 'high_risk_overclaim', 'low_risk_clear_factual', 'plausible_dangerous_recommendation'], required>=25)
