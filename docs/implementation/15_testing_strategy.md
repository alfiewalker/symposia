# Testing Strategy

## Purpose

This document defines how Symposia proves that each build phase is real, and that the full system is worthy of trust.

The central doctrine is:

1. every phase must have its own validation gate
2. every release must pass a smaller number of heavyweight system validations
3. no single large benchmark should substitute for phase-level correctness

In short:

`phase gates + release validations`, not `one giant test at the end`

---

## Current execution profile (experiment ladder)

Current evidence work is intentionally scoped to the experiment ladder. Day-to-day validation should run the ladder pack first, then expand only when changing non-ladder runtime surfaces.

Ladder pack:

- `tests/test_api_customization_ladder.py`
- `tests/test_juror_routing_yaml.py`
- `tests/test_openai_round0_comparison_runner.py`
- `tests/test_openai_round0_trust_evaluation_runner.py`
- `tests/test_openai_round0_silver_labeling.py`
- `tests/test_protocol_validation.py`
- `tests/test_trust_protocol_validation.py`

Suggested command:

`bash scripts/run_experiment_ladder_tests.sh -q`

Use the full regression suite for release gates and for any changes outside ladder/runtime evaluation paths.

---

## Best-in-class stance

For Symposia, best in class is a layered strategy:

### Layer 1 — Deterministic core tests
Used for the parts that must always behave the same way.

Examples:
- claim decomposition invariants
- verdict compilation rules
- threshold and stopping logic
- profile-set resolution fallbacks
- trace schema generation

These should be fast and exhaustive.

### Layer 2 — Contract tests
Used for stable interfaces.

Examples:
- library API request and response shapes
- profile-set registry loading
- juror adapter interface
- trace export contract
- calibration snapshot loading

These protect simplicity at the surface.

### Layer 3 — Golden tests
Used for controlled representative examples.

Examples:
- known medical examples
- known legal examples
- known finance examples
- known mixed-outcome examples

These verify that real outputs still look right after internal changes.

### Layer 4 — Benchmark and calibration tests
Used to measure whether the committee actually helps.

Examples:
- strongest single-model baseline
- unweighted committee baseline
- calibrated committee comparison
- profile-set comparison
- cost and escalation comparison

This is where reputability is earned.

### Layer 5 — Safety and adversarial tests
Used to probe failure modes.

Examples:
- unsafe medical advice
- jurisdiction traps
- contradictory evidence bundles
- overclaiming prompts
- weak-source contamination

These matter more than pretty averages.

### Layer 6 — Release gates and shadow validation
Used before promotion.

Examples:
- full regression suite
- benchmark delta review
- high-risk slice review
- manual trace inspection on selected runs
- shadow runs against previous release

This is how you avoid shipping a more confident but less safe system.

---

## The right balance

The right answer is **not**:
- only phase validation
- only one large validation at the end

The right answer is:

### During build
Each phase has a clear validation gate.

### Before release
Run a heavier integrated validation pack.

So the structure is:

`local correctness -> phase readiness -> release readiness`

---

## Phase gates

Each build phase should define:
- what is under test
- what must be deterministic
- what can remain heuristic
- what benchmark slice must pass
- what failures block progression

### Phase 0 — Doctrine gate
Pass condition:
- naming and concepts are stable
- no conflicting verdict definitions remain

### Phase 1 — Kernel object gate
Pass condition:
- core types exist
- verdict compilation is deterministic
- compound inputs decompose into stable structures

### Phase 2 — Profile gate
Pass condition:
- fixed registry loads cleanly
- default resolution works
- invalid profile references fail safely

### Phase 3 — Round 0 gate
Pass condition:
- end-to-end independent adjudication works
- early stop rules behave correctly
- trace contains core run metadata

### Phase 4 — Observability gate
Pass condition:
- trace exports are stable
- failure states are diagnosable
- replayability is conceptually possible

### Phase 5 — Escalation gate
Pass condition:
- only disputed runs escalate
- escalation remains bounded
- final verdict remains well-formed

### Phase 6 — Domain profile-set gate
Pass condition:
- domain-specific defaults behave conservatively on high-risk examples
- same API stays simple across domains

### Phase 7 — Calibration gate
Pass condition:
- weights come from versioned external calibration snapshots
- no live consensus-based weight mutation exists in production path

### Phase 8 — Evaluation gate
Pass condition:
- committee performance is measured against baselines
- gains and regressions are visible by domain and profile set

### Phase 9 — Release gate
Pass condition:
- public API stable
- examples work
- docs match behaviour
- benchmark summary attached

### Phase 10 — Institutional gate
Pass condition:
- policy controls exist
- audit artefacts are retained
- high-risk deployment checklist exists

---

## Test categories by component

### Adjudication core
- unit tests
- property tests
- threshold tests
- deterministic fixture tests

### Profiles and profile sets
- registry tests
- fallback tests
- conflict resolution tests
- override tests

### LLM selector (future approved phase)
- routing fixture tests
- structured-output tests
- low-confidence fallback tests
- prompt drift tests

### Juror engine
- adapter contract tests
- timeout tests
- partial failure tests
- concurrency tests

### Verdict compiler
- mapping tests
- caveat propagation tests
- risk flag tests
- contested-vs-insufficient edge tests

### Calibration registry
- snapshot loading tests
- weighting formula tests
- missing-data fallback tests
- version pinning tests

### Trace and observability
- schema tests
- completeness tests
- replay metadata tests
- redaction tests

---

## Recommended benchmark packs

Use at least four benchmark packs:

### 1. Core logic pack
Small, deterministic, synthetic.

Purpose:
- validate invariants
- catch obvious logic regressions quickly

### 2. Golden domain pack
Hand-curated examples.

Purpose:
- protect expected product behaviour
- preserve interpretability and caveat quality

### 3. Calibration pack
Known-answer seed tasks.

Purpose:
- compute and validate juror weights
- compare fixed profile sets

### 4. High-risk stress pack
Adversarial and failure-seeking tasks.

Purpose:
- detect unsafe validation behaviour
- test caveat and escalation discipline

---

## Release criteria

A release should not ship merely because tests are green.

It should ship only if all are true:
- deterministic and contract suites pass
- golden set quality is preserved
- benchmark deltas are acceptable
- high-risk slices do not worsen materially
- trace and audit artefacts are complete

For Symposia, a benchmark win with a safety regression is not a win.

---

## What to measure every release

Minimum release scorecard:
- validated precision
- false validation rate
- insufficiency accuracy
- contested rate
- escalation rate
- high-risk caveat hit rate
- benchmark gain over strongest single model
- benchmark gain over unweighted committee
- cost per run
- median latency per run

---

## Build recommendation

The best build order is:

1. deterministic tests first
2. golden tests second
3. benchmark harness third
4. adversarial pack fourth
5. release gates and shadow validation last

Why this order?
Because without deterministic confidence, benchmark results are too noisy to trust.

---

## Strong guidance

Treat testing as a first-class product asset.

For Symposia, the test system is not a side concern. It is part of the credibility engine.

The best version of Symposia will be able to say:

- why a release is better
- where it is worse
- which profile sets are safer
- which regressions are blocked from shipping

That is best in class.
