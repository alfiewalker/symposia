# Sprint Board — Phases 1 to 3

## Purpose

This sprint board operationalizes the rebuild roadmap with tighter early gates.

It incorporates:
- Phase 0.5 fixture and benchmark lock
- dual verifier function (build gatekeeper and methodology auditor)
- minimal trace contract in Phase 3
- parity checklist before deleting legacy voting strategy code
- baseline-superiority gate
- fixed-registry profile rule before any dynamic profile selection work

This board is aligned with:
- 08_build_phases.md
- 15_testing_strategy.md
- 06_calibration_and_evaluation.md
- 10_repo_structure.md

## Post-Release Priority Note

First substantial post-release architecture stream:
- externalise profile sets and defaults to YAML-backed typed config

Scope boundary for this stream:
- move policy (profile-set ids, included profiles, thresholds, domain defaults, registry mapping)
- keep behaviour in code (ProfileBehavior semantics, hint activation logic, juror decision mechanics)

## Global Build Rules

1. One major gate per iteration, with minor internal gates allowed.
2. No dynamic profile generation before fixed-registry profile selection is benchmarked and accepted.
3. Wave A deletions are blocked until parity checklist passes.
4. Phase 3 must emit minimal trace fields even before full tracing/export work.
5. Baseline-superiority gate applies at defined checkpoints.

## Verifier Model

Verifier function has two mandatory duties.

### A. Build Gatekeeper
Checks:
- deterministic tests
- contract tests
- regression status
- parity checklist status
- release of deletion blockers

### B. Methodology Auditor
Checks:
- implementation conforms to rebuild doctrine docs
- no drift from calibration-over-consensus principle
- no API creep beyond Level 1 and Level 2 simplicity doctrine
- no premature dynamic profile generation
- verdict and issuance semantics stay aligned with schema doctrine

A single verifier agent may perform both functions, but both reports are required at each major gate.

## Phase 0.5 — Fixtures and Benchmark Lock

## Goal
Freeze evaluation anchors before parallel implementation begins.

## Deliverables
1. Golden example lock file
- location: benchmarks/locks/golden_cases.jsonl
- contains domain-tagged representative examples and expected high-level outcomes

2. Seed benchmark slice lock file
- location: benchmarks/locks/baseline_cases.jsonl
- contains baseline comparison slices where committee must be greater than or equal to single-juror baseline

3. Safety slice lock file
- location: benchmarks/locks/safety_slices.jsonl
- contains adversarial and high-risk slices for medical, legal, finance

4. Trace snapshot contract lock
- location: benchmarks/locks/trace_snapshots/
- defines required minimal trace keys and stable field names via schema and snapshot examples

## Major Gate 0.5
Pass only if:
- all four lock files exist and are versioned
- verifier gatekeeper confirms immutability policy and schema checks
- methodology auditor confirms locked fixtures reflect doc doctrine

## Minor Internal Gates 0.5
- lock schema validation pass
- duplicate fixture detection pass
- provenance metadata completeness pass

---

## Iteration 1 — Phase 1 Foundation

## Scope
Phase 1 claim kernel and result model.

Start condition:
- Phase 0.5 major gate is green.

## Workstreams
1. Kernel stream
- implement ClaimBundle and Subclaim model set
- implement deterministic decomposition interface and first extractor behavior

2. Result schema stream
- implement ValidationResult and CompiledSubclaimVerdict contract
- implement verdict, certainty, issuance, risk enums

3. Contracts and tests stream
- deterministic model serialization tests
- schema contract tests
- decomposition stability tests

## Major Gate 1
Pass only if:
- phase 1 exit criteria in 15_testing_strategy are met for Phase 1
- deterministic core tests pass
- contract tests pass
- methodology auditor signs schema and naming alignment

## Minor Internal Gates 1
- model serialization round-trip gate
- decomposition invariants gate
- enum completeness gate

## Required Evidence
- test report bundle
- schema examples for each verdict class
- phase audit note from methodology auditor

---

## Iteration 2 — Phase 2 Foundation

## Scope
Phase 2 profile model and resolution.

## Workstreams
1. Profiles stream
- implement Profile registry and built-in profile definitions

2. Profile sets stream
- implement ProfileSet registry and domain defaults

3. Resolution stream
- implement deterministic domain to default profile set resolution
- implement explicit named profile set selection
- implement safe profile overlay resolution

