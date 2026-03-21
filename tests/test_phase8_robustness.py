"""Phase 8 robustness probes — three distinct checks.

GROUP A: Paraphrase robustness
    Proves the committee advantage survives when hint phrases are replaced
    with clinical/financial paraphrases of the same semantic.
    Test content is designed to contain ONLY the new paraphrase-tier hints
    (not any primary-tier hint), to confirm the extended list is doing the work,
    not the original phrases.

GROUP B: Confidence ablation
    Proves that verdict changes between committee and single are driven by
    boolean supported/sufficient divergence across profiles, NOT by
    confidence-value weighting.
    aggregate_round0 computes scores from boolean flags × profile weight.
    JurorDecision.confidence is stored in the trace but is never read by
    the aggregation function.  This group makes that mechanistic claim explicit
    and testable.

GROUP C: False escalation impact
    Proves that the new hint tiers do not produce false escalations on
    domain content that makes no safety overclaim and uses no weak-evidence
    language.  The medical and finance committees must PASS clean factual
    content at the same rate as before Phase 8.

Invariant preserved across all groups:
    Hard hints (_UNSAFE_HINTS, _INSUFFICIENT_HINTS) still fire for ALL profiles.
    The benchmark committee_advantage == 0 test in test_phase7_benchmark_suite.py
    continues to hold because benchmark ESCALATE cases use only hard hints.
"""
from __future__ import annotations

import copy

import pytest

pytestmark = pytest.mark.legacy

from symposia.aggregation.round0 import aggregate_round0
from symposia.evaluation import EvaluationHarness
from symposia.jurors.rule_based import RuleBasedJuror
from symposia.models.claim import Subclaim, SubclaimKind
from symposia.models.evaluation import EvaluationCase, ExpectedVerdict
from symposia.models.juror import JurorDecision
from symposia.profile_sets import get_profile_set


def _sc(text: str) -> Subclaim:
    return Subclaim(subclaim_id="sc", text=text, kind=SubclaimKind.FACT)


def _vote(profile_id: str, text: str) -> JurorDecision:
    return RuleBasedJuror(juror_id="j", profile_id=profile_id).decide(_sc(text))


# ---------------------------------------------------------------------------
# GROUP A — Paraphrase robustness
# Each test uses only paraphrase-tier hints.  primary-tier phrases must be
# absent from the test string to prove the extended list is doing the work.
# ---------------------------------------------------------------------------

def test_risk_sentinel_fires_on_no_adverse_reactions():
    """New paraphrase hint: 'no adverse reactions' (clinical variant of 'no side effects').
    risk_sentinel fires (safety_bias=high); balanced_reviewer does not.
    Confirmed: primary 'no side effects' is NOT present in this text.
    """
    text = "This compound has no adverse reactions and can be taken without medical guidance."
    assert _vote("risk_sentinel_v1", text).sufficient is False
    assert _vote("balanced_reviewer_v1", text).sufficient is True


def test_evidence_maximalist_fires_on_negligible_toxicity():
    """New paraphrase hint: 'negligible toxicity' (clinical understatement).
    evidence_maximalist fires (stance=strict); literal_parser does not.
    """
    text = "The formulation demonstrates negligible toxicity in in-house testing."
    assert _vote("evidence_maximalist_v1", text).sufficient is False
    assert _vote("literal_parser_v1", text).sufficient is True


def test_risk_sentinel_fires_on_no_adverse_effects():
    """New paraphrase hint: 'no adverse effects'."""
    text = "The product shows no adverse effects across tested populations."
    assert _vote("risk_sentinel_v1", text).sufficient is False
    assert _vote("balanced_reviewer_v1", text).sufficient is True


def test_finance_specialist_fires_on_no_known_risks():
    """New paraphrase hint: 'no known risks' (financial safety overclaim).
    finance_specialist fires (safety_bias=high); balanced_reviewer does not.
    """
    text = "Investing in this instrument carries no known risks per the issuer."
    assert _vote("finance_specialist_v1", text).sufficient is False
    assert _vote("balanced_reviewer_v1", text).sufficient is True


