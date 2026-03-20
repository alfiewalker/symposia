# Open Questions and ADR Seeds

## Purpose

These are the highest-value decisions still to settle.

## 1. How should claim decomposition be done?

Options:
- LLM-driven extraction only
- rules + LLM hybrid
- domain profile specific extractors

Recommendation:
Start with a hybrid. Pure LLM extraction is too unconstrained.

## 2. How should certainty be computed?

Options:
- directly from aggregated juror confidence
- from evidence quality + agreement + calibration
- profile-dependent composite score

Recommendation:
Use a composite, not a raw average confidence.

## 3. Should jurors abstain?

Recommendation:
Yes. Abstention is useful signal, especially for insufficiency.

## 4. How much role diversity should be exposed publicly?

Recommendation:
Little to none at the top-level API. Keep role diversity as an internal profile or advanced configuration concern.

## 5. Should users provide domain explicitly?

Recommendation:
Yes for v1. Automatic classification may be added later, but explicit domain is cleaner and safer.

## 6. How should evidence be supplied?

Recommendation:
Support:
- caller-supplied evidence
- retrieval-backed evidence
- hybrid

Keep it explicit in the trace.

## 7. Should calibration weights ever update online?

Recommendation:
Not by default. Use offline snapshots first.

## 8. Should there be more than one escalation round?

Recommendation:
Not by default. One challenge round is enough for the first serious version.

## 9. How much internal reasoning should be surfaced?

Recommendation:
Expose structured rationale summaries, not sprawling raw internal material.

## 10. What is the initial brand promise?

Recommendation:
Do not promise absolute truth.
Promise:
- validated support status
- explicit caveats
- auditable committee reasoning

## Suggested ADR list

Create ADRs for:
- public verdict vocabulary
- calibration weighting model
- claim decomposition strategy
- escalation policy
- trace retention policy
- domain profile strategy
- evidence adapter strategy