4. Contracts and tests stream
- registry load and lookup tests
- fallback behavior tests
- invalid reference safety tests

## Major Gate 2
Pass only if:
- phase 2 exit criteria in 15_testing_strategy are met for Phase 2
- default resolution deterministic across domains
- methodology auditor confirms no dynamic generation behavior
- fixed-registry selection benchmark slice is executed and documented

## Minor Internal Gates 2
- registry integrity gate
- overlay conflict resolution gate
- backward schema tolerance gate

## Required Evidence
- resolution matrix by domain
- invalid-config behavior report
- methodology compliance note

---

## Iteration 3 — Phase 3 Round 0 Engine

## Scope
Phase 3 independent adjudication engine with minimal trace.

## Workstreams
1. Juror orchestration stream
- juror interface and cohort orchestration from resolved profile set
- round 0 execution over subclaims

2. Aggregation stream
- weighted support logic
- contradiction logic
- sufficiency logic including abstention handling
- deterministic tie behavior
- threshold and early-stop behavior

3. Minimal trace stream
Phase 3 minimum required trace output keys:
- run_id
- profile_set_selected
- subclaims
- juror_votes
- aggregation_outcome

4. Tests and benchmark stream
- deterministic aggregation tests
- round 0 integration tests
- baseline comparison tests on locked slice

## Major Gate 3
Pass only if:
- phase 3 exit criteria in 15_testing_strategy are met for Phase 3
- minimal trace contract keys are emitted and validated
- parity checklist passes
- baseline-superiority gate passes on relevant locked slice

## Minor Internal Gates 3
- weighted vote and threshold gate
- abstention and insufficient handling gate
- deterministic tie behavior gate
- minimal trace schema gate

## Required Evidence
- round 0 end-to-end test report
- minimal trace samples from locked fixtures
- baseline comparison report on locked slice
- methodology audit note

---

## Baseline-Superiority Gate Definition

At designated checkpoints, require:
- committee performance greater than or equal to single-juror baseline
- evaluated on relevant locked benchmark slice
- with no material regression on locked safety slice

For Phase 3 this gate is required and blocking.

## Parity Checklist for Wave A Deletion

Wave A candidate deletions:
- strategies package and strategy tests

Deletion is allowed only if all checklist items pass:
1. Weighted voting parity
- new round 0 aggregation reproduces weighted influence behavior

2. Threshold parity
- support and contradiction thresholds are enforced deterministically

3. Abstention and insufficiency parity
- abstentions map to insufficient evidence behavior without silent promotion to validated

4. Deterministic tie behavior parity
- ties resolve by documented deterministic rule

5. Traceability parity
- minimal trace captures enough data to explain each outcome

6. Benchmark parity
- no regression against locked benchmark slice beyond agreed tolerance

7. Safety parity
- no worsening on locked safety slices

## Major Deletion Gate A
Only after the parity checklist passes and both verifier functions sign off.

---

## Agent Assignment Model for Phases 1 to 3

1. Kernel Specialist
- owns claim and result primitives in Iteration 1

2. Profile Specialist
- owns profile and profile-set model in Iteration 2

3. Adjudication Specialist
- owns round 0 orchestration and aggregation in Iteration 3

4. Verifier
- produces two reports per major gate:
  - build gatekeeper report
  - methodology auditor report

5. Integration Lead
- resolves cross-stream contract mismatches
- owns gate evidence bundle assembly

## Cadence Pattern

Within each iteration:
1. Day 1 to 2
- contract lock and minor gate definitions finalized

2. Day 3 to 7
- implementation and minor gate checks

3. Day 8 to 9
- integration and verifier dual-report cycle

4. Day 10
- major gate decision and merge or block

## Blockers and Escalation

Block progression immediately if:
- methodology auditor reports doctrine drift
- baseline-superiority gate fails
- minimal trace contract fails in Phase 3
- parity checklist fails for Wave A deletion

Escalation route:
- integration lead triage
- targeted fix sprint
- re-run only affected minor gates plus major gate

## Definition of Ready for Phase 4

Phase 4 may start only after all are true:
- Phase 3 major gate passed
- minimal trace contract is stable
- Wave A deletion decision is explicit (execute or defer with reasons)
- fixed-registry profile selection benchmark report accepted

## Enforcement Reference

For local, CI, and branch protection enforcement of the Phase 0.5 gate, use:
- `docs/implementation/17_branch_protection_checklist.md`
