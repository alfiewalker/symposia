# 24_decomposition_boundary_note.md

# Decomposition Boundary Note

## Why decomposition was demoted

Symposia moved its default runtime behavior to holistic single-claim review.

Reason:
- naive sentence-level splitting can remove critical context
- dependency-heavy claims can become misleading when split
- distorted subclaims can degrade committee judgment quality

## Current policy

- default: holistic single-claim review (`review_mode=holistic`)
- optional: rule-based decomposition (`review_mode=decomposed`) only when explicitly enabled
- decomposition is experimental and should not be treated as trust-grade default evidence

## When decomposition can still help

Decomposition can still be useful for narrow experiments where:
- the claim is clearly multi-part and low-dependency
- the experiment goal is claim-family analysis rather than product-default behavior
- outputs are explicitly tagged with `review_mode`

## Evidence hygiene rule

Do not mix holistic and decomposed outputs without explicit mode separation in summaries, reports, and governance claims.

## Forward path

Future work can re-introduce decomposition as a stronger candidate only if a dependency-aware, LLM-assisted decomposition method demonstrates stable gains on holdout trust metrics without context distortion.
