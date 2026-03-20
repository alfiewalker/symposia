"""Locked escalation fixtures.

These fixtures are fully deterministic: they construct InitialReviewResult
directly from known field values, with no engine or LLM involvement.
They test boundary conditions that neat synthetic cases miss.

Each fixture is a function returning an (InitialReviewResult, dict) pair,
where the dict is the locked expected behaviour the planner must produce.

DO NOT change the numeric values without updating the locked expectations.
These are intentionally messy — they surface the ugly edge cases.
"""
from __future__ import annotations

from symposia.models.claim import ClaimBundle, Subclaim, SubclaimKind
from symposia.models.juror import JurorDecision
from symposia.models.round0 import CompletionDecision, InitialReviewResult, SubclaimDecision
from symposia.models.trace import CoreTrace, MinimalTraceAggregation, MinimalTraceSubclaim, MinimalTraceVote

# ---------------------------------------------------------------------------
# Fixture A — Multi-subclaim partial escalation
#
# sc_001: clean pass  (support=0.85, contradiction=0.10, sufficiency=0.90)
# sc_002: borderline  (support=0.68, contradiction=0.30, sufficiency=0.65)  → LOW_SUPPORT + LOW_SUFFICIENCY
# sc_003: failing     (support=0.40, contradiction=0.50, sufficiency=0.45)  → all three reasons
#
# completion.should_stop = True  →  REVIEW_NOT_COMPLETE must NOT appear
# dissents: sc_002 has 1 support / 1 contradicting (ratio 0.50 → CRITICAL)
#           sc_003 has 0 support  → no dissent record (pure rejection, no split)
# ---------------------------------------------------------------------------

def fixture_multi_subclaim_partial() -> tuple[InitialReviewResult, dict]:
    subclaims = [
        Subclaim(subclaim_id="sc_001", text="Clean claim.", kind=SubclaimKind.FACT),
        Subclaim(subclaim_id="sc_002", text="Borderline claim.", kind=SubclaimKind.FACT),
        Subclaim(subclaim_id="sc_003", text="Failing claim.", kind=SubclaimKind.FACT),
    ]
    bundle = ClaimBundle(bundle_id="fix_a", raw_content="Multi-subclaim test", subclaims=subclaims)

    decisions = [
        JurorDecision(juror_id="j1", profile_id="balanced_reviewer_v1", subclaim_id="sc_001",
                      supported=True, contradicted=False, sufficient=True, issuable=True, confidence=0.9),
        JurorDecision(juror_id="j2", profile_id="balanced_reviewer_v1", subclaim_id="sc_002",
                      supported=True, contradicted=False, sufficient=False, issuable=True, confidence=0.6),
        JurorDecision(juror_id="j3", profile_id="risk_sentinel_v1", subclaim_id="sc_002",
                      supported=False, contradicted=True, sufficient=False, issuable=False, confidence=0.7),
        JurorDecision(juror_id="j4", profile_id="sceptical_verifier_v1", subclaim_id="sc_003",
                      supported=False, contradicted=False, sufficient=False, issuable=False, confidence=0.3),
    ]

    aggregated = {
        "sc_001": SubclaimDecision(subclaim_id="sc_001", support_score=0.85, contradiction_score=0.10,
                                   sufficiency_score=0.90, issuance_score=0.85),
        "sc_002": SubclaimDecision(subclaim_id="sc_002", support_score=0.68, contradiction_score=0.30,
                                   sufficiency_score=0.65, issuance_score=0.50),
        "sc_003": SubclaimDecision(subclaim_id="sc_003", support_score=0.40, contradiction_score=0.50,
                                   sufficiency_score=0.45, issuance_score=0.20),
    }

    core_trace = CoreTrace(
        run_id="fix_a",
        profile_set_selected="general_default_v1",
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[
            MinimalTraceVote(juror_id=d.juror_id, subclaim_id=d.subclaim_id,
                             supported=d.supported, contradicted=d.contradicted,
                             sufficient=d.sufficient, confidence=d.confidence)
            for d in decisions
        ],
        aggregation_outcome=[
            MinimalTraceAggregation(subclaim_id=k, support_score=v.support_score,
                                    contradiction_score=v.contradiction_score,
                                    sufficiency_score=v.sufficiency_score)
            for k, v in aggregated.items()
        ],
    )

    result = InitialReviewResult(
        run_id="fix_a",
        bundle=bundle,
        decisions=decisions,
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(should_stop=True, reason="threshold_met"),
        core_trace=core_trace,
    )

    expected = {
        "should_escalate": True,
        "escalated_subclaim_ids": {"sc_002", "sc_003"},
        "no_escalation_subclaim_ids": {"sc_001"},
        "review_not_complete_trigger": False,   # completion.should_stop=True
        "critical_dissent_trigger": True,       # sc_002: ratio=0.50 ≥ 0.40
        "dissent_count_min": 1,
    }
    return result, expected


