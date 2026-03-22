from __future__ import annotations

from collections import defaultdict

from symposia.models.escalation import (
    ChallengePacket,
    DissentRecord,
    DissentSeverity,
    EscalatedIssue,
    EscalationDecision,
    EscalationReason,
    NextStageReviewInput,
)
from symposia.models.initial import InitialReviewResult

# ---------------------------------------------------------------------------
# Escalation thresholds — imported from symposia.escalation.thresholds.
# Both the planner and the challenge runner use the same values so that
# "resolved" in Phase 6 is the exact inverse of "escalated" in Phase 5.
# ---------------------------------------------------------------------------
from symposia.escalation.thresholds import (
    CONTRADICTION_CEILING as _CONTRADICTION_CEILING,
    DISSENT_CRITICAL_RATIO as _DISSENT_CRITICAL_RATIO,
    DISSENT_MATERIAL_RATIO as _DISSENT_MATERIAL_RATIO,
    SUFFICIENCY_FLOOR as _SUFFICIENCY_FLOOR,
    SUPPORT_FLOOR as _SUPPORT_FLOOR,
)


def _build_dissent_records(initial_review_result: InitialReviewResult) -> list[DissentRecord]:
    """Build objection records from juror-level split signals.

    A DissentRecord captures *that jurors disagreed* — it is an observation,
    not an action.  Whether a dissent becomes a challenge is decided by
    plan_escalation(), not here.
    """
    by_subclaim: dict[str, list] = defaultdict(list)
    for decision in initial_review_result.decisions:
        by_subclaim[decision.subclaim_id].append(decision)

    dissent_records: list[DissentRecord] = []
    for subclaim_id, rows in by_subclaim.items():
        supporting = [row.juror_id for row in rows if row.supported]
        contradicting = [row.juror_id for row in rows if row.contradicted]
        if not supporting or not contradicting:
            continue

        contradiction_ratio = len(contradicting) / max(1, len(rows))
        if contradiction_ratio >= _DISSENT_CRITICAL_RATIO:
            severity = DissentSeverity.CRITICAL
        elif contradiction_ratio >= _DISSENT_MATERIAL_RATIO:
            severity = DissentSeverity.MATERIAL
        else:
            severity = DissentSeverity.MINOR

        dissent_records.append(
            DissentRecord(
                subclaim_id=subclaim_id,
                severity=severity,
                summary="Mixed supporting and contradicting juror signals.",
                supporting_jurors=supporting,
                contradicting_jurors=contradicting,
            )
        )

    return dissent_records


def _build_escalated_issues(initial_review_result: InitialReviewResult) -> list[EscalatedIssue]:
    """Identify subclaims that breach a score threshold.

    An EscalatedIssue is the *actionable* unit: it names a subclaim and the
    specific rules that triggered.  These issues become the payload of a
    ChallengePacket when escalation is decided.
    """
    issues: list[EscalatedIssue] = []
    for subclaim_id, decision in initial_review_result.aggregated_by_subclaim.items():
        reasons: list[EscalationReason] = []

        if decision.support_score < _SUPPORT_FLOOR:
            reasons.append(EscalationReason.LOW_SUPPORT)
        if decision.contradiction_score >= _CONTRADICTION_CEILING:
            reasons.append(EscalationReason.MATERIAL_CONTRADICTION)
        if decision.sufficiency_score < _SUFFICIENCY_FLOOR:
            reasons.append(EscalationReason.LOW_SUFFICIENCY)

        if reasons:
            issues.append(
                EscalatedIssue(
                    subclaim_id=subclaim_id,
                    reason_codes=reasons,
                    support_score=decision.support_score,
                    contradiction_score=decision.contradiction_score,
                    sufficiency_score=decision.sufficiency_score,
                )
            )

    return issues


def plan_escalation(initial_review_result: InitialReviewResult) -> EscalationDecision:
    issues = _build_escalated_issues(initial_review_result)
    dissents = _build_dissent_records(initial_review_result)

    triggers: list[EscalationReason] = []
    if not initial_review_result.completion.is_decisive:
        triggers.append(EscalationReason.REVIEW_NOT_COMPLETE)

    issue_reasons = {reason for issue in issues for reason in issue.reason_codes}
    triggers.extend(sorted(issue_reasons, key=lambda r: r.value))

    if any(d.severity == DissentSeverity.CRITICAL for d in dissents):
        triggers.append(EscalationReason.CRITICAL_DISSENT)

    should_escalate = bool(triggers)

    if not should_escalate:
        return EscalationDecision(
            should_escalate=False,
            trigger_reasons=[],
            escalated_issues=[],
            dissent_records=dissents,
            challenge_packet=None,
            next_stage_input=None,
        )

    challenge_packet = ChallengePacket(
        run_id=initial_review_result.run_id,
        profile_set_selected=initial_review_result.core_trace.profile_set_selected,
        escalated_issues=issues,
        dissent_records=dissents,
    )
    next_stage_input = NextStageReviewInput(
        parent_run_id=initial_review_result.run_id,
        challenge_packet=challenge_packet,
        max_rounds=1,
    )

    return EscalationDecision(
        should_escalate=True,
        trigger_reasons=triggers,
        escalated_issues=issues,
        dissent_records=dissents,
        challenge_packet=challenge_packet,
        next_stage_input=next_stage_input,
    )
