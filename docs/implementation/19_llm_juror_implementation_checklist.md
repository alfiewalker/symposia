# 19_llm_juror_implementation_checklist.md

# LLM Juror Implementation Checklist

## Core rule

No juror output enters aggregation unless it has been parsed into the canonical typed decision object.

---

## 1. Keep one canonical decision schema

- one output schema for all jurors
- profiles may change posture, not output shape
- schema must map directly into the existing typed decision contract

Required fields should include, at minimum:

- supported
- contradicted
- sufficient
- safe_to_issue
- confidence
- reasons
- uncertainty_notes

Sequencing note:

- keep `JurorDecision` contract stable for the first live integration slice
- carry richer explanatory fields (`reasons`, `uncertainty_notes`) in execution metadata/trace first
- promote those fields into canonical typed decision only in a deliberate contract bump

---

## 2. Use native structured output

- prefer provider-native structured output or JSON Schema
- do not rely on “please return JSON” as the contract
- parser should assume machine-readable output, not free-form prose

Sequencing note:

- first integration slice may use strict JSON contract + hardened parser for cross-provider stability
- provider-native structured output should be added provider-by-provider as the next hardening step

---

## 3. Separate responsibilities

Implement four clear layers:

- `JurorPromptBuilder`
- `ProviderAdapter`
- `JurorResponseParser`
- `JurorRunner`

No single class should own all of these concerns.

---

## 4. Keep prompts short and rigid

Every juror prompt should contain only:

- role or posture
- domain framing
- decision criteria
- output schema instruction
- refusal or uncertainty guidance

Do not embed orchestration logic or long history into the juror prompt.

---

## 5. Fail safe

On any of the following:

- timeout
- refusal
- malformed output
- missing fields
- invalid enums
- provider error

degrade to:

- unresolved
- insufficient
- traceable error state

Never silently guess from malformed text.

---

## 6. Credentials handling

Default path:

- environment variables

Advanced path:

- typed provider credentials object or registry

Do not put raw API key strings on the main `validate(...)` surface.

---

## 7. Start with small capable models

Round 0 defaults:

- small capable models
- low latency
- controlled cost

Reserve stronger models for:

- escalation
- unresolved cases
- high-risk cases

---

## 8. Preserve diversity without breaking the contract

Vary where useful:

- profile posture
- model family
- provider

Keep fixed:

- output schema
- adjudication task
- aggregation contract

---

## 9. Harden the parser before widening provider support

Create locked fixtures for:

- valid JSON
- near-valid JSON
- missing fields
- invalid enum values
- refusal output
- truncated output
- provider error payloads

The parser fixture suite is a phase gate.

---

## 10. Record execution metadata per juror

Trace each juror run with:

- provider
- model
- profile
- latency
- token usage if available
- parse success or failure
- fallback used
- final typed decision

---

## 11. Enforce routing and key rules

- default OpenAI-first mode without OpenAI key must fail fast
- `model="provider:model"` requires matching provider key
- `routing=...` requires credentials for all providers referenced
- `routing` combined with `model` or `escalation_model` must raise a clear error

---

## 12. Keep the first live slice narrow

First live integration should be:

- one provider
- one model family
- 3 to 4 profiles
- strict schema
- parser fixtures
- timeout handling
- end-to-end trace

Do not start with full provider diversity.

---

## 13. Required tests

### Contract tests
- typed decision schema is stable
- parser output maps cleanly into typed models

### Parser tests
- malformed outputs reject cleanly
- refusal handling works
- truncation handling works

### Failure tests
- one failed juror does not crash the run
- partial committee still aggregates
- trace captures the failure cause

### Live smoke tests
- one live juror
- one multi-juror run
- one run per domain slice

### Benchmark tests
- single-juror baseline
- committee path
- malformed-output rate
- latency
- cost
- false escalation
- missed escalation

---

## 14. Naming guidance

Recommended internal names:

- `LLMJuror`
- `JurorPromptBuilder`
- `JurorResponseParser`
- `JurorExecutionRecord`
- `ProviderErrorRecord`

Use ontology names, not build-phase names.

---

## 15. Done criteria

The phase is not complete merely because a model call works.

Completion requires:

- live LLM jurors running through the current adjudication core
- structured outputs parsed into canonical typed decisions
- safe failure handling
- traceable per-juror execution records
- a small live benchmark slice showing actual behaviour

---

## 16. Build order

1. decision schema
2. prompt builder
3. provider adapter
4. parser plus malformed fixtures
5. juror runner
6. multi-juror execution
7. failure handling
8. live benchmark slice
