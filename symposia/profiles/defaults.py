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
from symposia.models.profile import Profile, ProfileBehavior

BUILTIN_PROFILES = {
    "balanced_reviewer_v1": Profile(
        profile_id="balanced_reviewer_v1",
        label="Balanced Reviewer",
        purpose=(
            "Provide even-handed judgement. Accept claims when they are genuinely supported, "
            "reject them when they are genuinely undermined, and preserve uncertainty when that "
            "is the most faithful answer."
        ),
        behavior=ProfileBehavior(
            stance="balanced",
            literalism="medium",
            evidence_demand="medium",
            safety_bias="medium",
        ),
        weight=1.0,
        failure_modes=["may underweight edge-case risk"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "sceptical_verifier_v1": Profile(
        profile_id="sceptical_verifier_v1",
        label="Sceptical Verifier",
        purpose=(
            "Apply extra scrutiny to broad, confident, or weakly qualified claims. "
            "Prefer caution over overstatement, without punishing appropriately hedged language."
        ),
        behavior=ProfileBehavior(
            stance="sceptical",
            literalism="medium",
            evidence_demand="high",
            safety_bias="moderate",
        ),
        weight=1.05,
        failure_modes=["may over-escalate borderline claims"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "evidence_maximalist_v1": Profile(
        profile_id="evidence_maximalist_v1",
        label="Evidence Maximalist",
        purpose=(
            "Raise the threshold for sufficiency. Require strong grounding before treating a claim "
            "as trustworthy enough to rely on."
        ),
        behavior=ProfileBehavior(
            stance="strict",
            literalism="high",
            evidence_demand="high",
            safety_bias="moderate",
        ),
        weight=1.1,
        failure_modes=["may classify useful claims as insufficient"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "literal_parser_v1": Profile(
        profile_id="literal_parser_v1",
        label="Literal Parser",
        purpose=(
            "Judge the wording as written. Pay close attention to scope, qualifiers, and whether "
            "the literal statement outruns what can actually be defended."
        ),
        behavior=ProfileBehavior(
            stance="literal",
            literalism="high",
            evidence_demand="medium",
            safety_bias="medium",
        ),
        weight=1.0,
        failure_modes=["may underweight practical context"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "risk_sentinel_v1": Profile(
        profile_id="risk_sentinel_v1",
        label="Risk Sentinel",
        purpose=(
            "Prioritise harm prevention. If acting on a claim could cause meaningful harm, demand "
            "stronger support and stronger caveating before treating it as safe to rely on."
        ),
        behavior=ProfileBehavior(
            stance="risk-first",
            literalism="medium",
            evidence_demand="high",
            safety_bias="high",
        ),
        weight=1.2,
        failure_modes=["can be overly conservative on low-risk claims"],
        compatible_domains=["general", "medical", "legal", "finance"],
        version="v1",
    ),
    "medical_specialist_v1": Profile(
        profile_id="medical_specialist_v1",
        label="Medical Safety Specialist",
        purpose=(
            "Apply medical caution to treatment, medication, contraindication, and safety-sensitive "
            "claims. Preserve uncertainty where stronger clinical framing is needed."
        ),
        behavior=ProfileBehavior(
            stance="risk-first",
            literalism="high",
            evidence_demand="high",
            safety_bias="high",
        ),
        weight=1.15,
        failure_modes=[
            "may over-escalate low-risk medical claims",
            "may treat reasonable hedging as insufficiently decisive",
        ],
        compatible_domains=["medical"],
        version="v1",
    ),
    "legal_specialist_v1": Profile(
        profile_id="legal_specialist_v1",
        label="Legal Precision Specialist",
        purpose=(
            "Apply extra care to scope, jurisdiction, and interpretive dependence in legal or policy "
            "claims. Resist universal legal conclusions stated without sufficient boundary conditions."
        ),
        behavior=ProfileBehavior(
            stance="literal",
            literalism="high",
            evidence_demand="high",
            safety_bias="medium",
        ),
        weight=1.15,
        failure_modes=[
            "may over-penalise informal legal wording",
            "may miss broader safety concerns outside legal scope",
        ],
        compatible_domains=["legal"],
        version="v1",
    ),
    "finance_specialist_v1": Profile(
        profile_id="finance_specialist_v1",
        label="Finance Risk Specialist",
        purpose=(
            "Apply extra caution to predictive, risk, and investment claims. Penalise unsupported "
            "certainty, missing downside framing, and weak causal inference."
        ),
        behavior=ProfileBehavior(
            stance="risk-first",
            literalism="medium",
            evidence_demand="high",
            safety_bias="high",
        ),
        weight=1.15,
        failure_modes=[
            "may over-escalate optimistic but qualified forecasts",
            "may increase dissent on noisy market claims without improving convergence",
        ],
        compatible_domains=["finance"],
        version="v1",
    ),
}