# ---------------------------------------------------------------------------
# Fixture B — Contradiction threshold boundary (exact-value edge cases)
#
# sc_below: contradiction=0.349  →  below ceiling (0.35)  → no MATERIAL_CONTRADICTION
# sc_at:    contradiction=0.350  →  at ceiling exactly    → MATERIAL_CONTRADICTION
#
# support and sufficiency are both 0.75 (pass) for both subclaims.
# completion.should_stop = True
# ---------------------------------------------------------------------------

def fixture_contradiction_threshold_boundary() -> tuple[InitialReviewResult, dict]:
    subclaims = [
        Subclaim(subclaim_id="sc_below", text="Below threshold.", kind=SubclaimKind.FACT),
        Subclaim(subclaim_id="sc_at", text="At threshold exactly.", kind=SubclaimKind.FACT),
    ]
    bundle = ClaimBundle(bundle_id="fix_b", raw_content="Boundary test", subclaims=subclaims)

    aggregated = {
        "sc_below": SubclaimDecision(subclaim_id="sc_below", support_score=0.75,
                                     contradiction_score=0.349, sufficiency_score=0.75, issuance_score=0.70),
        "sc_at": SubclaimDecision(subclaim_id="sc_at", support_score=0.75,
                                  contradiction_score=0.350, sufficiency_score=0.75, issuance_score=0.70),
    }

    core_trace = CoreTrace(
        run_id="fix_b",
        profile_set_selected="general_default_v1",
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[],
        aggregation_outcome=[
            MinimalTraceAggregation(subclaim_id=k, support_score=v.support_score,
                                    contradiction_score=v.contradiction_score,
                                    sufficiency_score=v.sufficiency_score)
            for k, v in aggregated.items()
        ],
    )

    result = InitialReviewResult(
        run_id="fix_b",
        bundle=bundle,
        decisions=[],
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(should_stop=True, reason="threshold_met"),
        core_trace=core_trace,
    )

    expected = {
        "should_escalate": True,              # sc_at triggers MATERIAL_CONTRADICTION
        "sc_below_escalated": False,          # below the ceiling
        "sc_at_escalated": True,              # exactly at ceiling → escalated
        "sc_at_reason_codes": {"material_contradiction"},
        "review_not_complete_trigger": False,
    }
    return result, expected


# ---------------------------------------------------------------------------
# Fixture C — Maximum dissent: six jurors, three-way even split per subclaim
#
# sc_001: 3 supporting, 3 contradicting → ratio = 0.50 → CRITICAL
# sc_002: 2 supporting, 4 contradicting → ratio = 0.67 → CRITICAL
#
# Aggregated scores reflect the split:
#   sc_001: support=0.50, contradiction=0.50, sufficiency=0.55
#   sc_002: support=0.30, contradiction=0.67, sufficiency=0.40
#
# completion.should_stop = False  →  REVIEW_NOT_COMPLETE must appear
# ---------------------------------------------------------------------------