def test_evidence_maximalist_fires_on_preliminary_data():
    """New paraphrase hint: 'preliminary data' (weak-evidence hedge).
    evidence_maximalist fires (evidence_demand=high); balanced_reviewer does not.
    """
    text = "Preliminary data from the pilot study suggests reduced recovery time."
    assert _vote("evidence_maximalist_v1", text).sufficient is False
    assert _vote("balanced_reviewer_v1", text).sufficient is True


def test_sceptical_verifier_fires_on_early_findings_suggest():
    """New paraphrase hint: 'early findings suggest'.
    sceptical_verifier fires (evidence_demand=high); balanced_reviewer does not.
    """
    text = "Early findings suggest this allocation methodology may outperform passive strategies."
    assert _vote("sceptical_verifier_v1", text).sufficient is False
    assert _vote("balanced_reviewer_v1", text).sufficient is True


def test_evidence_maximalist_fires_on_limited_evidence():
    """New paraphrase hint: 'limited evidence'."""
    text = "Limited evidence points to improved outcomes with this intervention."
    assert _vote("evidence_maximalist_v1", text).sufficient is False
    assert _vote("balanced_reviewer_v1", text).sufficient is True


def test_risk_sentinel_fires_on_not_yet_conclusive():
    """New paraphrase hint: 'not yet conclusive'."""
    text = "Results look promising, though not yet conclusive per the research team."
    assert _vote("risk_sentinel_v1", text).sufficient is False
    assert _vote("balanced_reviewer_v1", text).sufficient is True


# Four committee-vs-single cases using ONLY paraphrase-tier hints.
# These must not contain any primary-tier phrase — verified in comments.
PARAPHRASE_CASES = [
    EvaluationCase(
        case_id="pr_med_safety_1",
        content=(
            "This supplement has no adverse reactions and demonstrates negligible toxicity, "
            "so patients can self-administer without physician oversight."
        ),
        domain="medical",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale=(
            "Uses 'no adverse reactions' (new) + 'negligible toxicity' (new). "
            "Primary-tier phrases absent. Medical committee escalates; "
            "balanced_reviewer (single) misses it."
        ),
        tags=["phase8", "paraphrase", "medical"],
    ),
    EvaluationCase(
        case_id="pr_med_safety_2",
        content=(
            "The product is free from side effects and presents no known risks, "
            "according to in-house testing."
        ),
        domain="medical",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale=(
            "Uses 'free from side effects' (new) + 'no known risks' (new). "
            "Primary 'no side effects' is absent."
        ),
        tags=["phase8", "paraphrase", "medical"],
    ),
    EvaluationCase(
        case_id="pr_fin_weak_1",
        content=(
            "Preliminary data from a small pilot study indicates this strategy "
            "may deliver above-market returns."
        ),
        domain="finance",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale=(
            "Uses 'preliminary data' (new). "
            "Primary 'some evidence suggests' absent. Finance committee escalates."
        ),
        tags=["phase8", "paraphrase", "finance"],
    ),
    EvaluationCase(
        case_id="pr_fin_weak_2",
        content=(
            "Early findings suggest this allocation approach has historically provided "
            "strong growth, though not yet conclusive."
        ),
        domain="finance",
        expected_verdict=ExpectedVerdict.ESCALATE,
        rationale=(
            "Uses 'early findings suggest' (new) + 'not yet conclusive' (new). "
            "Primary phrases absent. Finance committee escalates."
        ),
        tags=["phase8", "paraphrase", "finance"],
    ),
]


def test_paraphrase_primary_hints_absent():
    """Invariant: none of the paraphrase cases contain a primary-tier hint phrase.

    This proof is essential — if a primary-tier phrase were present, the test
    would not isolate the paraphrase extensions.  All profiles fire on primary-tier
    phrases, which would eliminate the committee vs single contrast.
    """
    primary_hints = (
        "no side effects", "completely safe", "no risk", "always works", "zero risk",
        "skip emergency", "ignore jurisdiction", "guaranteed", "all retirement savings",
        "proven to work", "this treatment",
        "may help", "some evidence suggests", "could be beneficial",
        "possibly effective", "anecdotal reports",
    )
    for case in PARAPHRASE_CASES:
        lowered = case.content.lower()
        for phrase in primary_hints:
            assert phrase not in lowered, (
                f"Case '{case.case_id}' contains primary hint '{phrase}'. "
                "This invalidates the paraphrase isolation."
            )


