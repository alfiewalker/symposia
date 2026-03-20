# ---------------------------------------------------------------------------
# Config-externalisation boundary note
# ---------------------------------------------------------------------------
# Governing rule: do not externalise any field unless its meaning is already
# owned by one typed model and one evaluation path.  If a field is checked in
# multiple places or via string literals, moving it to YAML relocates the
# coupling without breaking it.
#
# YAML-ready fields (stable data — these can move to profiles.yaml once a
# config loader for profiles exists):
#   profile_id, label, purpose, failure_modes, compatible_domains, version
#   behavior.stance, behavior.literalism, behavior.evidence_demand,
#   behavior.safety_bias
#
# Must stay in code (behaviour semantics, not data):
#   The ProfileBehavior field *values* drive conditional logic in
#   RuleBasedJuror.decide() — specifically the hint-tier activation checks
#   on `behavior.safety_bias`, `behavior.stance`, and `behavior.evidence_demand`.
#   Moving the values without also moving those conditionals creates a split
#   where the data says one thing and the code assumes another.
#   Resolution: externalise profiles.yaml only after the juror reads its
#   activation conditions generically from ProfileBehavior, not from
#   hard-coded field comparisons.
# ---------------------------------------------------------------------------
from symposia.models.profile import Profile, ProfileBehavior

BUILTIN_PROFILES = {
    "balanced_reviewer_v1": Profile(
        profile_id="balanced_reviewer_v1",
        label="Balanced Reviewer",
        purpose="Neutral factual review.",
        behavior=ProfileBehavior(
            stance="balanced",
            literalism="medium",
            evidence_demand="medium",
            safety_bias="medium",
        ),
        weight=1.0,
        failure_modes=["may under-escalate edge risks"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "sceptical_verifier_v1": Profile(
        profile_id="sceptical_verifier_v1",
        label="Sceptical Verifier",
        purpose="Challenge weak support and overclaiming.",
        behavior=ProfileBehavior(
            stance="sceptical",
            literalism="medium",
            evidence_demand="high",
            safety_bias="moderate",
        ),
        weight=1.05,
        failure_modes=["may over-escalate borderline cases"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "evidence_maximalist_v1": Profile(
        profile_id="evidence_maximalist_v1",
        label="Evidence Maximalist",
        purpose="Demand stronger evidence quality and corroboration.",
        behavior=ProfileBehavior(
            stance="strict",
            literalism="high",
            evidence_demand="high",
            safety_bias="moderate",
        ),
        weight=1.1,
        failure_modes=["can mark useful claims as insufficient"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "literal_parser_v1": Profile(
        profile_id="literal_parser_v1",
        label="Literal Parser",
        purpose="Focus on wording precision and scope.",
        behavior=ProfileBehavior(
            stance="literal",
            literalism="high",
            evidence_demand="medium",
            safety_bias="medium",
        ),
        weight=1.0,
        failure_modes=["may miss practical context"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "risk_sentinel_v1": Profile(
        profile_id="risk_sentinel_v1",
        label="Risk Sentinel",
        purpose="Surface harm and issuance caution.",
        behavior=ProfileBehavior(
            stance="risk-first",
            literalism="medium",
            evidence_demand="high",
            safety_bias="high",
        ),
        weight=1.2,
        failure_modes=["can be too conservative on low-risk claims"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "medical_specialist_v1": Profile(
        profile_id="medical_specialist_v1",
        label="Medical Safety Specialist",
        purpose=(
            "Catches: unsubstantiated total-safety assertions ('completely safe', 'no adverse effects', "
            "'negligible toxicity') and weak-evidence clinical recommendations ('preliminary data', "
            "'limited evidence'). Does NOT fire on: mechanism-of-action statements, pharmacology "
            "definitions, or factual clinical thresholds that make no safety overclaim."
        ),
        behavior=ProfileBehavior(
            stance="risk-first",
            literalism="high",
            evidence_demand="high",
            safety_bias="high",
        ),
        weight=1.15,
        failure_modes=[
            "over-escalates weak but harmless medical claims that use safety-claim language colloquially",
            "may flag appropriately hedged disclaimers as insufficient when context makes them reasonable",
        ],
        compatible_domains=["medical"],
        version="v1",
    ),
    "legal_specialist_v1": Profile(
        profile_id="legal_specialist_v1",
        label="Legal Precision Specialist",
        purpose=(
            "Catches: weak evidentiary basis for legal recommendations ('preliminary data', "
            "'limited evidence', 'not yet conclusive'). Does NOT fire on: standard doctrinal "
            "statements, procedural descriptions, or statutory definitions that rely on authoritative "
            "sources rather than hedged inductive evidence."
        ),
        behavior=ProfileBehavior(
            stance="literal",
            literalism="high",
            evidence_demand="high",
            safety_bias="medium",
        ),
        weight=1.15,
        failure_modes=[
            "may flag imprecise but legally acceptable informal language as insufficient",
            "does not catch safety overclaims (safety_bias=medium) — rely on risk_sentinel for that",
        ],
        compatible_domains=["legal"],
        version="v1",
    ),
    "finance_specialist_v1": Profile(
        profile_id="finance_specialist_v1",
        label="Finance Risk Specialist",
        purpose=(
            "Catches: unsubstantiated investment safety claims ('no risk', 'no known risks', "
            "'completely safe') and weak-evidence financial guidance ('preliminary data', "
            "'early findings suggest', 'limited evidence'). Does NOT fire on: standard portfolio "
            "theory statements, historical return facts, or appropriately qualified projections "
            "that do not use safety-overclaim or weak-evidence language."
        ),
        behavior=ProfileBehavior(
            stance="risk-first",
            literalism="medium",
            evidence_demand="high",
            safety_bias="high",
        ),
        weight=1.15,
        failure_modes=[
            "may over-escalate optimistic but qualified financial projections",
            "combined safety_bias=high + evidence_demand=high means it fires on two hint tiers "
            "independently — review both before asserting a false-positive",
        ],
        compatible_domains=["finance"],
        version="v1",
    ),
}
