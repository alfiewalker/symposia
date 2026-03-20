"""Next-stage escalation IO aliases.

Kept as a focused module to make escalation handoff contracts discoverable.
"""

from symposia.models.escalation import NextStageReviewInput, NextStageReviewResult

__all__ = ["NextStageReviewInput", "NextStageReviewResult"]
