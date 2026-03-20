"""Escalation contract module.

This module intentionally holds only contract-level construction logic,
without introducing debate loops or additional adjudication strategies.
"""

from symposia.escalation.planner import plan_escalation

__all__ = ["plan_escalation"]
