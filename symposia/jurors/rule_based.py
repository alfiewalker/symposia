# ---------------------------------------------------------------------------
# Config-externalisation boundary note
# ---------------------------------------------------------------------------
# These hint tables ARE candidates for YAML externalisation, but only once
# the activation conditions in decide() are also externalised.  Right now
# the juror contains hard-coded checks like:
#   `behavior.safety_bias == "high" or behavior.stance in ("risk-first", "strict")`
# which mirror the ProfileBehavior field values in profiles/defaults.py.
# Externalising one without the other creates an invisible coupling: the YAML
# declares a stance but the code checks it as a string literal.
#
# Safe path to externalisation:
#   - Define ActivationRule objects that pair a hint set with its ProfileBehavior
#     condition declaratively.
#   - Replace the hard-coded conditionals in decide() with a loop over those rules.
#   - Only then can both the hints and the conditions live in config.
#
# Until that refactor, treat all three tables as code, not data.
# ---------------------------------------------------------------------------
from __future__ import annotations

from symposia.models.claim import Subclaim
from symposia.models.juror import JurorDecision

_UNSAFE_HINTS = (
    "skip emergency",
    "ignore jurisdiction",
    "guaranteed",
    "all retirement savings",
)

_INSUFFICIENT_HINTS = (
    "proven to work",
    "this treatment",
)

# Fired by profiles with safety_bias="high" or stance in ("risk-first", "strict"):
# an unsubstantiated total-safety claim is insufficient evidence.
#
# Primary tier: blunt, single-word or double-word safety overclaims.
# Paraphrase tier: clinical and consumer variants of the same semantic.
# Adding a phrase here is a cross-phase semantic change: test implications before editing.
_SAFETY_CLAIM_HINTS = (
    # primary tier
    "no side effects",
    "completely safe",
    "no risk",
    "always works",
    "zero risk",
    # paraphrase tier
    "no adverse effects",
    "no adverse reactions",
    "no known risks",
    "free from side effects",
    "negligible toxicity",
)

# Fired by profiles with evidence_demand="high":
# weak epistemic language signals an insufficient evidentiary basis.
#
# Primary tier: explicit epistemic hedges.
# Paraphrase tier: equivalent hedges in scientific and financial phrasing.
# Adding a phrase here is a cross-phase semantic change: test implications before editing.
_WEAK_EVIDENCE_HINTS = (
    # primary tier
    "may help",
    "some evidence suggests",
    "could be beneficial",
    "possibly effective",
    "anecdotal reports",
    # paraphrase tier
    "preliminary data",
    "early findings suggest",
    "limited evidence",
    "not yet conclusive",
)

_CONFIDENCE_SUPPORTED = {"low": 0.72, "medium": 0.82, "high": 0.88}
_CONFIDENCE_UNSUPPORTED = {"low": 0.20, "medium": 0.28, "high": 0.35}


class RuleBasedJuror:
    def __init__(self, juror_id: str, profile_id: str):
        self.juror_id = juror_id
        self.profile_id = profile_id

    def decide(self, subclaim: Subclaim) -> JurorDecision:
        from symposia.profiles import get_profile  # late import avoids circular dependency

        text = subclaim.text.lower()
        behavior = get_profile(self.profile_id).behavior

        contradicted = any(hint in text for hint in _UNSAFE_HINTS)

        # Hard insufficiency: all profiles apply.
        insufficient = any(hint in text for hint in _INSUFFICIENT_HINTS)

        # Safety claims: profiles with high safety_bias or risk-first/strict stance
        # flag unsubstantiated total-safety assertions as insufficiently evidenced.
        if not insufficient and (
            behavior.safety_bias == "high"
            or behavior.stance in ("risk-first", "strict")
        ):
            insufficient = any(hint in text for hint in _SAFETY_CLAIM_HINTS)

        # Weak evidence: profiles with high evidence_demand flag epistemic hedging.
        if not insufficient and behavior.evidence_demand == "high":
            insufficient = any(hint in text for hint in _WEAK_EVIDENCE_HINTS)

        supported = not contradicted and not insufficient
        sufficient = not insufficient
        issuable = supported and not contradicted

        demand = behavior.evidence_demand
        confidence = (
            _CONFIDENCE_SUPPORTED.get(demand, 0.82)
            if supported
            else _CONFIDENCE_UNSUPPORTED.get(demand, 0.28)
        )

        return JurorDecision(
            juror_id=self.juror_id,
            profile_id=self.profile_id,
            subclaim_id=subclaim.subclaim_id,
            supported=supported,
            contradicted=contradicted,
            sufficient=sufficient,
            issuable=issuable,
            confidence=confidence,
        )
