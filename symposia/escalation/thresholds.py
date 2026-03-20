"""Shared escalation threshold constants.

These are TEMPORARY OPERATIONAL VALUES used by both the escalation planner
and the challenge review engine to ensure the two components apply identical
pass/fail criteria.  A subclaim is "resolved" after challenge review when
it no longer triggers any of these thresholds.

CRITICAL: editing any value here is a **cross-phase semantic change**.
  - Escalation (Phase 5) and resolution (Phase 6) both depend on these values.
  - Changing a threshold changes what gets escalated AND what counts as resolved.
  - Required steps before changing:
      1. Update locked fixture expectations in tests/fixtures/.
      2. Re-run the full Phase 5+6 test suite.
      3. Document the change reason in the commit message.
  - Never change a threshold to pass a single failing test.
"""
from __future__ import annotations

# Issue thresholds: subclaim scores that trigger an escalation/unresolved entry.
SUPPORT_FLOOR: float = 0.70          # below this → LOW_SUPPORT / unresolved
CONTRADICTION_CEILING: float = 0.35  # at or above → MATERIAL_CONTRADICTION / unresolved
SUFFICIENCY_FLOOR: float = 0.70      # below this → LOW_SUFFICIENCY / unresolved

# Dissent severity: fraction of contradicting jurors among all jurors.
DISSENT_CRITICAL_RATIO: float = 0.40   # at or above → CRITICAL
DISSENT_MATERIAL_RATIO: float = 0.20   # at or above → MATERIAL (else MINOR)
