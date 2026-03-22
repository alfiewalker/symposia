# Governance Evidence Update Process (Formal SOP)

Status: active  
Owner: protocol/governance maintainers  
Applies to: `docs/governance_product_note.md`, README evidence framing

---

## Purpose

Ensure governance and public evidence language is derived from **current run artifacts** only.

Core rule:

$$
\text{governance note} = \text{rendered interpretation of current run artifacts}
$$

Manual prose updates without artifact backing are not allowed.

---

## Split Policy (Why development and holdout)

The trust evaluation runner is split-scoped per call:

- `split_id="development"` for iterative assessment
- `split_id="holdout"` for confirmation and claim publication boundary

Running both is expected for evaluation cycles. Claims intended for governance/public messaging must be backed by the selected publication scope and explicitly labeled by split.

Canonical trust-governance runs use:

- `publication_scope=synthesis`
- `splits=development holdout`
- `decomposition_mode=holistic`

unless the run is explicitly labeled as a decomposition experiment.

---

## Required Source Run Identity

Before updating governance/README, capture:

- `run_id`
- `generated_at_utc`
- `publication_scope` (`development` | `holdout` | `synthesis`)
- `review_mode`
- `decomposition_mode`
- `route_set_id`
- `dataset_version`
- `protocol_version`
- `evidence_tier`

If any field is absent in the selected run artifact set, write exactly:

`Claim not supported by current run artifacts.`

Do not infer missing values.

---

## Minimum Artifact Set

Read these files from the **same run**:

- `pipeline_summary.json`
- `trust_summary.json` (or `comparison.json` when trust summary is unavailable)
- `decision.md`
- `resolved_protocol.json`

If the note includes family-specific statements (forecast lift, mixed-family lift, decomposition findings), include same-run family-lift artifact(s).

For ladder governance, the run package must also preserve:

- rung label
- ladder step index
- route setup used for committee/single/escalation
- consolidated per-rung summary artifact

This is required so later cross-rung analysis can be performed without reconstructing metadata by hand.

---

## Canonical Ladder Program

The trust-governance program is organized as a labeled ladder. These labels must be used in run manifests, artifact directories, and analysis summaries.

### Rung labels

- `rung_1_single_weak`
- `rung_2_same_family_weak_committee`
- `rung_3_mixed_family_weak_committee`
- `rung_4_single_strong`
- `rung_5_smaller_stronger_committee`

### Canonical rung definitions

#### 1. Single weak baseline

Purpose: test whether a weak lone judge is viable.

Route setup:

- `committee_route_set_id=default_round0_openai_nano`
- `single_route_set_id=default_round0_openai_nano`

Interpretation:

$$
	ext{baseline floor}
$$

#### 2. Same-family weak committee

Purpose: test plurality without cross-family diversity.

Route setup:

- `committee_route_set_id=default_round0_openai_nano`
- `single_route_set_id=default_round0_openai_nano`

Primary comparison:

- single nano
- committee nano

Interpretation:

$$
	ext{Step 2 vs Step 1} = \text{plurality effect}
$$

#### 3. Mixed-family weak committee

Purpose: test diversity beyond same-family plurality.

Route setup:

- `committee_route_set_id=committee_round0_mixed_small_triplet_v1`
- `single_route_set_id=default_round0_openai_nano`

Interpretation:

$$
	ext{Step 3 vs Step 2} = \text{cross-family diversity effect}
$$

#### 4. Single stronger baseline

Purpose: test whether a stronger lone judge masks committee lift.

Route setup:

- `committee_route_set_id=default_round0_openai_mini`
- `single_route_set_id=default_round0_openai_mini`

Note: this uses the same mini route set for both paths, but the single baseline is still a one-juror execution selected from that route at runtime.

Interpretation:

$$
	ext{Step 4 vs prior steps} = \text{strong single challenge}
$$

#### 5. Smaller stronger committee

Purpose: test the quality-count frontier.

Route setup:

- `committee_route_set_id=committee_round0_openai_mini_triplet_v1`
- `single_route_set_id=default_round0_openai_mini`

Interpretation:

$$
	ext{can better jurors reduce committee size?}
$$

### Minimal essential set

If only the essential program is run, execute these four ladder steps:

1. `rung_1_single_weak`
2. `rung_2_same_family_weak_committee`
3. `rung_3_mixed_family_weak_committee`
4. `rung_4_single_strong`

This is the minimum set needed to estimate:

- plurality effect
- cross-family diversity effect
- masking by a stronger single judge

### Experimental extensions

The following are separate from the canonical evidence ladder and must be labeled experimental:

- decomposition experiments: run the same rung with `decomposition_mode=holistic` and `decomposition_mode=rule_based`
- family-focused runs: execute only after a signal appears in the ladder and keep slices explicit (for example `forecast_style_claim`, `underspecified_legal_policy`, `low_risk_clear_factual`)

---

## Stale-Mixing Refusal Rules

Do not mix across runs, dates, or modes unless explicitly labeled as synthesis.

If a sentence mentions any of the following, verify from current run artifacts:

- forecast lift
- mixed-family lift
- decomposition findings
- committee opt-in/default support

If unsupported, omit it or replace with:

`Claim not supported by current run artifacts.`

---

## Two-Stage Build (Mandatory)

