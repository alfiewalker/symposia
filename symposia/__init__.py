"""Symposia package root.

Primary day-one surface is intentionally tiny:
    - validate(...)
    - load_profile_set(...)

Advanced internals remain importable by module path.
"""

from symposia.api import load_profile_set, validate
from symposia.models import (
    CompletionDecision,
    InitialReviewResult,
    JurorDecision,
    Risk,
    SubclaimDecision,
)
from symposia.round0 import InitialReviewEngine

__version__ = "0.1.1"
__author__ = "Symposia Team"

__all__ = [
    "validate",
    "load_profile_set",
    "InitialReviewEngine",
    "JurorDecision",
    "SubclaimDecision",
    "CompletionDecision",
    "Risk",
    "InitialReviewResult",
]