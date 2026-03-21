import pytest

pytestmark = pytest.mark.core

from symposia.escalation import plan_escalation
from symposia.models import (
    CompletionDecision,
    CoreTrace,
    DissentSeverity,
    InitialReviewResult,
    JurorDecision,
    MinimalTraceAggregation,
    MinimalTraceSubclaim,
    MinimalTraceVote,
    SubclaimDecision,
)
from symposia.round0 import InitialReviewEngine


def test_escalation_contract_on_locked_safety_case():
    engine = InitialReviewEngine()
    result = engine.run(
        content="A patient with chest pain should skip emergency evaluation and self-treat at home.",
        domain="medical",
    )

    decision = plan_escalation(result)
    assert decision.should_escalate is True
    assert decision.trigger_reasons
    assert decision.escalated_issues
    assert decision.challenge_packet is not None
    assert decision.next_stage_input is not None
    assert decision.next_stage_input.max_rounds == 1


def test_escalation_contract_no_escalation_when_review_complete_and_clean():
    engine = InitialReviewEngine()
    result = engine.run(
        content="Water boils at lower temperatures at higher altitude due to lower atmospheric pressure.",
        domain="general",
    )

    decision = plan_escalation(result)
    assert decision.should_escalate is False
    assert decision.challenge_packet is None
    assert decision.next_stage_input is None


def test_escalation_contract_builds_dissent_and_critical_trigger():
    synthetic = InitialReviewResult(
        run_id="run_synthetic",
        bundle=InitialReviewEngine().run(
            content="Sample claim with mixed outcomes.",
            domain="general",
        ).bundle,
        decisions=[
            JurorDecision(
                juror_id="juror_1",
                profile_id="balanced_reviewer_v1",
                subclaim_id="sc_001",
                supported=True,
                contradicted=False,
                sufficient=True,
                issuable=True,
                confidence=0.8,
            ),
            JurorDecision(
                juror_id="juror_2",
                profile_id="risk_sentinel_v1",
                subclaim_id="sc_001",
                supported=False,
                contradicted=True,
                sufficient=True,
                issuable=False,
                confidence=0.4,
            ),
            JurorDecision(
                juror_id="juror_3",
                profile_id="sceptical_verifier_v1",
                subclaim_id="sc_001",
                supported=False,
                contradicted=True,
                sufficient=True,
                issuable=False,
                confidence=0.35,
            ),
        ],
        aggregated_by_subclaim={
            "sc_001": SubclaimDecision(
                subclaim_id="sc_001",
                support_score=0.33,
                contradiction_score=0.67,
                sufficiency_score=0.8,
                issuance_score=0.2,
            )
        },
        completion=CompletionDecision(should_stop=False, reason="escalation_candidate"),
        core_trace=CoreTrace(
            run_id="run_synthetic",
            profile_set_selected="general_default_v1",
            subclaims=[MinimalTraceSubclaim(subclaim_id="sc_001", text="Synthetic")],
            juror_votes=[
                MinimalTraceVote(juror_id="juror_1", subclaim_id="sc_001", supported=True, contradicted=False, sufficient=True, confidence=0.8),
                MinimalTraceVote(juror_id="juror_2", subclaim_id="sc_001", supported=False, contradicted=True, sufficient=True, confidence=0.4),
                MinimalTraceVote(juror_id="juror_3", subclaim_id="sc_001", supported=False, contradicted=True, sufficient=True, confidence=0.35),
            ],
            aggregation_outcome=[
                MinimalTraceAggregation(
                    subclaim_id="sc_001",
                    support_score=0.33,
                    contradiction_score=0.67,
                    sufficiency_score=0.8,
                )
            ],
        ),
    )

    decision = plan_escalation(synthetic)
    assert decision.should_escalate is True
    assert decision.dissent_records
    assert any(d.severity == DissentSeverity.CRITICAL for d in decision.dissent_records)
