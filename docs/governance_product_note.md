# Governance and Product Note

Status: current  
Last updated: 2026-03-21  
Scope: permitted messaging, evidence boundary, and product positioning

---

## Public summary

Symposia is a committee-based judgement system for trust-sensitive questions.

Current evidence supports a bounded claim:

- mixed-family committees help on forecast-style claims
- are neutral on clear factual claims
- and can be harmful on underspecified policy claims

This means committee value is claim-structure-dependent, not universal.

Use this document as the canonical source for what can and cannot be claimed publicly.

---

## What Symposia is

Symposia brings plural judgement, visible dissent, and traceable adjudication to trust-sensitive questions.

It is a structured committee judgement engine — not a universal validation oracle, not a single-model wrapper, and not a truth machine.

The product value is in the *structure* of judgement: plurality, independence, auditability, and escalation discipline.

---

## What the evidence currently supports

### Confirmed positive case

**Mixed-family committee diversity improves judgement quality on forecast-style claims.**

From controlled decomposition experiments (Step 2 vs Step 3 on the experimental ladder, trust value dataset v2, 2026-03-21):

| Metric | Development | Holdout |
|---|---|---|
| Target match rate (ΔTM) | +0.20 | +0.40 |
| Weighted score (ΔWS) | +0.256 | +0.12 |
| Weighted agreement | -0.267 | -0.267 |

Agreement falls in this slice, but the quality lift is consistent across both splits. In this case, disagreement appears productive rather than noisy.

### Confirmed null case

**Mixed-family committees add no measurable value on clear factual claims.**

`low_risk_clear_factual`: ΔTM = 0.0, ΔWS = 0.0 in development; ΔWS = +0.096 holdout only (no target-match lift). Committees converge to the same output regardless of model family. Diversity adds overhead without adding judgement quality.

### Confirmed harmful case

**Mixed-family committees increase critical dissent without improving judgement on underspecified policy claims.**

`underspecified_legal_policy`: ΔWS = -0.072 (dev), -0.048 (holdout). Critical dissent spikes: +0.200 development, +0.400 holdout. Diversity fragments the committee verdict on questions that lack enough structure for models to disagree productively.

---

## Permitted messaging

### Preferred core claim (accurate and defensible)

> Symposia's mixed-family committee value is claim-structure-dependent. It appears strongest on forecast-style questions, neutral on clear factual questions, and harmful on underspecified policy questions.

### Top-level positioning (always permitted)

> Symposia brings plural judgement, visible dissent, and traceable adjudication to trust-sensitive questions.

### Evidence-backed supporting line (permitted with family scope)

> Current evidence suggests committee diversity is most valuable on forecast-style claims — questions with inferential structure and bounded uncertainty. On those questions, mixed-family committees show consistent target-match and weighted-score lift across development and holdout splits.

---

## Prohibited messaging

The following are not supported by current evidence and must not appear in any external or internal framing:

- "Mixed committees are better than same-family committees in general."
- "More committee disagreement means more reliable output."
- "Committee has been universally proven to outperform single-juror paths."
- "Symposia's committee is always more trustworthy than a single strong model."
- "Diversity improves committee judgement across all claim types."

---

## Boundary conditions

The committee diversity lift is **claim-structure-dependent**:

| Claim type | Committee diversity effect |
|---|---|
| Forecast-style (inferential, bounded uncertainty) | **Positive** — consistent lift, confirmed positive case |
| Clear factual (low ambiguity, well-defined answer) | **Neutral** — no measurable lift, overhead not justified |
| Underspecified policy/legal | **Harmful** — increases dissent without improving quality |
| High-stakes advice | Not yet confirmed either direction |
| Plausible but dangerous recommendations | Not yet confirmed either direction |

Unconfirmed families should not be asserted in either direction.

---

## Evidence tier

Current evidence is **Tier B (silver)**: controlled decomposition run, holdout confirmed, family-scoped, dataset limited (5 cases per family per split). This supports:

- committee opt-in positioning for forecast-style claim domains
- family-scoped diversity claims
- provisional trust thesis positioning

This does not yet support:

- universal committee-default recommendation
- broad institutional superiority claims
- cross-domain generalisation beyond tested families

---

## Next evidence steps

To strengthen claims, the following are the logical next moves (in order):

1. Expand `forecast_style_claim` dataset to ≥25 cases per split (current: 5)
2. Run adjacent inferential families (e.g. ambiguous/mixed-truth) to check if lift pattern extends
3. Complete Step 4 of the ladder (stronger single baseline) to test whether diversity lift survives a stronger single comparator
4. Reach Tier A evidence thresholds (≥100 global, ≥25 per slice) required for stronger product claims

---

## Artifact references

- Focused validation: `artifacts/trust_pipeline_runs/2026-03-21-family-focused-validation/family_lift_and_focused_validation_summary.json`
- Adjacent family replication: `artifacts/trust_pipeline_runs/2026-03-21-adjacent-family-validation/adjacent_family_validation_summary.json`
- Full decomposition: `artifacts/trust_pipeline_runs/2026-03-21-decomposition-v1/`
- Experimental ladder spec: `docs/implementation/22_experimental_ladder_and_testing_revamp.md`
- Safety governance: `docs/implementation/07_safety_governance.md`

For a concise public snapshot, see `docs/benchmark-summary.md`.