def test_committee_advantage_survives_paraphrase():
    """The committee catches all four paraphrase cases; the single baseline misses all.

    This is the central claim of Group A: committee advantage is NOT phrase-bound
    to the original primary-tier hints.  It survives paraphrase.
    """
    harness = EvaluationHarness()
    cmp = harness.compare_committee_vs_single(
        suite_id="pr_paraphrase_advantage",
        cases=PARAPHRASE_CASES,
        single_profile_id="balanced_reviewer_v1",
    )
    assert cmp.committee_advantage_count == len(PARAPHRASE_CASES), (
        f"Expected committee advantage on all {len(PARAPHRASE_CASES)} paraphrase cases. "
        f"Got committee_advantage={cmp.committee_advantage_count}, "
        f"single_advantage={cmp.single_advantage_count}, "
        f"both_correct={cmp.both_correct_count}, "
        f"both_wrong={cmp.both_wrong_count}"
    )


def test_committee_accuracy_perfect_single_accuracy_zero_on_paraphrase():
    """Full accuracy gap on paraphrase cases: committee=1.0, single=0.0."""
    harness = EvaluationHarness()
    cmp = harness.compare_committee_vs_single(
        suite_id="pr_accuracy_gap",
        cases=PARAPHRASE_CASES,
        single_profile_id="balanced_reviewer_v1",
    )
    assert cmp.committee_accuracy == pytest.approx(1.0)
    assert cmp.single_juror_accuracy == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# GROUP B — Confidence ablation
# ---------------------------------------------------------------------------

def test_aggregate_round0_ignores_confidence_field():
    """Mechanistic proof: aggregate_round0 does not read JurorDecision.confidence.

    Two decision lists identical in boolean flags and profile weights but
    differing in confidence must produce identical aggregated scores.
    """
    decisions_real = [
        JurorDecision(
            juror_id="j1", profile_id="balanced_reviewer_v1", subclaim_id="sc",
            supported=True, contradicted=False, sufficient=True, issuable=True,
            confidence=0.88,
        ),
        JurorDecision(
            juror_id="j2", profile_id="risk_sentinel_v1", subclaim_id="sc",
            supported=False, contradicted=False, sufficient=False, issuable=False,
            confidence=0.20,
        ),
    ]
    # Same boolean flags, completely different confidence values.
    decisions_ablated = [
        d.model_copy(update={"confidence": 0.5}) for d in decisions_real
    ]

    agg_real = aggregate_round0(decisions_real)["sc"]
    agg_ablated = aggregate_round0(decisions_ablated)["sc"]

    assert agg_real.support_score == pytest.approx(agg_ablated.support_score)
    assert agg_real.contradiction_score == pytest.approx(agg_ablated.contradiction_score)
    assert agg_real.sufficiency_score == pytest.approx(agg_ablated.sufficiency_score)
    assert agg_real.issuance_score == pytest.approx(agg_ablated.issuance_score)


def test_phase8_advantage_driven_by_boolean_flags_not_confidence():
    """Ablation applied to the full medical committee on a safety-claim subclaim.

    Replacing all per-juror confidence values with 0.5 (uniform) does not
    change the aggregated support/sufficiency scores.  The committee advantage
    over a single balanced_reviewer comes from boolean flag divergence (3 of 5
    profiles flag sufficient=False), not from confidence weighting.
    """
    subclaim = _sc(
        "This supplement is completely safe and has no side effects."
    )
    ps = get_profile_set("medical_strict_v1")
    jurors = [
        RuleBasedJuror(juror_id=f"j{i}", profile_id=pid)
        for i, pid in enumerate(ps.profiles)
    ]
    decisions = [j.decide(subclaim) for j in jurors]

    # Ablated: all confidence = 0.5, booleans unchanged.
    ablated = [d.model_copy(update={"confidence": 0.5}) for d in decisions]

    agg_real = aggregate_round0(decisions)["sc"]
    agg_ablated = aggregate_round0(ablated)["sc"]

    assert agg_real.support_score == pytest.approx(agg_ablated.support_score), (
        "Confidence ablation changed support_score — confidence is being used in "
        "aggregation.  This would mean the verdict mechanism has changed unexpectedly."
    )
    assert agg_real.sufficiency_score == pytest.approx(agg_ablated.sufficiency_score)


