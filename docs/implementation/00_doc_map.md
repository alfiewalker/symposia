# Document Map

This is the master map for the Symposia doc set.

## Core docs

### 1. `01_why_what_how.md`
Use this to explain Symposia in one sitting:
- why the product should exist
- what it is
- how it works

### 2. `02_methodology_v2.md`
The doctrinal heart of the system:
- Condorcet spirit
- calibrated jurors
- evidence grading
- escalation rules
- verdict compilation

### 3. `03_system_spec.md`
The detailed build spec:
- modules
- interfaces
- entities
- request lifecycle
- algorithms
- persistence
- trace model
- domain handling

### 4. `04_library_api.md`
The library surface doctrine:
- the public API should be small
- advanced capability should stay behind configuration and profiles
- outputs should be stable, typed, and auditable

### 5. `13_profile_sets.md`
Defines the profile model in build-up order:
- why profiles exist
- what a single profile is
- what a profile set is
- default domain sets
- how the library uses and exposes them
- how advanced users author custom sets

### 6. `14_profile_selection_strategy.md`
Bridge document for the next abstraction layer:
- why assuming the right profile set at call time is acceptable but not ideal
- fixed selection vs inferred selection vs dynamic synthesis
- the recommended first selector shape: one bounded LLM routing call to a fixed registry
- what should stay invariant in the adjudication core
- the recommended build order
- how to preserve API simplicity while increasing intelligence

### 7. `05_verdict_schema.md`
Defines:
- verdict classes
- certainty
- issuance
- risk
- disagreement and dissent rules

### 8. `06_calibration_and_evaluation.md`
Defines:
- calibration registry
- seed sets
- benchmark strategy
- weight updates
- success metrics

### 9. `07_safety_governance.md`
Defines:
- high-stakes rules
- domain boundaries
- human review thresholds
- trace and audit requirements
- governance posture

### 10. `08_build_phases.md`
The execution roadmap:
- phase sequence
- deliverables
- exit criteria
- what not to build too early

## Supporting docs

### 11. `09_examples_and_reference_flows.md`
Concrete examples:
- medical
- legal
- finance
- generic factual validation
- profile-set usage patterns

### 12. `10_repo_structure.md`
Recommended package and repository shape.

### 13. `11_open_questions_and_adrs.md`
Major decisions still to settle before or during build.

### 14. `12_glossary.md`
Terminology.

## Minimal set if time is short

If you had to keep only six docs:
1. `README.md`
2. `01_why_what_how.md`
3. `02_methodology_v2.md`
4. `03_system_spec.md`
5. `04_library_api.md`
6. `08_build_phases.md`

## Best-in-class set

For a serious open-source or institution-facing build, keep all of them and treat `13_profile_sets.md` and `14_profile_selection_strategy.md` as first-class design docs rather than appendices.

## 15. Testing strategy

`15_testing_strategy.md` defines the layered testing doctrine for Symposia:
- deterministic core tests
- contract tests
- golden tests
- benchmark and calibration tests
- safety and adversarial tests
- release gates

It also defines phase-level validation gates so each build phase can be considered complete in a disciplined way.