def fixture_maximum_dissent() -> tuple[InitialReviewResult, dict]:
    subclaims = [
        Subclaim(subclaim_id="sc_001", text="Even split claim.", kind=SubclaimKind.FACT),
        Subclaim(subclaim_id="sc_002", text="Heavy contradiction claim.", kind=SubclaimKind.FACT),
    ]
    bundle = ClaimBundle(bundle_id="fix_c", raw_content="Max dissent test", subclaims=subclaims)

    decisions = [
        JurorDecision(juror_id=f"j{i}", profile_id="balanced_reviewer_v1", subclaim_id="sc_001",
                      supported=(i < 3), contradicted=(i >= 3), sufficient=True, issuable=(i < 3), confidence=0.5)
        for i in range(6)
    ] + [
        JurorDecision(juror_id=f"k{i}", profile_id="sceptical_verifier_v1", subclaim_id="sc_002",
                      supported=(i < 2), contradicted=(i >= 2), sufficient=False, issuable=False, confidence=0.4)
        for i in range(6)
    ]

    aggregated = {
        "sc_001": SubclaimDecision(subclaim_id="sc_001", support_score=0.50, contradiction_score=0.50,
                                   sufficiency_score=0.55, issuance_score=0.40),
        "sc_002": SubclaimDecision(subclaim_id="sc_002", support_score=0.30, contradiction_score=0.67,
                                   sufficiency_score=0.40, issuance_score=0.15),
    }

    core_trace = CoreTrace(
        run_id="fix_c",
        profile_set_selected="general_default_v1",
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[
            MinimalTraceVote(juror_id=d.juror_id, subclaim_id=d.subclaim_id,
                             supported=d.supported, contradicted=d.contradicted,
                             sufficient=d.sufficient, confidence=d.confidence)
            for d in decisions
        ],
        aggregation_outcome=[
            MinimalTraceAggregation(subclaim_id=k, support_score=v.support_score,
                                    contradiction_score=v.contradiction_score,
                                    sufficiency_score=v.sufficiency_score)
            for k, v in aggregated.items()
        ],
    )

    result = InitialReviewResult(
        run_id="fix_c",
        bundle=bundle,
        decisions=decisions,
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(should_stop=False, reason="escalation_candidate"),
        core_trace=core_trace,
    )

    expected = {
        "should_escalate": True,
        "review_not_complete_trigger": True,   # should_stop=False
        "critical_dissent_trigger": True,
        "dissent_severity_sc_001": "critical",  # ratio 0.50 ≥ 0.40
        "dissent_severity_sc_002": "critical",  # ratio 0.67 ≥ 0.40
        "escalated_subclaim_ids": {"sc_001", "sc_002"},
    }
    return result, expected


# ---------------------------------------------------------------------------
# Fixture D — High support, critical safety caveat
#
# One subclaim scores well on support and sufficiency, but has a non-trivial
# contradiction score that crosses the ceiling.  This models the real-world
# pattern where a claim is mostly accepted but carries a material safety
# objection from a minority of jurors.
#
# sc_001: support=0.88, contradiction=0.40, sufficiency=0.85
#         → MATERIAL_CONTRADICTION only (support and sufficiency pass)
#
# completion.should_stop = True
# Jurors: 4 supporting, 2 contradicting → ratio = 0.33 → MATERIAL dissent
# ---------------------------------------------------------------------------

def fixture_high_support_safety_caveat() -> tuple[InitialReviewResult, dict]:
    subclaims = [
        Subclaim(subclaim_id="sc_001", text="Drug X is safe for adults at standard doses.", kind=SubclaimKind.FACT),
    ]
    bundle = ClaimBundle(bundle_id="fix_d", raw_content="Safety caveat test", subclaims=subclaims)

    decisions = [
        JurorDecision(juror_id=f"j{i}", profile_id="balanced_reviewer_v1", subclaim_id="sc_001",
                      supported=True, contradicted=False, sufficient=True, issuable=True, confidence=0.85)
        for i in range(4)
    ] + [
        JurorDecision(juror_id=f"k{i}", profile_id="risk_sentinel_v1", subclaim_id="sc_001",
                      supported=False, contradicted=True, sufficient=True, issuable=False, confidence=0.75)
        for i in range(2)
    ]

    aggregated = {
        "sc_001": SubclaimDecision(subclaim_id="sc_001", support_score=0.88,
                                   contradiction_score=0.40, sufficiency_score=0.85,
                                   issuance_score=0.70),
    }

    core_trace = CoreTrace(
        run_id="fix_d",
        profile_set_selected="medical_strict_v1",
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[
            MinimalTraceVote(juror_id=d.juror_id, subclaim_id=d.subclaim_id,
                             supported=d.supported, contradicted=d.contradicted,
                             sufficient=d.sufficient, confidence=d.confidence)
            for d in decisions
        ],
        aggregation_outcome=[
            MinimalTraceAggregation(subclaim_id=k, support_score=v.support_score,
                                    contradiction_score=v.contradiction_score,
                                    sufficiency_score=v.sufficiency_score)
            for k, v in aggregated.items()
        ],
    )

    result = InitialReviewResult(
        run_id="fix_d",
        bundle=bundle,
        decisions=decisions,
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(should_stop=True, reason="threshold_met"),
        core_trace=core_trace,
    )

    expected = {
        "should_escalate": True,
        "escalated_subclaim_ids": {"sc_001"},
        "sc_001_reason_codes": {"material_contradiction"},  # support & sufficiency pass
        "review_not_complete_trigger": False,
        "critical_dissent_trigger": False,                  # 2/6 = 0.33 < 0.40 → MATERIAL, not CRITICAL
        "dissent_severity_sc_001": "material",              # 0.33 ≥ 0.20 → MATERIAL
    }
    return result, expected


