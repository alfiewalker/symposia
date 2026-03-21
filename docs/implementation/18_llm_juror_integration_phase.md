# 18_llm_juror_integration_phase.md

# Phase 11 — Live LLM Juror Integration

## Purpose

Move Symposia from profile-aware simulated jurors to real LLM jurors running inside the existing adjudication core, while preserving:

- the current public API
- the current core contracts
- deterministic trace and evaluation discipline
- narrow, testable phase gates

## Core principle

Keep the kernel. Replace the juror implementation.

Do not redesign the system. Make the existing review flow accept live LLM jurors as first-class participants.

## Done means

At the end of this phase, Symposia can:

1. execute `validate(...)` with live LLM jurors
2. instantiate multiple jurors from one or more providers/models
3. vary jurors by profile prompt and reasoning posture
4. parse structured outputs into existing decision contracts
5. aggregate them through the current initial review flow
6. emit trace with per-juror execution records
7. degrade safely on malformed output, timeout, refusal, or provider failure
8. run a small live benchmark slice across domains

---

## Scope rules

### In scope

- LLM juror adapter
- juror prompt layer
- structured response parser
- live multi-juror execution
- failure handling
- cost and latency controls
- small live benchmark slice

### Out of scope

- dynamic profile generation
- full YAML externalisation of behaviour
- new top-level verbs
- debate theatre / multi-round agent discussion
- live reputation learning
- multi-provider optimisation beyond a narrow first slice

---

## Build order

### Phase 11.1 — LLM juror contract

#### Deliver

A real `LLMJuror` implementation that fits the current juror slot and produces existing decision objects.

#### Input

- subclaim text
- domain
- profile
- selected profile set
- optional context bundle
- output schema contract

#### Output

- `JurorDecision`
- execution metadata for trace
- error state when parsing or provider execution fails

#### Gate

- one live juror can produce a valid `JurorDecision`
- invalid output is rejected cleanly
- trace captures raw response summary and parsed result

---

### Phase 11.2 — Juror prompt layer

#### Deliver

A bounded prompt builder that maps profile and domain into juror instructions.

#### Prompt must include

- role / posture
- decision rules
- domain framing
- output schema
- uncertainty / refusal guidance

#### Constraint

All jurors share the same output schema. Only reasoning posture varies.

#### Gate

At least these profiles produce valid structured output on the same slice:

- `balanced_reviewer_v1`
- `sceptical_verifier_v1`
- `evidence_maximalist_v1`
- one domain specialist

---

### Phase 11.3 — Structured output parser hardening

#### Deliver

A robust parser for LLM juror responses.

#### Must handle

- valid JSON
- near-valid JSON
- missing fields
- invalid enum values
- empty output
- refusal text
- truncated output

#### Failure rule

If parsing fails, the juror result degrades to unresolved / insufficient with a traceable error record.

#### Gate

Locked parser fixture suite exists and passes.

---

### Phase 11.4 — Multi-juror live execution

#### Deliver

Real LLM jurors run through the existing initial review path.

#### Rules

- profile-set driven
- same current aggregation path
- same early-stop logic
- same escalation triggers
- no redesign of adjudication flow

#### Gate

Live end-to-end run succeeds across:

- general
- medical
- legal
- finance

with valid trace output.

---

### Phase 11.5 — Reliability and failure handling

#### Deliver

Operational protections for live juror execution.

#### Required behaviours

- retry policy
- timeout policy
- malformed-response handling
- juror dropout handling
- provider error handling

#### Principle

A failed juror weakens certainty. It must not corrupt or crash the run.

#### Gate

Injected failure tests prove:

- one failed juror does not crash the run
- partial committee still aggregates
- trace records the failure cause

---

### Phase 11.6 — Cost, latency, and concurrency discipline

#### Deliver

Basic execution controls for real-world viability.

#### Required controls

- max juror count
- provider timeout
- concurrency limit
- token budgeting
- rough per-run cost estimate

#### Gate

Documented and tested defaults exist for:

- default juror count
- average latency by domain slice
- approximate cost envelope for one validation run

---

### Phase 11.7 — Live benchmark slice

#### Deliver

A small but serious live evaluation set.

#### Minimum per domain

