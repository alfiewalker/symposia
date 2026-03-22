# Benchmark Summary

This artifact summarizes the deterministic benchmark and acceptance suites that gate release quality, alongside the current live evaluation evidence boundary.

## Public snapshot

Current evidence says committee value is claim-structure-dependent:

- Forecast-style claims: mixed-family committees help.
- Clear factual claims: mixed-family committees are neutral.
- Underspecified policy claims: mixed-family committees can be harmful.

This is a bounded claim, not a universal committee-superiority claim.

Current default runtime mode: `decomposition_mode=holistic` (holistic single-claim review at all layers).
Experimental ladder evidence in this document is decomposition-path evidence (`decomposition_mode=rule_based`).

Juror personality injection is active: each LLM juror receives a system prompt derived from its `Profile` (stance, evidence demand, safety bias, purpose).

## Deterministic Test Snapshot

- Full test suite: `245 collected` (34 files, marker-partitioned: 125 core / 33 ladder / 87 legacy)
- Core + ladder gate: `158 passed, 87 deselected`
- Benchmark suite: `8/8 cases correct`
- Boundary suite: threshold boundary behavior locked by regression tests
- Committee vs single baseline on benchmark cases:
  - committee advantage: `0`
  - single advantage: `0`
  - both correct: all cases

Test marker partition (2026-03-22):

| Marker | Role | CI default |
|---|---|---|
| `core` | Runtime integrity — always run | Yes |
| `ladder` | Thesis/experiment protocol | Yes |
| `legacy` | Valid but not in default CI | No (on-demand) |

## Evidence boundary details (2026-03-21)

Controlled ladder decomposition runs (Step 2: same-family committee vs Step 3: cross-family committee) on the trust value dataset v2 produced the following family-scoped findings.

Mode tag for this section: `review_mode=decomposed` (legacy/experimental evidence track).

| Case family | Mixed-family delta (TM) | Mixed-family delta (WS) | Interpretation |
|---|---|---|---|
| **forecast_style_claim** | dev +0.20 / hold +0.40 | dev +0.256 / hold +0.12 | **Positive** — consistent lift both splits |
| low_risk_clear_factual | 0.0 / 0.0 | 0.0 / +0.096 | **Neutral** — no target-match lift, minimal WS gain |
| underspecified_legal_policy | 0.0 / 0.0 | -0.072 / -0.048 | **Harmful** — critical dissent +0.20/+0.40, no quality gain |
| high_stakes_advice | 0.0 / 0.0 | -0.096 / +0.024 | Not confirmed either direction |
| plausible_but_dangerous_recommendation | 0.0 / 0.0 | -0.016 / +0.008 | Not confirmed either direction |

**Bounded claim from this evidence:**

> Committee diversity is claim-structure-dependent. It produces measurable quality lift on forecast-style claims, no lift on clear factual claims, and harmful dissent increase on underspecified policy claims.

**What this does not say:**

- Committee is not universally better than same-family plurality.
- Committee diversity is not beneficial across all claim types.
- These results are Tier B evidence (5 cases per family per split). They support bounded family-scoped claims, not broad deployment decisions.

## Efficiency snapshot (same-family OpenAI Round0)

From the hard 8-case live comparison set (single juror vs committee, same model family):

- escalation error reduction: `0%`
- average latency ratio (committee/single): `4.05x`
- average estimated cost ratio (committee/single): `4.01x`
- worth-it rule outcome: `failed` (`efficiency_worth_it_decision=false`)

Current product decision from efficiency evaluation:

- single juror is the default live path
- committee is experimental and opt-in
- committee is justified for opt-in use on forecast-style claim domains based on trust evaluation evidence

Protocol gate for the next decision cycle:

- Committee-value reruns are governed by [Committee Value Experiment Protocol (v1)](committee-value-experiment-protocol-v1.md).
- No new default-path claim should be made unless holdout results are protocol-compliant and reach Tier A sample thresholds.
- Trust-aware interpretation authority is `docs/governance_product_note.md`.

## Interpretation

Current deterministic results are expected for the rule-based juror implementation:

- Accuracy is high on deterministic suites because cases map to explicit hint rules.
- Zero committee advantage on these suites is informative, not a failure — these are not the discriminative case families where diversity adds value.
- Committee advantage is claim-family dependent. It is confirmed on forecast-style claims and not confirmed or negative on other current families.
- Do not merge decomposed and holistic evidence in a single aggregate claim unless results are explicitly split by `review_mode`.

## Current Limits

- Trust evaluation dataset is small (5 cases per family per split). Tier A thresholds (≥25 per slice) require dataset expansion before strong product claims.
- Diversity lift is confirmed only on `forecast_style_claim`. Adjacent family replication on `low_risk_clear_factual` and `underspecified_legal_policy` did not extend the finding.
- Confidence values are trace fields only in the current aggregation path and are not used in score computation.

## Source Tests (experiment ladder pack)

- `tests/test_api_customization_ladder.py`
- `tests/test_juror_routing_yaml.py`
- `tests/test_openai_round0_comparison_runner.py`
- `tests/test_openai_round0_trust_evaluation_runner.py`
- `tests/test_openai_round0_silver_labeling.py`
- `tests/test_protocol_validation.py`
- `tests/test_trust_protocol_validation.py`

Suggested execution command:

`python -m pytest -m "core or ladder" -q`

Full suite (including legacy):

`python -m pytest tests/ -q`

## Release Gate Reminder

Treat this document as a release snapshot, not a claims paper. Keep language factual and tied to executable tests and preregistered protocols.
