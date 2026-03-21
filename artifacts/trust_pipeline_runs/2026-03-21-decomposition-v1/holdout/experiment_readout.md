# Committee Trust Decomposition Readout

- protocol_version: committee_trust_decomposition_protocol_v1_2026_03_21
- split_id: holdout

## Arm Summary

- arm1_single_cheap: target_match=0.2, weighted_score=1.64
- arm2_same_family_committee: target_match=0.16, weighted_score=1.6496
- arm3_mixed_family_committee: target_match=0.24, weighted_score=1.6848

## Primary Comparisons

- plurality_effect_arm2_minus_arm1: {'rubric_target_match_rate': -0.04, 'rubric_average_weighted_score': 0.0096, 'weighted_agreement_rate': -0.0667, 'critical_dissent_rate': 0.08, 'trace_completeness_score': 0.0}
- cross_family_diversity_effect_arm3_minus_arm2: {'rubric_target_match_rate': 0.08, 'rubric_average_weighted_score': 0.0352, 'weighted_agreement_rate': -0.1066, 'critical_dissent_rate': 0.08, 'trace_completeness_score': 0.0}

## Null Rules

- if arm2_same_family_committee does not exceed arm1_single_cheap on preregistered primary metrics, do not claim plurality lift
- if arm3_mixed_family_committee does not exceed arm2_same_family_committee on preregistered primary metrics, do not claim cross_family_diversity_lift
- if results split by case family, report family-specific lift instead of universal superiority