def test_boolean_flag_divergence_identifies_which_profiles_drive_escalation():
    """Direct inspection of which profiles vote sufficient=False on a safety-claim subclaim.

    Expected split for medical committee
    ('risk_sentinel_v1', 'evidence_maximalist_v1', 'medical_specialist_v1',
     'sceptical_verifier_v1', 'literal_parser_v1') on 'completely safe':

        Fires (sufficient=False):  risk_sentinel, evidence_maximalist, medical_specialist
        Does not fire (sufficient=True): sceptical_verifier, literal_parser

    This 3/5 split with higher-weighted profiles in the firing group is what
    drives support_score below SUPPORT_FLOOR.
    """
    text = "This compound is completely safe and always works as directed."
    for pid in ("risk_sentinel_v1", "evidence_maximalist_v1", "medical_specialist_v1"):
        d = _vote(pid, text)
        assert d.sufficient is False, (
            f"{pid} should fire on 'completely safe'/'always works' "
            f"but returned sufficient=True"
        )
    for pid in ("sceptical_verifier_v1", "literal_parser_v1"):
        d = _vote(pid, text)
        assert d.sufficient is True, (
            f"{pid} should NOT fire on safety-claim hints but returned sufficient=False"
        )


def test_weighted_aggregation_sum_with_known_profile_weights():
    """Verify the expected numeric outcome of the 3/5 medical committee split.

    Profile weights: risk_sentinel=1.2, evidence_maximalist=1.1, medical_specialist=1.15,
                     sceptical_verifier=1.05, literal_parser=1.0
    Firing (supported=False): 1.2 + 1.1 + 1.15 = 3.45
    Not firing (supported=True): 1.05 + 1.0 = 2.05
    Total weight: 5.5
    Expected support_score ≈ 2.05 / 5.5 ≈ 0.373

    0.373 < SUPPORT_FLOOR=0.70, so escalation fires on support alone.
    """
    from symposia.escalation.thresholds import SUPPORT_FLOOR

    subclaim = _sc("This compound is completely safe and has no side effects.")
    ps = get_profile_set("medical_strict_v1")
    decisions = [
        RuleBasedJuror(f"j{i}", pid).decide(subclaim)
        for i, pid in enumerate(ps.profiles)
    ]
    agg = aggregate_round0(decisions)["sc"]

    expected_support = pytest.approx(2.05 / 5.5, abs=1e-3)
    assert agg.support_score == expected_support, (
        f"support_score={agg.support_score:.4f}, expected ≈0.373.  "
        "A profile weight or behavioral flag may have changed."
    )
    assert agg.support_score < SUPPORT_FLOOR, (
        "Aggregated support should be below SUPPORT_FLOOR to confirm escalation fires."
    )


# ---------------------------------------------------------------------------
# GROUP C — False escalation impact
# Clean factual content with no safety-overclaim and no weak-evidence language.
# All cases must PASS through both the domain committee AND the single baseline.
# These prove the new hint tiers do not create false alarms on ordinary domain content.
# ---------------------------------------------------------------------------

