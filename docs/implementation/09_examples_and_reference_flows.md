# Examples and Reference Flows

## Purpose

This document shows how Symposia should behave on representative inputs.

## Notebook references

- `../../examples/getting_started.ipynb`
- `../../examples/single_vs_committee_use_cases.ipynb`

## Example 1 — Medical emergency advice

### Input
"If you're experiencing chest pain, shortness of breath, and dizziness, these could be signs of a heart attack. You should immediately call 911 or go to the nearest emergency room. While waiting for help, chew an aspirin if you're not allergic, and try to stay calm. Don't drive yourself to the hospital."

### Claim bundle
- symptoms may indicate heart attack
- seek emergency help immediately
- chew aspirin if not allergic
- do not self-drive
- use the correct emergency number for the jurisdiction

### Likely output
- verdict: `validated_with_caveats`
- certainty: `high`
- issuance: `issue_with_caveats`
- risk: `high`
- profile set used: `medical_strict_v1`

### Why
The advice is broadly supported, but:
- aspirin is conditional
- emergency number is jurisdiction-sensitive
- this is high-risk medical content

## Example 2 — Legal procedural statement

### Input
"In France, an employer can dismiss an employee immediately without any formal process."

### Claim bundle
- immediate dismissal without formal process is permitted
- jurisdiction is France
- no process is required

### Likely output
- verdict: `rejected`
- certainty: `moderate` or `high`
- issuance: `requires_expert_review`
- risk: `high`
- profile set used: `legal_strict_v1`

### Why
The statement is over-broad and likely contradicted by procedural requirements.

## Example 3 — Finance claim

### Input
"Company X doubled revenue last year, therefore the stock is a buy."

### Claim bundle
- Company X doubled revenue last year
- doubling revenue implies buy recommendation

### Likely output
- factual subclaim may be `validated`
- recommendation subclaim likely `rejected` or `contested`
- overall issuance likely `requires_expert_review`
- profile set used: `finance_strict_v1`

### Why
A factual validation does not automatically justify an investment recommendation.

## Example 4 — General factual claim

### Input
"The Eiffel Tower is in Berlin."

### Likely output
- verdict: `rejected`
- certainty: `high`
- issuance: `safe_to_issue`
- risk: `low`
- profile set used: `general_default_v1`

## Example 5 — Incomplete claim

### Input
"This new treatment is proven to work."

### Likely output
- verdict: `insufficient`
- certainty: `low`
- issuance: `requires_expert_review`
- risk: `medium` or `high`

### Why
The claim is under-specified:
- what treatment?
- for what condition?
- what evidence?

## Usage pattern examples

### Level 1 — simplest use

```python
from symposia import Symposia

sp = Symposia()
result = sp.validate(content="The Eiffel Tower is in Berlin.", domain="general")
```

Expected behaviour:
- default domain profile set resolves automatically
- caller does not think about jurors

### Level 2 — reproducible serious use

```python
sp = Symposia(profile_set="medical_strict_v1")
result = sp.validate(content="...", domain="medical")
```

Expected behaviour:
- profile-set choice is explicit
- run metadata includes `profile_set_used`

### Level 3 — advanced customisation

```python
result = sp.validate(
    content="...",
    domain="medical",
    profile_set="medical_strict_v1",
    profile="risk_sentinel_v1",
)
```

Expected behaviour:
- customisation remains bounded
- the committee still behaves like a coherent profile set, not a random assortment

## Reference flow

1. request received
2. profile set resolved
3. claim bundle built
4. evidence pack attached
5. Initial jurors run
6. aggregate and evaluate stop rules
7. if needed, escalate disputed subclaims
8. compile verdict
9. return result and optional trace
