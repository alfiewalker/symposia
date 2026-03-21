# Adjudication Trace run_13f85062fa0d

- profile_set_selected: general_default_v1
- event_count: 10

## Explainability
- sc_001: validated_candidate (support and sufficiency satisfy deterministic thresholds)

## Events
- [1] run_started run_13f85062fa0d: Round 0 run started.
- [2] run_policy_applied run_13f85062fa0d: Run-level execution policy applied.
- [3] subclaim_registered sc_001: Subclaim registered for adjudication.
- [4] juror_execution_succeeded juror_1:sc_001: Juror execution succeeded and produced a parsed decision.
- [5] juror_execution_succeeded juror_2:sc_001: Juror execution succeeded and produced a parsed decision.
- [6] juror_execution_succeeded juror_3:sc_001: Juror execution succeeded and produced a parsed decision.
- [7] juror_execution_succeeded juror_4:sc_001: Juror execution succeeded and produced a parsed decision.
- [8] aggregation sc_001: Subclaim aggregation computed.
- [9] early_stop run_13f85062fa0d: Early stop decision recorded.
- [10] run_runtime_stats run_13f85062fa0d: Runtime statistics recorded.
