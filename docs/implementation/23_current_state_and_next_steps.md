# 23 — Current State and Next Steps

Status: current  
Date: 2026-03-21  
Purpose: one-page cycle-close note — what is proven, what is bounded, what is open, and what to do next

---

## What is proven

**Mixed-family committee diversity improves judgement quality on forecast-style claims.**

From Step 2 vs Step 3 on the experimental ladder (trust value dataset v2, 2026-03-21):

| Metric | Development | Holdout |
|---|---|---|
| Target match (ΔTM) | +0.20 | +0.40 |
| Weighted score (ΔWS) | +0.256 | +0.12 |

This is Tier B evidence (5 cases per family per split, holdout confirmed). It supports:
- family-scoped diversity claims on forecast-style questions
- committee opt-in positioning for that domain type

---

## What is bounded

- Committee diversity value is **claim-structure-dependent**. It does not generalise across claim families.
- Mixed-family committees are **neutral** on clear factual claims and **harmful** on underspecified policy claims.
- Same-family plurality (Step 1 vs Step 2) has not been formally isolated. The plurality effect is currently unconfirmed with weak jurors.
- Current evidence tier is **Tier B** throughout — dataset too small for Tier A claims. No broad deployment decisions are warranted.
- The single juror remains the default live path. Committee is experimental and opt-in.

---

## What remains open

1. **Step 1 vs Step 2 not run.** Single weak juror vs same-family committee. This is the foundational plurality test and must be resolved before advancing further.
2. **Same-family plurality may be null** with current weak-model setup. Needs formal confirmation.
3. **Step 4 (stronger single baseline) not yet run.** Diversity lift confirmed at Step 3 may not survive a strong single comparator.
4. **Dataset needs expansion.** Tier A thresholds: ≥25 cases per family per split. Current: 5.
5. **Adjacent family replication** (ambiguous/mixed-truth families) has not been run. Forecast-style lift may or may not extend to adjacent inferential structures.
6. **Live committee path** remains experimental. Not wired for escalation. Performance at scale is unknown.

---

## System state at cycle close

- **Test suite**: 228 tests, 0 failures. Marker-partitioned (core / ladder / legacy). CI runs `python -m pytest -m "core or ladder"`.
- **Docs**: README, governance note, benchmark summary, and ladder doc all reflect current evidence boundary.
- **Public messaging**: governed by `docs/governance_product_note.md`. All claims are claim-structure-scoped.
- **Codebase**: stable. Public API surface is small and intentional. Live path wired behind `live=True`.
- **Theoretical foundations**: Condorcet (plurality), Cooke (calibration), GRADE/RAND (evidence judgement), NIST (governance) — now named explicitly in README and methodology doc.

---

## Next rung to run

**Step 1 vs Step 2: single weak juror vs same-family committee of weak jurors.**

This is the required next run under the ladder.

Steps before running:
1. Preregister with protocol v2 format
2. Define a `step1_vs_step2` dataset slice (minimum 10 forecast-style cases per split, ideally 25)
3. Confirm provider readiness for all slots
4. Run. Interpret against the preregistered expectation.
5. Update governance note and this doc with findings.

Do not run Step 4 or adjacent families until Step 1 vs Step 2 is resolved.
Do not start a new run without preregistration.

---

## Stop condition for this cycle

This cycle is closed. The next action is a commit, not an experiment.
