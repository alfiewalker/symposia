# Profile Set Selection Guide

This guide is for day-one users who just want to choose the right committee profile set.

## Quick Rule

- Use `general_default_v1` for mixed or unknown content.
- Use `medical_strict_v1` for clinical or patient-safety content.
- Use `legal_strict_v1` for regulatory, compliance, or legal interpretation content.
- Use `finance_strict_v1` for investing, portfolio, risk, and financial advice content.

If you are unsure, start with `general_default_v1`.

## Selection Table

| Content type | Recommended profile set | Why |
| --- | --- | --- |
| General factual claims | `general_default_v1` | Balanced default committee for mixed topics. |
| Medical claims | `medical_strict_v1` | Stronger safety and evidence posture for harm-sensitive claims. |
| Legal claims | `legal_strict_v1` | Tighter scrutiny for jurisdiction and legal overclaims. |
| Finance claims | `finance_strict_v1` | Higher caution on guarantees and retirement-risk language. |

## Python Usage

```python
from symposia import validate

result = validate(
    content="Diversification can reduce portfolio volatility over time.",
    domain="finance",
)
print(result.core_trace.profile_set_selected)
```

## Advanced Override

Use `profile_set` only when you want explicit control:

```python
from symposia import validate

result = validate(
    content="Contracts require offer, acceptance, and consideration.",
    domain="legal",
    profile_set="legal_strict_v1",
)
```

## Optional Profile Overlay

You can append one compatible profile with `profile`:

```python
from symposia import validate

result = validate(
    content="This treatment is proven to work for all patients.",
    domain="medical",
    profile="risk_sentinel_v1",
)
```

The overlay is applied only if the profile is domain-compatible and not already present.
