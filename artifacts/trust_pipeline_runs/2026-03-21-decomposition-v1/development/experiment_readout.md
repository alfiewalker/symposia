# Committee Trust Decomposition Readout

- protocol_version: committee_trust_decomposition_protocol_v1_2026_03_21
- split_id: development

## Arm Summary

- arm1_single_cheap: target_match=0.28, weighted_score=1.6336
- arm2_same_family_committee: target_match=0.16, weighted_score=1.6304
- arm3_mixed_family_committee: target_match=0.16, weighted_score=1.616

## Primary Comparisons

- plurality_effect_arm2_minus_arm1: {'rubric_target_match_rate': -0.12, 'rubric_average_weighted_score': -0.0032, 'weighted_agreement_rate': -0.1467, 'critical_dissent_rate': 0.12, 'trace_completeness_score': 0.0}
- cross_family_diversity_effect_arm3_minus_arm2: {'rubric_target_match_rate': 0.0, 'rubric_average_weighted_score': -0.0144, 'weighted_agreement_rate': -0.0466, 'critical_dissent_rate': 0.0, 'trace_completeness_score': 0.0}

## Null Rules

- if arm2_same_family_committee does not exceed arm1_single_cheap on preregistered primary metrics, do not claim plurality lift
- if arm3_mixed_family_committee does not exceed arm2_same_family_committee on preregistered primary metrics, do not claim cross_family_diversity_lift
- if results split by case family, report family-specific lift instead of universal superiority
