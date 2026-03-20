# Phase 0.5 Locks

This directory contains immutable lock artifacts for early rebuild phases.

## Lock Policy

1. These files are the canonical fixtures for Phases 1 to 3.
2. Phases 1 to 3 cannot pass major gates without testing against these locks.
3. Changes to lock files require explicit verifier approval and lock version bump.
4. Lock modifications must include rationale and provenance updates in the same change set.

## Artifacts

- golden_cases.jsonl
  - representative expected-behavior cases across domains
- safety_slices.jsonl
  - high-risk/adversarial slices for conservative behavior checks
- baseline_cases.jsonl
  - baseline superiority checks where committee must be greater than or equal to single-juror baseline
- trace_snapshots/
  - minimal trace schema and sample snapshots for Phase 3 contract checks

## JSONL Schema Conventions

Each line is one JSON object.

Common fields:
- case_id: stable case identifier
- domain: general, medical, legal, finance
- content: input text to validate
- tags: category labels
- lock_version: fixture lock version

## Required Gate Rule

Nothing in Phases 1 to 3 moves unless it is tested against these locked fixtures.

## Suggested Validation Commands

Example command shape (to be wired as implementation lands):

- validate golden cases and assert expected verdict class behavior
- validate safety slices and assert conservative issuance behavior
- compare committee versus single-juror on baseline cases
- validate Phase 3 trace output against trace_snapshots/schema_v1.json
