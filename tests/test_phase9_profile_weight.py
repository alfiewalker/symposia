"""Phase 9 — Profile.weight parity tests.

Three groups:
  A. Direct field assertions: every BUILTIN_PROFILE has the expected weight.
  B. Numeric parity: aggregate_round0 scores match values computed from the
     old substring-matching table for the same profile IDs.
  C. Registry shim: _profile_weight falls back to 1.0 for unknown IDs and
     raises nothing.
"""
from __future__ import annotations

import pytest

from symposia.aggregation.round0 import _profile_weight, aggregate_round0
from symposia.models.juror import JurorDecision
from symposia.profiles import get_profile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OLD_WEIGHT_TABLE = {
    "risk_sentinel_v1": 1.2,
    "evidence_maximalist_v1": 1.1,
    "medical_specialist_v1": 1.15,
    "legal_specialist_v1": 1.15,
    "finance_specialist_v1": 1.15,
    "sceptical_verifier_v1": 1.05,
    "balanced_reviewer_v1": 1.0,
    "literal_parser_v1": 1.0,
}


def _decision(
    profile_id: str,
    *,
    supported: bool = True,
    contradicted: bool = False,
    sufficient: bool = True,
    issuable: bool = True,
    sub: str = "s1",
) -> JurorDecision:
    return JurorDecision(
        juror_id=f"j_{profile_id}",
        profile_id=profile_id,
        subclaim_id=sub,
        supported=supported,
        contradicted=contradicted,
        sufficient=sufficient,
        issuable=issuable,
        confidence=0.9,
    )


# ---------------------------------------------------------------------------
# Group A — direct field assertions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile_id,expected", _OLD_WEIGHT_TABLE.items())
def test_profile_weight_field(profile_id: str, expected: float) -> None:
    """Profile.weight matches the value previously hardcoded in _profile_weight."""
    assert get_profile(profile_id).weight == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Group B — numeric parity against the old substring-matching table
# ---------------------------------------------------------------------------

_PARITY_CASES = [
    # (profile_ids, supported_set, contradicted_set, sufficient_set, issuable_set)
    # All agree: single profile
    (["risk_sentinel_v1"], {"risk_sentinel_v1"}, set(), {"risk_sentinel_v1"}, {"risk_sentinel_v1"}),
    # Mixed support: three profiles, two agree
    (
        ["balanced_reviewer_v1", "sceptical_verifier_v1", "evidence_maximalist_v1"],
        {"balanced_reviewer_v1", "evidence_maximalist_v1"},
        set(),
        {"balanced_reviewer_v1", "evidence_maximalist_v1"},
        {"balanced_reviewer_v1", "evidence_maximalist_v1"},
    ),
    # All specialist profiles
    (
        ["medical_specialist_v1", "legal_specialist_v1", "finance_specialist_v1"],
        {"medical_specialist_v1"},
        {"legal_specialist_v1"},
        set(),
        set(),
    ),
    # Full general set
    (
        [
            "balanced_reviewer_v1",
            "sceptical_verifier_v1",
            "evidence_maximalist_v1",
            "literal_parser_v1",
            "risk_sentinel_v1",
        ],
        {"balanced_reviewer_v1", "risk_sentinel_v1"},
        {"sceptical_verifier_v1"},
        {"balanced_reviewer_v1", "risk_sentinel_v1", "literal_parser_v1"},
        {"balanced_reviewer_v1", "risk_sentinel_v1"},
    ),
]


@pytest.mark.parametrize("profile_ids,sup_set,con_set,suf_set,iss_set", _PARITY_CASES)
def test_aggregate_parity(
    profile_ids: list[str],
    sup_set: set[str],
    con_set: set[str],
    suf_set: set[str],
    iss_set: set[str],
) -> None:
    """aggregate_round0 produces scores numerically identical to the old table."""
    decisions = [
        _decision(
            pid,
            supported=pid in sup_set,
            contradicted=pid in con_set,
            sufficient=pid in suf_set,
            issuable=pid in iss_set,
        )
        for pid in profile_ids
    ]
    result = aggregate_round0(decisions)
    sub = result["s1"]

    # Compute expected from old table directly
    total = sum(_OLD_WEIGHT_TABLE[pid] for pid in profile_ids)
    exp_support = sum(_OLD_WEIGHT_TABLE[pid] for pid in profile_ids if pid in sup_set) / total
    exp_contra = sum(_OLD_WEIGHT_TABLE[pid] for pid in profile_ids if pid in con_set) / total
    exp_suf = sum(_OLD_WEIGHT_TABLE[pid] for pid in profile_ids if pid in suf_set) / total
    exp_iss = sum(_OLD_WEIGHT_TABLE[pid] for pid in profile_ids if pid in iss_set) / total

    assert sub.support_score == pytest.approx(exp_support)
    assert sub.contradiction_score == pytest.approx(exp_contra)
    assert sub.sufficiency_score == pytest.approx(exp_suf)
    assert sub.issuance_score == pytest.approx(exp_iss)


# ---------------------------------------------------------------------------
# Group C — _profile_weight shim
# ---------------------------------------------------------------------------


def test_profile_weight_shim_known() -> None:
    """_profile_weight returns .weight for a known profile."""
    assert _profile_weight("risk_sentinel_v1") == pytest.approx(1.2)
    assert _profile_weight("evidence_maximalist_v1") == pytest.approx(1.1)


def test_profile_weight_shim_unknown_falls_back() -> None:
    """_profile_weight returns 1.0 for unregistered synthetic profile IDs."""
    assert _profile_weight("synthetic_juror_x") == pytest.approx(1.0)
    assert _profile_weight("unknown_profile_99") == pytest.approx(1.0)