Canonical runner command (evidence path):

```bash
PYTHONPATH=. .venv/bin/python scripts/run_trust_pipeline.py \
  --run-id 2026-03-22-v2-rubric-holistic \
  --publication-scope synthesis \
  --committee-route-set-id default_round0_openai_nano \
  --single-route-set-id default_round0_openai_nano \
  --escalation-route-set-id escalation_high_risk_openai_mini \
  --decomposition-mode holistic \
  --evidence-tier tier_b_silver \
  --splits development holdout
```

Decomposition experiment command (non-canonical, explicitly experimental):

```bash
PYTHONPATH=. .venv/bin/python scripts/run_trust_pipeline.py \
  --run-id 2026-03-22-v2-rubric-rule-based-experiment \
  --publication-scope synthesis \
  --committee-route-set-id default_round0_openai_nano \
  --single-route-set-id default_round0_openai_nano \
  --escalation-route-set-id escalation_high_risk_openai_mini \
  --decomposition-mode rule_based \
  --evidence-tier tier_b_silver \
  --splits development holdout
```

Dry plumbing check command (non-public, iterative only):

```bash
PYTHONPATH=. .venv/bin/python scripts/run_trust_pipeline.py \
  --run-id 2026-03-22-v2-rubric-dry-dev \
  --publication-scope development \
  --committee-route-set-id default_round0_openai_nano \
  --single-route-set-id default_round0_openai_nano \
  --escalation-route-set-id escalation_high_risk_openai_mini \
  --decomposition-mode holistic \
  --evidence-tier tier_b_silver \
  --splits development
```

Only canonical evidence-path runs may update governance or README evidence claims.

Outputs are written to:

- `artifacts/trust_pipeline_runs/<run_id>/development/*`
- `artifacts/trust_pipeline_runs/<run_id>/holdout/*`
- `artifacts/trust_pipeline_runs/<run_id>/pipeline_summary.json`

Canonical ladder storage requirement:

- `artifacts/trust_ladder_runs/<run_id>/manifest.json`
- `artifacts/trust_ladder_runs/<run_id>/<rung_label>/development/*`
- `artifacts/trust_ladder_runs/<run_id>/<rung_label>/holdout/*`
- `artifacts/trust_ladder_runs/<run_id>/<rung_label>/pipeline_summary.json`
- `artifacts/trust_ladder_runs/<run_id>/ladder_summary.json`

`manifest.json` must record every rung label, route setup, decomposition mode, publication scope, and artifact paths.

`ladder_summary.json` must aggregate the per-rung summaries so cross-rung analysis is possible after all runs complete.

### Stage 1: Machine extraction

Generate `docs/governance_note_inputs.json` with machine-extracted fields only.

Suggested minimal shape:

```json
{
  "source_run": {
    "run_id": "...",
    "generated_at_utc": "...",
    "publication_scope": "development|holdout|synthesis",
    "review_mode": "...",
    "decomposition_mode": "...",
    "route_set_id": "...",
    "dataset_version": "...",
    "protocol_version": "...",
    "evidence_tier": "..."
  },
  "summary": {"...": "..."},
  "claim_checks": {"...": "..."},
  "source_artifacts": ["..."]
}
```

### Stage 2: Deterministic render

Render `docs/governance_product_note.md` from `docs/governance_note_inputs.json` only.

No text copied from prior notes unless that exact claim is present in current inputs.

Renderer hard-fail rule:

- Fail rendering if any required provenance field is missing:
  - `run_id`
  - `protocol_version`
  - `dataset_version`
  - `source_artifacts`

`Claim not supported by current run artifacts.` is for unsupported evidence claims, not for missing required provenance.

---

## Governance Note Schema (Fixed)

Use exactly these sections:

1. objective
2. what this run established
3. what this run did not establish
4. claim boundary
5. permitted messaging
6. next evidence condition
7. provenance

Provenance must include run id, protocol version, dataset version, review/decomposition mode, and source artifact paths.

---

## README Update Rule

README evidence language must be a strict derivative of `docs/governance_product_note.md`.

Allowed in README:

- bounded headline claim already permitted by governance note
- one-line caveat that claims are scoped to current evidence tier and run protocol

Not allowed in README:

- stronger claims than governance note
- family-specific performance claims absent from current run artifacts

Additional guardrail:

- Development-only runs are not sufficient for public evidence claims.
- Public-facing evidence updates require holdout-backed scope (`holdout` or labeled `synthesis`).

---

## Operational Checklist

1. Select one source run and scope (`development`, `holdout`, or explicitly labeled synthesis).
2. Decide whether the run is canonical ladder, decomposition experiment, family-focused validation, or dry plumbing check.
3. Freeze artifact list and load required files.
4. For ladder work, persist rung label and route setup in the ladder manifest.
5. Build `docs/governance_note_inputs.json`.
6. Render `docs/governance_product_note.md` from inputs.
7. Update README evidence text only if it remains within governance-permitted messaging.
8. Verify provenance footer is present.
9. Record run_id and artifact paths in commit message.

---

## Legacy Script Note

The historical decomposition script used two calls (`development` then `holdout`) by design. This is valid evaluation behavior; it must be documented as split-labeled evidence and not merged into unlabeled global claims.
