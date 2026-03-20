# ---------------------------------------------------------------------------
# Config-externalisation boundary note
# ---------------------------------------------------------------------------
# Governing rule: do not externalise any field unless its meaning is already
# owned by one typed model and one evaluation path.  If a field is checked in
# multiple places or via string literals, moving it to YAML relocates the
# coupling without breaking it.
#
# YAML-ready fields (stable data — these are purely declarative and have no
# companion code that would need to change simultaneously):
#   profile_set_id, domain, purpose, juror_count, profiles (list of IDs),
#   max_rounds, issuance_policy, calibration_snapshot
#   thresholds.support, thresholds.confidence
#
# Must stay in code until explicitly migrated:
#   DOMAIN_DEFAULT_PROFILE_SET (in the same file) — referenced by the
#   resolver and harness at import time; a YAML loader must be initialised
#   before any call that touches the registry, which requires a defined
#   bootstrap order that does not yet exist.
#
# Prerequisite for externalisation:
#   1. A ProfileSet YAML loader that runs before _PROFILE_SET_REGISTRY is
#      populated (i.e., before any import of profile_sets.__init__).
#   2. A test that the loaded registry is structurally identical to the
#      current hardcoded one (regression lock).
#   3. An explicit version field on each profile set entry so that YAML
#      changes can be detected without comparing full structures.
# ---------------------------------------------------------------------------
from symposia.models.profile import ProfileSet, ProfileSetThresholds

BUILTIN_PROFILE_SETS = {
    "general_default_v1": ProfileSet(
        profile_set_id="general_default_v1",
        domain="general",
        purpose="General factual validation baseline.",
        juror_count=5,
        profiles=[
            "balanced_reviewer_v1",
            "sceptical_verifier_v1",
            "literal_parser_v1",
            "evidence_maximalist_v1",
            "risk_sentinel_v1",
        ],
        thresholds=ProfileSetThresholds(support=0.70, confidence=0.70),
        max_rounds=2,
        issuance_policy="standard",
        calibration_snapshot="general_2026_q1",
    ),
    "medical_strict_v1": ProfileSet(
        profile_set_id="medical_strict_v1",
        domain="medical",
        purpose="Conservative medical validation with domain-specialist harm gate.",
        juror_count=5,
        profiles=[
            "risk_sentinel_v1",
            "evidence_maximalist_v1",
            "medical_specialist_v1",
            "sceptical_verifier_v1",
            "literal_parser_v1",
        ],
        thresholds=ProfileSetThresholds(support=0.80, confidence=0.82),
        max_rounds=2,
        issuance_policy="conservative",
        calibration_snapshot="medical_2026_q1",
    ),
    "legal_strict_v1": ProfileSet(
        profile_set_id="legal_strict_v1",
        domain="legal",
        purpose="Jurisdiction-sensitive legal validation with precision specialist.",
        juror_count=5,
        profiles=[
            "literal_parser_v1",
            "sceptical_verifier_v1",
            "evidence_maximalist_v1",
            "legal_specialist_v1",
            "risk_sentinel_v1",
        ],
        thresholds=ProfileSetThresholds(support=0.78, confidence=0.80),
        max_rounds=2,
        issuance_policy="cautious",
        calibration_snapshot="legal_2026_q1",
    ),
    "finance_strict_v1": ProfileSet(
        profile_set_id="finance_strict_v1",
        domain="finance",
        purpose="Finance recommendation and factual scrutiny with risk specialist.",
        juror_count=5,
        profiles=[
            "risk_sentinel_v1",
            "sceptical_verifier_v1",
            "evidence_maximalist_v1",
            "finance_specialist_v1",
            "balanced_reviewer_v1",
        ],
        thresholds=ProfileSetThresholds(support=0.77, confidence=0.79),
        max_rounds=2,
        issuance_policy="cautious",
        calibration_snapshot="finance_2026_q1",
    ),
}

DOMAIN_DEFAULT_PROFILE_SET = {
    "general": "general_default_v1",
    "medical": "medical_strict_v1",
    "legal": "legal_strict_v1",
    "finance": "finance_strict_v1",
}