# ---------------------------------------------------------------------------
# Fixture E — Low support, zero contradiction
#
# A subclaim that jurors mostly ignore (low confidence, low support) but
# nobody actively disputes.  Demonstrates that LOW_SUPPORT escalates
# independently of contradiction — silence is not endorsement.
#
# sc_001: support=0.40, contradiction=0.05, sufficiency=0.45
#         → LOW_SUPPORT + LOW_SUFFICIENCY (no MATERIAL_CONTRADICTION)
#
# No juror contradicted → no dissent record should be produced.
# completion.should_stop = True
# ---------------------------------------------------------------------------

def fixture_low_support_no_contradiction() -> tuple[InitialReviewResult, dict]:
    subclaims = [
        Subclaim(subclaim_id="sc_001", text="An obscure claim with weak backing.", kind=SubclaimKind.FACT),
    ]
    bundle = ClaimBundle(bundle_id="fix_e", raw_content="Low support test", subclaims=subclaims)

    decisions = [
        JurorDecision(juror_id=f"j{i}", profile_id="balanced_reviewer_v1", subclaim_id="sc_001",
                      supported=(i == 0), contradicted=False, sufficient=False, issuable=(i == 0), confidence=0.35)
        for i in range(4)
    ]

    aggregated = {
        "sc_001": SubclaimDecision(subclaim_id="sc_001", support_score=0.40,
                                   contradiction_score=0.05, sufficiency_score=0.45,
                                   issuance_score=0.25),
    }

    core_trace = CoreTrace(
        run_id="fix_e",
        profile_set_selected="general_default_v1",
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[
            MinimalTraceVote(juror_id=d.juror_id, subclaim_id=d.subclaim_id,
                             supported=d.supported, contradicted=d.contradicted,
                             sufficient=d.sufficient, confidence=d.confidence)
            for d in decisions
        ],
        aggregation_outcome=[
            MinimalTraceAggregation(subclaim_id=k, support_score=v.support_score,
                                    contradiction_score=v.contradiction_score,
                                    sufficiency_score=v.sufficiency_score)
            for k, v in aggregated.items()
        ],
    )

    result = InitialReviewResult(
        run_id="fix_e",
        bundle=bundle,
        decisions=decisions,
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(should_stop=True, reason="threshold_met"),
        core_trace=core_trace,
    )

    expected = {
        "should_escalate": True,
        "escalated_subclaim_ids": {"sc_001"},
        "sc_001_reason_codes": {"low_support", "low_sufficiency"},  # no material_contradiction
        "review_not_complete_trigger": False,
        "critical_dissent_trigger": False,
        "dissent_count": 0,   # nobody contradicted → no dissent record
    }
    return result, expected


