# Build Phases

## Purpose

This document sequences the Symposia build.

Each phase should be considered complete only when its validation gate passes as defined in `15_testing_strategy.md`.

The phases are designed to avoid two common mistakes:
1. building surface complexity before kernel clarity
2. building clever adaptation before external calibration

## Phase 0 — Reframe and freeze doctrine

### Goal
Lock the conceptual upgrade from the current whitepaper shape to v2.

### Deliverables
- this doc set adopted
- renamed verdict model agreed
- calibration-over-consensus decision agreed
- public API doctrine agreed
- profile and profile-set doctrine agreed

### Exit criteria
- no ambiguity about what Symposia is
- no ambiguity about what the first release is not

---

## Phase 1 — Claim kernel and result model

### Goal
Build the primitives that everything else depends on.

### Deliverables
- `ClaimBundle`
- `Subclaim`
- `ValidationResult`
- `CompiledSubclaimVerdict`
- deterministic verdict schema

### Exit criteria
- compound content decomposes reasonably
- output contract is stable

### Do not build yet
- adaptive juror learning
- multi-round open debate

---

## Phase 2 — Profile model and resolution

### Goal
Make juror variation explicit without exposing complexity on the surface.

### Deliverables
- `Profile` object
- `ProfileSet` object
- default registry
- domain default resolution
- profile-set identifier in result metadata

### Exit criteria
- `domain -> default profile set` works deterministically
- one named profile set can be selected explicitly
- profile overlays resolve safely

### Do not build yet
- custom marketplace of community profile packs
- per-juror public customisation in the main API

---

## Phase 3 — Round 0 adjudication engine

### Goal
Build the independent first-pass engine.

### Deliverables
- juror interface
- cohort orchestration from a resolved profile set
- hidden binary tests
- weighted aggregation
- early stop rules

### Exit criteria
- one request can run through Round 0 end to end
- verdict compilation works without escalation

---

## Phase 4 — Trace and observability

### Goal
Make runs inspectable.

### Deliverables
- event log
- trace model
- trace export
- run metadata
- source references
- profile-set metadata in trace

### Exit criteria
- every run can be replayed conceptually from its trace
- failures are diagnosable

---

## Phase 5 — Escalation engine

### Goal
Add one targeted challenge round.

### Deliverables
- escalation trigger rules
- disputed subclaim selection
- challenge packet generation
- final re-aggregation

### Exit criteria
- disputed runs can escalate cleanly
- rounds remain bounded

### Do not build yet
- arbitrary debate loops
- social chat between jurors

---

## Phase 6 — Domain profile sets

### Goal
Make the same kernel usable in real domains.

### Deliverables
- `general_default_v1`
- `medical_strict_v1`
- `legal_strict_v1`
- `finance_strict_v1`
- per-domain issuance and caveat policy wiring

### Exit criteria
- profile-set-specific behaviour works
- high-risk examples behave conservatively
- library remains simple at Level 1 and Level 2 usage

---

## Phase 7 — Calibration registry

### Goal
Earn the right to weight jurors credibly.

### Deliverables
- benchmark schema
- seed set loader
- calibration store
- effective weight computation
- scorecard generation
- profile-set-specific evaluation slices

### Exit criteria
- weights come from external calibration snapshots
- production runs can select a snapshot

### Do not build yet
- live online learning from consensus alignment

---

## Phase 8 — Evaluation harness

### Goal
Prove that the committee helps.

### Deliverables
- single-model baseline runner
- unweighted committee runner
- calibrated committee runner
- regression benchmark suite
- error analysis notebook or report flow
- comparison by profile set

### Exit criteria
- you can compare releases and profile sets cleanly
- committee gains are measured, not assumed

---

## Phase 9 — Minimal polished library release

### Goal
Ship a clean open-source or internal package.

### Deliverables
- slim public API
- strong README
- examples
- stable types
- versioned docs
- benchmark summary
- clear profile-set guidance

### Exit criteria
- a new user can get value quickly
- a serious user can choose a named profile set easily
- an expert can inspect methodology and trace

---

## Phase 10 — Institutional hardening

### Goal
Prepare for serious external credibility.

### Deliverables
- policy registry
- stricter governance controls
- release scorecards
- incident process
- audit-oriented reporting
- profile-set release discipline

### Exit criteria
- domain deployments are governed, not improvised

---

## What should wait until later

Push these out unless they become absolutely necessary:
- marketplace of juror types
- complex reputation economies
- more than two rounds by default
- fancy public dashboards before score quality is proven
- sprawling public API surface

## Recommended implementation order

1. doctrine
2. primitives
3. profile model
4. Round 0 engine
5. trace
6. escalation
7. domain profile sets
8. calibration
9. evaluation
10. release
11. hardening

## Principle

Build the adjudication kernel first. Build the profile model early. Keep both more sophisticated than the public API.
