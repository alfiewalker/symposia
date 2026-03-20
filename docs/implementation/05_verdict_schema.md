# Verdict Schema

## Purpose

This document defines the public output language of Symposia.

A strong verdict system must be:
- simple enough for callers
- precise enough for institutions
- domain-neutral at the top level
- domain-aware in caveats and issuance

## Top-level verdicts

Use four top-level verdicts:

- `validated`
- `rejected`
- `insufficient`
- `contested`

This is the public vocabulary.

## Definitions

### `validated`
The committee finds the content or claim sufficiently supported to rely on under the current evidence and profile rules.

### `rejected`
The committee finds the content materially contradicted, misleading, or unsupported to the degree that it should not be relied on.

### `insufficient`
The committee cannot reach a supportable decision because evidence, clarity, or coverage is inadequate.

### `contested`
The committee sees real support and real dispute that cannot be cleanly resolved under the current run conditions.

## Verdict modifiers

To preserve simplicity, modifiers should be additive, not alternative verdict classes.

Examples:
- `validated_with_caveats`
- `validated_high_risk`
- `rejected_high_confidence`
- `insufficient_due_to_missing_evidence`

## Certainty

Separate from verdict.

Allowed values:
- `high`
- `moderate`
- `low`
- `very_low`

## Issuance

Also separate from verdict.

Allowed values:
- `safe_to_issue`
- `issue_with_caveats`
- `requires_expert_review`
- `unsafe_to_issue`

## Risk

Allowed values:
- `low`
- `medium`
- `high`

## Agreement

Agreement should be numeric and interpretable:
- value in `[0, 1]`
- based on weighted support cohesion, not raw vote count alone

## Dissent

Dissent should be structured, not merely a text blob.

Suggested structure:

```json
{
  "severity": "minor | material | critical",
  "summary": "string",
  "subclaims": ["sc_1", "sc_2"]
}
```

## Subclaim verdicts

Each subclaim should also receive:
- verdict
- certainty
- issuance
- risk
- caveats
- agreement

## Overall verdict compilation

The whole answer should not be a naive majority of subclaim verdicts.

Suggested rules:
- if any critical actionable subclaim is rejected, overall issuance may need to degrade
- if any high-risk subclaim is insufficient, overall verdict may remain validated but issuance becomes `requires_expert_review`
- if one core premise fails, dependent conclusions may not be marked validated

## Domain examples

### Medical
A paragraph may be:
- validated
- certainty: high
- issuance: issue_with_caveats
- risk: high

### Legal
A paragraph may be:
- validated
- certainty: moderate
- issuance: requires_expert_review
- risk: high

### Finance
A statement may be:
- validated
- certainty: moderate
- issuance: issue_with_caveats
- risk: medium

## Design principle

Verdict answers:
- what is the status?
- how sure are we?
- can it be issued?
- how risky is it?
- what caveats matter?

That is the public contract.