CLEAN_PASS_CASES = [
    # Medical: mechanism, threshold, and pharmacology facts — no safety claims.
    EvaluationCase(
        case_id="clean_med_01",
        content="Metformin reduces hepatic glucose output and improves peripheral insulin sensitivity.",
        domain="medical",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Mechanism of action statement; no safety claim, no epistemic hedge.",
        tags=["phase8", "false_escalation_check", "medical"],
    ),
    EvaluationCase(
        case_id="clean_med_02",
        content="Hypertension is defined as a persistent systolic blood pressure above 130 mmHg.",
        domain="medical",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Clinical definition; no overclaim, no hedge.",
        tags=["phase8", "false_escalation_check", "medical"],
    ),
    EvaluationCase(
        case_id="clean_med_03",
        content="Statins inhibit HMG-CoA reductase, reducing hepatic cholesterol synthesis.",
        domain="medical",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Standard pharmacology; no hint phrase of any tier.",
        tags=["phase8", "false_escalation_check", "medical"],
    ),
    # Finance: definitions, principles, qualified historical facts — no overclaim.
    EvaluationCase(
        case_id="clean_fin_01",
        content="A bond's duration measures its sensitivity to interest rate changes.",
        domain="finance",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Standard fixed-income definition; no hint phrases.",
        tags=["phase8", "false_escalation_check", "finance"],
    ),
    EvaluationCase(
        case_id="clean_fin_02",
        content="Dollar-cost averaging reduces the average cost per share by purchasing more units at lower prices.",
        domain="finance",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Mechanical description; no safety claim, no epistemic hedge.",
        tags=["phase8", "false_escalation_check", "finance"],
    ),
    EvaluationCase(
        case_id="clean_fin_03",
        content="Equities have historically provided higher long-term returns than government bonds, with higher volatility.",
        domain="finance",
        expected_verdict=ExpectedVerdict.PASS,
        rationale="Qualified historical fact ('historically', 'higher volatility'); no overclaim.",
        tags=["phase8", "false_escalation_check", "finance"],
    ),
]


def test_clean_medical_content_does_not_false_escalate():
    harness = EvaluationHarness()
    result = harness.run(
        suite_id="clean_med",
        cases=[c for c in CLEAN_PASS_CASES if c.domain == "medical"],
    )
    failed = [o for o in result.outcomes if not o.correct]
    assert not failed, (
        "Clean medical content was incorrectly escalated:\n"
        + "\n".join(
            f"  {o.case_id}: triggers={o.trigger_reasons}" for o in failed
        )
    )


def test_clean_finance_content_does_not_false_escalate():
    harness = EvaluationHarness()
    result = harness.run(
        suite_id="clean_fin",
        cases=[c for c in CLEAN_PASS_CASES if c.domain == "finance"],
    )
    failed = [o for o in result.outcomes if not o.correct]
    assert not failed, (
        "Clean finance content was incorrectly escalated:\n"
        + "\n".join(
            f"  {o.case_id}: triggers={o.trigger_reasons}" for o in failed
        )
    )


def test_false_escalation_rate_zero_for_clean_pass_suite():
    """FER = 0.0 for all domains in the clean PASS suite.

    This is the quantitative check that the new hint tiers do not spike
    false escalation on ordinary domain content.
    """
    harness = EvaluationHarness()
    result = harness.run(suite_id="clean_all", cases=CLEAN_PASS_CASES)
    for domain, summary in result.domain_summaries.items():
        assert summary.false_escalation_rate == pytest.approx(0.0), (
            f"{domain}: false_escalation_rate={summary.false_escalation_rate:.4f} "
            "(expected 0.0 on clean factual content)"
        )


def test_committee_and_single_agree_on_clean_content():
    """Neither committee nor single escalates clean content.

    committee_advantage == 0 on clean PASS content is the CORRECT result:
    there should be no dispute on factual, unhedged statements.
    """
    harness = EvaluationHarness()
    cmp = harness.compare_committee_vs_single(
        suite_id="clean_agree",
        cases=CLEAN_PASS_CASES,
        single_profile_id="balanced_reviewer_v1",
    )
    assert cmp.committee_advantage_count == 0, (
        "Committee should not outperform single on clean content "
        "(no escalation is correct for both)"
    )
    assert cmp.single_advantage_count == 0, (
        "Single should not outperform committee on clean content"
    )
    assert cmp.both_wrong_count == 0, (
        "Neither path should escalate clean factual content; "
        "both_wrong > 0 means a false escalation occurred"
    )
    assert cmp.both_correct_count == len(CLEAN_PASS_CASES)
