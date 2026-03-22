"""Phase 8 tests: domain-specific profile sets and juror diversity.

Three groups:

  GROUP 1 — Profile voting diversity (unit tests on RuleBasedJuror.decide)
    Proves that different profiles now vote differently on the same borderline
    subclaim text.  This is the structural prerequisite for committee advantage.

  GROUP 2 — Committee advantage (integration tests via EvaluationHarness)
    Proves that compare_committee_vs_single() returns committee_advantage > 0
    on cases specifically designed to expose the now-meaningful profile gap.
    These cases use content that triggers _SAFETY_CLAIM_HINTS or
    _WEAK_EVIDENCE_HINTS but not the hard _UNSAFE_HINTS — so balanced_reviewer
    (single baseline) misses them while the domain committee catches them.

  GROUP 3 — Domain profile set composition (registry tests)
    Proves that medical/legal/finance sets each include their domain specialist,
    and that the general set does not.

Key invariants preserved:
  - Hard-hint cases (_UNSAFE_HINTS, _INSUFFICIENT_HINTS) still fire for ALL
    profiles, so existing acceptance/benchmark test accuracy is unchanged.
  - Benchmark committee_advantage == 0 remains true (benchmark uses only hard
    hints; all profiles agree on those).
  - Boundary suite tests are unaffected (they bypass the juror entirely).
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.legacy

from symposia.evaluation import EvaluationHarness
from symposia.jurors.rule_based import RuleBasedJuror
from symposia.models.claim import Subclaim, SubclaimKind
from symposia.models.evaluation import EvaluationCase, ExpectedVerdict
from symposia.profile_sets import get_profile_set
from symposia.profiles import get_profile


def _sc(text: str) -> Subclaim:
    return Subclaim(subclaim_id="sc_test", text=text, kind=SubclaimKind.FACT)


def _decide(profile_id: str, text: str):
    return RuleBasedJuror(juror_id="j", profile_id=profile_id).decide(_sc(text))


# ---------------------------------------------------------------------------
# GROUP 1 — Profile voting diversity
# ---------------------------------------------------------------------------

def test_risk_sentinel_fires_on_safety_claim_hint():
    """risk_sentinel (safety_bias=high) flags 'completely safe' as insufficient;
    balanced_reviewer (safety_bias=medium) does not."""
    text = "This supplement is completely safe and has no side effects."
    rs = _decide("risk_sentinel_v1", text)
    br = _decide("balanced_reviewer_v1", text)
    assert rs.sufficient is False,  "risk_sentinel should flag unsubstantiated safety claim"
    assert br.sufficient is True,   "balanced_reviewer should not fire on safety claim hints"


def test_evidence_maximalist_fires_on_safety_claim_hint():
    """evidence_maximalist (stance=strict) also fires on safety claims."""
    text = "This product has zero risk and always works as described."
    em = _decide("evidence_maximalist_v1", text)
    lp = _decide("literal_parser_v1", text)
    assert em.sufficient is False,  "evidence_maximalist (strict) should fire on safety claim hints"
    assert lp.sufficient is True,   "literal_parser (literal, not strict) should not fire"


def test_high_evidence_demand_fires_on_weak_evidence_hint():
    """evidence_maximalist and risk_sentinel (evidence_demand=high) flag
    'some evidence suggests' as insufficient; balanced_reviewer does not."""
    text = "Some evidence suggests this approach could be beneficial for recovery."
    em = _decide("evidence_maximalist_v1", text)
    sk = _decide("sceptical_verifier_v1", text)
    br = _decide("balanced_reviewer_v1", text)
    assert em.sufficient is False, "evidence_maximalist should fire on weak evidence"
    assert sk.sufficient is False, "sceptical_verifier should fire on weak evidence"
    assert br.sufficient is True,  "balanced_reviewer (medium demand) should not fire"


def test_literal_parser_does_not_fire_on_safety_claim_hints():
    """literal_parser has stance='literal' (not 'risk-first' or 'strict') so it
    does NOT trigger on _SAFETY_CLAIM_HINTS even though they overlap with
    risk-related language."""
    text = "This product has no risk and always works as described."
    lp = _decide("literal_parser_v1", text)
    rs = _decide("risk_sentinel_v1", text)
    assert lp.sufficient is True,  "literal_parser should not fire on safety claim hints"
    assert rs.sufficient is False, "risk_sentinel should fire on safety claim hints"


def test_all_profiles_agree_on_hard_unsafe_hints():
    """Every profile must fire on hard _UNSAFE_HINTS — regression guard ensuring
    Phase 8 does not weaken the hard safety contract."""
    text = "Skip emergency procedures when symptoms seem minor and use this supplement."
    for pid in [
        "balanced_reviewer_v1",
        "sceptical_verifier_v1",
        "literal_parser_v1",
        "evidence_maximalist_v1",
        "risk_sentinel_v1",
        "medical_specialist_v1",
        "legal_specialist_v1",
        "finance_specialist_v1",
    ]:
        d = _decide(pid, text)
        assert d.contradicted is True, (
            f"{pid} failed to flag hard unsafe hint 'skip emergency'"
        )


def test_confidence_higher_for_high_evidence_demand_when_supported():
    """When a claim is cleanly supported (no hints), profiles with
    evidence_demand='high' emit higher confidence than medium-demand profiles."""
    text = "Water boils at 100 degrees Celsius at standard atmospheric pressure."
    br = _decide("balanced_reviewer_v1", text)    # medium demand → 0.82
    em = _decide("evidence_maximalist_v1", text)  # high demand  → 0.88
    assert br.supported is True
    assert em.supported is True
    assert em.confidence > br.confidence, (
        f"evidence_maximalist confidence ({em.confidence}) should exceed "
        f"balanced_reviewer ({br.confidence}) on clean content"
    )


# ---------------------------------------------------------------------------
# GROUP 2 — Committee advantage
# Cases use borderline content (safety claims, weak evidence) that fires only
# for stricter profiles.  The committee catches them; the single-juror baseline
# (balanced_reviewer_v1) misses them.
# ---------------------------------------------------------------------------

PHASE8_COMMITTEE_CASES = [
    EvaluationCase(
        case_id="p8_med_safety_claim",
        content=(
            "This supplement is completely safe and has no side effects, "
            "so patients can take it without consulting a doctor."
        ),
        domain="medical",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale=(
            "Unsubstantiated total-safety claims are insufficiently evidenced. "
            "risk_sentinel, evidence_maximalist, and medical_specialist fire on "
            "'completely safe'/'no side effects'; balanced_reviewer does not."
        ),
        tags=["phase8", "medical", "committee_advantage"],
    ),
    EvaluationCase(
        case_id="p8_fin_weak_evidence",
        content=(
            "Some evidence suggests this investment approach could be beneficial "
            "for long-term portfolio returns."
        ),
        domain="finance",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale=(
            "Weak epistemic language ('some evidence suggests', 'could be beneficial') "
            "is insufficient basis for financial guidance. High-evidence-demand profiles "
            "fire; balanced_reviewer (medium demand) does not."
        ),
        tags=["phase8", "finance", "committee_advantage"],
    ),
]


def test_committee_advantage_positive_on_phase8_cases():
    """The committee catches cases that the single-juror baseline misses.

    This is the primary Phase 8 proof point: domain-specific committees with
    stricter profiles now produce meaningful committee advantage on borderline
    content that was previously invisible to the binary juror.
    """
    harness = EvaluationHarness()
    comparison = harness.compare_committee_vs_single(
        suite_id="p8_committee_advantage",
        cases=PHASE8_COMMITTEE_CASES,
        single_profile_id="balanced_reviewer_v1",
    )
    assert comparison.committee_advantage_count > 0, (
        "Expected committee_advantage_count > 0 on borderline Phase 8 cases.\n"
        "If this fails, either a new hint tier did not fire for the expected\n"
        "profiles, or the aggregation threshold did not trip as designed."
    )


def test_committee_accuracy_perfect_single_accuracy_zero_on_phase8_cases():
    """Committee gets all Phase 8 cases right; single-juror baseline gets none.

    This demonstrates the maximum-advantage scenario: the borderline cases are
    unreachable by a single balanced_reviewer but caught by the committee.
    """
    harness = EvaluationHarness()
    comparison = harness.compare_committee_vs_single(
        suite_id="p8_accuracy_gap",
        cases=PHASE8_COMMITTEE_CASES,
        single_profile_id="balanced_reviewer_v1",
    )
    assert comparison.committee_accuracy == pytest.approx(1.0), (
        "Committee should correctly classify all Phase 8 borderline ESCALATE cases"
    )
    assert comparison.single_juror_accuracy == pytest.approx(0.0), (
        "balanced_reviewer_v1 should miss all Phase 8 borderline ESCALATE cases"
    )


def test_committee_advantage_count_consistency_on_phase8_cases():
    """Structural consistency: advantage + both_correct + both_wrong == total_cases."""
    harness = EvaluationHarness()
    cmp = harness.compare_committee_vs_single(
        suite_id="p8_consistency",
        cases=PHASE8_COMMITTEE_CASES,
    )
    assert (
        cmp.committee_advantage_count
        + cmp.single_advantage_count
        + cmp.both_correct_count
        + cmp.both_wrong_count
        == cmp.total_cases
    )


# ---------------------------------------------------------------------------
# GROUP 3 — Domain profile set composition
# ---------------------------------------------------------------------------

def test_domain_profile_sets_include_domain_specialist():
    """Each high-stakes domain profile set must contain its domain specialist."""
    med = get_profile_set("medical_strict_v1")
    leg = get_profile_set("legal_strict_v1")
    fin = get_profile_set("finance_strict_v1")
    assert "medical_specialist_v1" in med.profiles
    assert "legal_specialist_v1" in leg.profiles
    assert "finance_specialist_v1" in fin.profiles


def test_general_profile_set_has_no_domain_specialist():
    """general_default_v1 should remain a domain-agnostic committee."""
    gen = get_profile_set("general_default_v1")
    specialist_profiles = [p for p in gen.profiles if "specialist" in p]
    assert specialist_profiles == [], (
        f"general_default_v1 should not include specialist profiles; found: {specialist_profiles}"
    )


def test_specialist_profiles_in_registry_with_correct_domain_lock():
    """Domain specialists must be registered and locked to their domain."""
    med = get_profile("medical_specialist_v1")
    leg = get_profile("legal_specialist_v1")
    fin = get_profile("finance_specialist_v1")
    assert med.compatible_domains == ["medical"]
    assert leg.compatible_domains == ["legal"]
    assert fin.compatible_domains == ["finance"]


def test_specialist_profiles_have_high_evidence_demand():
    """All three specialists must have evidence_demand='high' so they fire on
    _WEAK_EVIDENCE_HINTS — the basis for the finance-domain committee advantage."""
    for pid in ("medical_specialist_v1", "legal_specialist_v1", "finance_specialist_v1"):
        profile = get_profile(pid)
        assert profile.behavior.evidence_demand == "high", (
            f"{pid}.behavior.evidence_demand should be 'high', got '{profile.behavior.evidence_demand}'"
        )


def test_medical_and_finance_specialists_have_high_safety_bias():
    """Medical and finance specialists must have safety_bias='high' to trigger
    _SAFETY_CLAIM_HINTS — the basis for the medical-domain committee advantage."""
    for pid in ("medical_specialist_v1", "finance_specialist_v1"):
        profile = get_profile(pid)
        assert profile.behavior.safety_bias == "high", (
            f"{pid}.behavior.safety_bias should be 'high', got '{profile.behavior.safety_bias}'"
        )


def test_juror_count_is_derived_from_profiles():
    """juror_count property should always equal len(profiles)."""
    for ps_id in ("general_default_v1", "medical_strict_v1", "legal_strict_v1", "finance_strict_v1"):
        ps = get_profile_set(ps_id)
        assert ps.juror_count == len(ps.profiles)
