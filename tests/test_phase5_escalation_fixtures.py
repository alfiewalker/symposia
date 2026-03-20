"""Fixture-driven escalation tests.

Each test loads a locked fixture (fully deterministic InitialReviewResult)
and asserts exact escalation behaviour against the frozen expected dict.

These tests are harder than the synthetic tests because:
- they use messy boundary values (0.349 vs 0.350)
- they cover multi-subclaim partial escalation
- they cover maximum-dissent scenarios with 6 jurors
"""
from __future__ import annotations

from symposia.escalation import plan_escalation
from symposia.models.escalation import DissentSeverity, EscalationReason

from tests.fixtures.escalation_fixtures import (
    fixture_contradiction_threshold_boundary,
    fixture_high_support_safety_caveat,
    fixture_low_support_no_contradiction,
    fixture_maximum_dissent,
    fixture_mixed_domain_ambiguity,
    fixture_multi_subclaim_partial,
)


def test_fixture_multi_subclaim_partial_escalation():
    result, expected = fixture_multi_subclaim_partial()
    decision = plan_escalation(result)

    assert decision.should_escalate is expected["should_escalate"]

    escalated_ids = {i.subclaim_id for i in decision.escalated_issues}
    assert escalated_ids == expected["escalated_subclaim_ids"]
    assert escalated_ids.isdisjoint(expected["no_escalation_subclaim_ids"])

    has_rnc = EscalationReason.REVIEW_NOT_COMPLETE in decision.trigger_reasons
    assert has_rnc is expected["review_not_complete_trigger"]

    has_cd = EscalationReason.CRITICAL_DISSENT in decision.trigger_reasons
    assert has_cd is expected["critical_dissent_trigger"]

    assert len(decision.dissent_records) >= expected["dissent_count_min"]

    # sc_001 must never appear in escalated issues
    assert "sc_001" not in escalated_ids


def test_fixture_contradiction_threshold_boundary():
    result, expected = fixture_contradiction_threshold_boundary()
    decision = plan_escalation(result)

    assert decision.should_escalate is expected["should_escalate"]

    escalated_ids = {i.subclaim_id for i in decision.escalated_issues}
    assert ("sc_below" in escalated_ids) is expected["sc_below_escalated"]
    assert ("sc_at" in escalated_ids) is expected["sc_at_escalated"]

    has_rnc = EscalationReason.REVIEW_NOT_COMPLETE in decision.trigger_reasons
    assert has_rnc is expected["review_not_complete_trigger"]

    # Verify the exact reason codes for sc_at — only MATERIAL_CONTRADICTION
    sc_at_issue = next(i for i in decision.escalated_issues if i.subclaim_id == "sc_at")
    assert {r.value for r in sc_at_issue.reason_codes} == expected["sc_at_reason_codes"]


def test_fixture_maximum_dissent():
    result, expected = fixture_maximum_dissent()
    decision = plan_escalation(result)

    assert decision.should_escalate is expected["should_escalate"]

    has_rnc = EscalationReason.REVIEW_NOT_COMPLETE in decision.trigger_reasons
    assert has_rnc is expected["review_not_complete_trigger"]

    has_cd = EscalationReason.CRITICAL_DISSENT in decision.trigger_reasons
    assert has_cd is expected["critical_dissent_trigger"]

    escalated_ids = {i.subclaim_id for i in decision.escalated_issues}
    assert escalated_ids == expected["escalated_subclaim_ids"]

    dissent_by_id = {d.subclaim_id: d for d in decision.dissent_records}
    assert dissent_by_id["sc_001"].severity == DissentSeverity.CRITICAL
    assert dissent_by_id["sc_002"].severity == DissentSeverity.CRITICAL

    # Dissents are objections; challenge_packet is the actionable forwarding unit
    assert decision.challenge_packet is not None
    assert len(decision.challenge_packet.escalated_issues) == 2
    assert len(decision.challenge_packet.dissent_records) == 2

    # next_stage_input packages both for the downstream consumer
    assert decision.next_stage_input is not None
    assert decision.next_stage_input.parent_run_id == result.run_id
    assert decision.next_stage_input.max_rounds >= 1


def test_fixture_high_support_safety_caveat():
    result, expected = fixture_high_support_safety_caveat()
    decision = plan_escalation(result)

    assert decision.should_escalate is expected["should_escalate"]

    escalated_ids = {i.subclaim_id for i in decision.escalated_issues}
    assert escalated_ids == expected["escalated_subclaim_ids"]

    sc_issue = next(i for i in decision.escalated_issues if i.subclaim_id == "sc_001")
    assert {r.value for r in sc_issue.reason_codes} == expected["sc_001_reason_codes"]

    # Support and sufficiency pass → those reasons must NOT appear
    assert EscalationReason.LOW_SUPPORT not in sc_issue.reason_codes
    assert EscalationReason.LOW_SUFFICIENCY not in sc_issue.reason_codes

    has_rnc = EscalationReason.REVIEW_NOT_COMPLETE in decision.trigger_reasons
    assert has_rnc is expected["review_not_complete_trigger"]

    has_cd = EscalationReason.CRITICAL_DISSENT in decision.trigger_reasons
    assert has_cd is expected["critical_dissent_trigger"]

    dissent_by_id = {d.subclaim_id: d for d in decision.dissent_records}
    assert dissent_by_id["sc_001"].severity == DissentSeverity.MATERIAL


def test_fixture_low_support_no_contradiction():
    result, expected = fixture_low_support_no_contradiction()
    decision = plan_escalation(result)

    assert decision.should_escalate is expected["should_escalate"]

    escalated_ids = {i.subclaim_id for i in decision.escalated_issues}
    assert escalated_ids == expected["escalated_subclaim_ids"]

    sc_issue = next(i for i in decision.escalated_issues if i.subclaim_id == "sc_001")
    assert {r.value for r in sc_issue.reason_codes} == expected["sc_001_reason_codes"]

    # Nobody contradicted → no dissent records
    assert len(decision.dissent_records) == expected["dissent_count"]

    has_rnc = EscalationReason.REVIEW_NOT_COMPLETE in decision.trigger_reasons
    assert has_rnc is expected["review_not_complete_trigger"]

    has_cd = EscalationReason.CRITICAL_DISSENT in decision.trigger_reasons
    assert has_cd is expected["critical_dissent_trigger"]


def test_fixture_mixed_domain_ambiguity():
    result, expected = fixture_mixed_domain_ambiguity()
    decision = plan_escalation(result)

    assert decision.should_escalate is expected["should_escalate"]

    escalated_ids = {i.subclaim_id for i in decision.escalated_issues}
    assert escalated_ids == expected["escalated_subclaim_ids"]
    assert escalated_ids.isdisjoint(expected["no_escalation_subclaim_ids"])

    sc_issue = next(i for i in decision.escalated_issues if i.subclaim_id == "sc_002")
    assert {r.value for r in sc_issue.reason_codes} == expected["sc_002_reason_codes"]

    has_rnc = EscalationReason.REVIEW_NOT_COMPLETE in decision.trigger_reasons
    assert has_rnc is expected["review_not_complete_trigger"]

    has_cd = EscalationReason.CRITICAL_DISSENT in decision.trigger_reasons
    assert has_cd is expected["critical_dissent_trigger"]

    dissent_by_id = {d.subclaim_id: d for d in decision.dissent_records}
    # sc_001 should have no dissent (clean, no contradicting jurors)
    assert "sc_001" not in dissent_by_id
    assert dissent_by_id["sc_002"].severity == DissentSeverity.CRITICAL