- 5 to 10 cases
- clear expected direction
- hard negatives
- edge cases
- at least one escalation-worthy case

#### Comparisons

- single LLM juror baseline
- multi-juror committee
- deterministic juror baseline where useful

#### Metrics

- accuracy
- false escalation
- missed escalation
- malformed output rate
- cost
- latency

#### Gate

Produce one human-readable report for the phase.

---

## Architecture constraints

### Keep one adjudication core

Do not fork the system into separate orchestration paths for deterministic and LLM modes. The kernel remains the same; only the juror implementation changes.

### LLMs are jurors, not hidden workflow engines

Each LLM juror performs one bounded review task and returns structured judgement. It must not take over orchestration.

### Model routing is a separate policy layer

Keep profile-set policy separate from model-routing policy.

Routing unit for live jurors should be:
- stage + domain + profile slot -> provider/model assignment

Default posture:
- Round 0 uses small-capable models by default
- premium models are reserved for escalation, high-risk, or unresolved paths

Guardrails:
- no single global model default for all jurors
- fallback route per assignment for provider outage
- premium caps and run-cost caps enforced by typed routing config
- identical output schema across all routing files

### Profiles shape prompts, not schemas

Profile choice should alter posture, scepticism, and evidence demand. It must not alter the contract returned by the juror.

### Safe degradation beats cleverness

Malformed or missing outputs must degrade to safe, traceable states rather than silent corruption.

---

## Recommended internal names

- `LLMJuror`
- `JurorPromptBuilder`
- `JurorResponseParser`
- `JurorExecutionRecord`
- `ProviderErrorRecord`

These names fit the existing ontology and should survive future phases.

---

## Testing doctrine for this phase

### Required test classes

1. contract tests
2. parser fixture tests
3. injected failure tests
4. live smoke tests
5. live benchmark tests
6. trace parity tests

### Non-negotiable rule

Do not call the phase complete merely because live model calls succeed. Completion requires safe failure behaviour, traceability, and benchmark evidence.

---

## Release posture

This phase should end with Symposia being truthfully describable as:

> A validation library whose jurors are real LLMs running through a traceable committee review path.

Until this phase is complete, Symposia should be described as architecturally ready for LLM jurors, but not yet fully validated with them.

---

## Immediate implementation sequence

### Sprint A

## Progress Update (2026-03-21)

Implemented now:
- `LLMJuror` contract primitive with safe degradation on provider and parser failures
- `JurorPromptBuilder` with bounded fixed-schema instruction contract
- `JurorResponseParser` with strict schema checks and near-valid JSON recovery
- phase contract tests for valid parse, near-valid parse, refusal, malformed output, and provider error handling
- Round 0 `juror_mode="llm"` execution path (with deterministic default still `rule_based`)
- per-juror execution metadata in trace votes (`provider_model`, `parsed_ok`, `error_code`)
- deterministic adjudication trace event enrichment for runtime truthfulness:
	- `run_policy_applied`
	- `juror_execution_succeeded`
	- `juror_execution_failed`
	- `run_runtime_stats`
- run-level failure orchestration controls:
	- timeout
	- retries / retry delay
	- max dropout threshold per subclaim

Still pending for full phase completion:
- run live benchmark slice and publish phase report
- widen provider-backed routing beyond the narrow slice
- run and review one real narrow live smoke trace artifact in this environment once credentials are present

Implemented for the next narrow slice:
- routed live-provider service factory for YAML route assignments
- explicit routed juror lineup support in `InitialReviewEngine`
- OpenAI-only `default_round0_openai` route for a four-juror small-capable Round0 slice
- dedicated smoke runner at `examples/openai_round0_live_smoke.py` that exports trace artifacts
- explicit `validate(..., live=True)` path for round0-only live routing or a single explicit live model

- `LLMJuror`
- prompt builder
- parser
- malformed-output fixture suite

### Sprint B

- live multi-juror execution
- trace integration
- failure handling

### Sprint C

- cost / latency controls
- small live benchmark slice
- phase report

---

## Success statement

This phase is successful when Symposia can truthfully claim:

- its jurors are real LLMs
- the committee path runs end to end
- malformed or failed juror responses degrade safely
- live evaluation shows whether the committee adds value