# ---------------------------------------------------------------------------
# Fixture F — Mixed domain ambiguity (two subclaims, different profiles)
#
# Models a general-domain review where one subclaim is unambiguously clean
# and a second is legally ambiguous: high support from general reviewers but
# active contradiction from the risk_sentinel profile.
#
# sc_001 (factual): support=0.90, contradiction=0.05 → clean, no escalation
# sc_002 (normative): support=0.72, contradiction=0.38, sufficiency=0.60
#         → MATERIAL_CONTRADICTION + LOW_SUFFICIENCY
#
# Jurors on sc_002: 3 support (general), 2 contradict (risk_sentinel)
#   ratio = 2/5 = 0.40 → exactly at CRITICAL boundary → CRITICAL dissent
#
# completion.should_stop = True
# ---------------------------------------------------------------------------

def fixture_mixed_domain_ambiguity() -> tuple[InitialReviewResult, dict]:
    subclaims = [
        Subclaim(subclaim_id="sc_001", text="The study enrolled 500 patients.", kind=SubclaimKind.FACT),
        Subclaim(subclaim_id="sc_002", text="The treatment is broadly appropriate for all adults.", kind=SubclaimKind.NORMATIVE),
    ]
    bundle = ClaimBundle(bundle_id="fix_f", raw_content="Mixed domain test", subclaims=subclaims)

    decisions = [
        JurorDecision(juror_id="j1", profile_id="balanced_reviewer_v1", subclaim_id="sc_001",
                      supported=True, contradicted=False, sufficient=True, issuable=True, confidence=0.92),
        JurorDecision(juror_id="j2", profile_id="balanced_reviewer_v1", subclaim_id="sc_002",
                      supported=True, contradicted=False, sufficient=False, issuable=True, confidence=0.70),
        JurorDecision(juror_id="j3", profile_id="literal_parser_v1", subclaim_id="sc_002",
                      supported=True, contradicted=False, sufficient=False, issuable=True, confidence=0.65),
        JurorDecision(juror_id="j4", profile_id="balanced_reviewer_v1", subclaim_id="sc_002",
                      supported=True, contradicted=False, sufficient=True, issuable=True, confidence=0.75),
        JurorDecision(juror_id="j5", profile_id="risk_sentinel_v1", subclaim_id="sc_002",
                      supported=False, contradicted=True, sufficient=False, issuable=False, confidence=0.80),
        JurorDecision(juror_id="j6", profile_id="sceptical_verifier_v1", subclaim_id="sc_002",
                      supported=False, contradicted=True, sufficient=False, issuable=False, confidence=0.72),
    ]

    aggregated = {
        "sc_001": SubclaimDecision(subclaim_id="sc_001", support_score=0.90,
                                   contradiction_score=0.05, sufficiency_score=0.88,
                                   issuance_score=0.88),
        "sc_002": SubclaimDecision(subclaim_id="sc_002", support_score=0.72,
                                   contradiction_score=0.38, sufficiency_score=0.60,
                                   issuance_score=0.50),
    }

    core_trace = CoreTrace(
        run_id="fix_f",
        profile_set_selected="general_default_v1",
        subclaims=[MinimalTraceSubclaim(subclaim_id=s.subclaim_id, text=s.text) for s in subclaims],
        juror_votes=[
            MinimalTraceVote(juror_id=d.juror_id, subclaim_id=d.subclaim_id,
                             supported=d.supported, contradicted=d.contradicted,
                             sufficient=d.sufficient, confidence=d.confidence)
            for d in decisions
        ],
        aggregation_outcome=[
            MinimalTraceAggregation(subclaim_id=k, support_score=v.support_score,
                                    contradiction_score=v.contradiction_score,
                                    sufficiency_score=v.sufficiency_score)
            for k, v in aggregated.items()
        ],
    )

    result = InitialReviewResult(
        run_id="fix_f",
        bundle=bundle,
        decisions=decisions,
        aggregated_by_subclaim=aggregated,
        completion=CompletionDecision(should_stop=True, reason="threshold_met"),
        core_trace=core_trace,
    )

    expected = {
        "should_escalate": True,
        "escalated_subclaim_ids": {"sc_002"},       # sc_001 is clean
        "no_escalation_subclaim_ids": {"sc_001"},
        "sc_002_reason_codes": {"material_contradiction", "low_sufficiency"},
        "review_not_complete_trigger": False,
        "critical_dissent_trigger": True,           # sc_002: 2/5 = 0.40 ≥ CRITICAL threshold
        "dissent_severity_sc_002": "critical",
    }
    return result, expected
