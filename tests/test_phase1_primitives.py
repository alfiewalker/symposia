import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.core
from pydantic import ValidationError

from symposia.kernel import HolisticSubclaimDecomposer, RuleBasedSubclaimDecomposer
from symposia.kernel import resolve_decomposer, resolve_decomposition_mode
from symposia.models import (
    Certainty,
    ClaimBundle,
    CompiledSubclaimVerdict,
    Issuance,
    Risk,
    Subclaim,
    ValidationResult,
    VerdictClass,
)


def _load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def test_holistic_decomposer_returns_single_subclaim_by_default():
    decomposer = HolisticSubclaimDecomposer()
    content = "Call emergency services immediately. Chest pain can indicate a heart attack."

    bundle_a = decomposer.decompose(content=content, domain="medical")
    bundle_b = decomposer.decompose(content=content, domain="medical")

    assert bundle_a.bundle_id == bundle_b.bundle_id
    assert len(bundle_a.subclaims) == 1
    assert bundle_a.subclaims[0].subclaim_id == "sc_001"
    assert bundle_a.subclaims[0].text == content
    assert bundle_a.subclaims[0].kind.value == "instruction"


def test_rule_based_decomposer_contract_and_determinism():
    decomposer = RuleBasedSubclaimDecomposer()
    content = "Call emergency services immediately. Chest pain can indicate a heart attack."

    bundle_a = decomposer.decompose(content=content, domain="medical")
    bundle_b = decomposer.decompose(content=content, domain="medical")

    assert bundle_a.bundle_id == bundle_b.bundle_id
    assert len(bundle_a.subclaims) == 2
    assert bundle_a.subclaims[0].subclaim_id == "sc_001"
    assert bundle_a.subclaims[1].subclaim_id == "sc_002"
    assert bundle_a.subclaims[0].kind.value == "instruction"


def test_claimbundle_round_trip_serialization_is_lossless():
    decomposer = RuleBasedSubclaimDecomposer()
    bundle = decomposer.decompose(
        content="Diversification reduces idiosyncratic risk.",
        domain="finance",
    )

    payload = bundle.to_canonical_json()
    round_tripped = ClaimBundle.model_validate_json(payload)

    assert round_tripped.to_canonical_dict() == bundle.to_canonical_dict()


def test_experimental_rule_based_decomposer_meets_golden_fixture_minima():
    fixtures = _load_jsonl(Path("benchmarks/locks/golden_cases.jsonl"))
    decomposer = RuleBasedSubclaimDecomposer()

    for fixture in fixtures:
        bundle = decomposer.decompose(
            content=fixture["content"],
            domain=fixture["domain"],
        )
        minimum_subclaims = fixture["expected"]["minimum_subclaims"]
        assert len(bundle.subclaims) >= minimum_subclaims


def test_compiled_subclaim_verdict_deterministic_serialization():
    verdict = CompiledSubclaimVerdict(
        subclaim_id="sc_001",
        verdict=VerdictClass.VALIDATED,
        certainty=Certainty.HIGH,
        issuance=Issuance.ISSUE_WITH_CAVEATS,
        risk=Risk.MEDIUM,
        caveats=["jurisdiction dependent"],
        agreement=0.82,
    )

    first = verdict.to_canonical_json()
    second = verdict.to_canonical_json()
    assert first == second
    assert "\n" not in first


def test_validation_result_deterministic_serialization():
    subclaim = CompiledSubclaimVerdict(
        subclaim_id="sc_001",
        verdict=VerdictClass.VALIDATED,
        certainty=Certainty.MODERATE,
        issuance=Issuance.ISSUE_WITH_CAVEATS,
        risk=Risk.HIGH,
        caveats=["requires regional emergency number"],
        agreement=0.78,
    )

    result = ValidationResult(
        run_id="spm_001",
        verdict=VerdictClass.VALIDATED,
        certainty=Certainty.MODERATE,
        issuance=Issuance.ISSUE_WITH_CAVEATS,
        risk=Risk.HIGH,
        agreement=0.78,
        summary="Supported with caveats.",
        caveats=["regional emergency number required"],
        subclaims=[subclaim],
        profile_set_used="medical_strict_v1",
        rounds_used=1,
        trace_id="tr_001",
    )

    first = result.to_canonical_json()
    second = result.to_canonical_json()
    assert first == second


def test_validation_result_rejects_out_of_range_agreement():
    with pytest.raises(ValidationError):
        ValidationResult(
            run_id="spm_002",
            verdict=VerdictClass.VALIDATED,
            certainty=Certainty.HIGH,
            issuance=Issuance.SAFE_TO_ISSUE,
            risk=Risk.LOW,
            agreement=1.5,
            summary="Invalid agreement.",
        )


def test_malformed_subclaim_fixture_rejected_cleanly():
    malformed_path = Path("tests/fixtures/malformed_subclaim.json")
    malformed_payload = json.loads(malformed_path.read_text(encoding="utf-8"))

    with pytest.raises(ValidationError):
        Subclaim.model_validate(malformed_payload)


# ── Decomposer resolver tests ────────────────────────────────────────


def test_resolve_decomposer_holistic_returns_holistic_instance():
    decomposer = resolve_decomposer("holistic")
    assert isinstance(decomposer, HolisticSubclaimDecomposer)


def test_resolve_decomposer_rule_based_returns_rule_based_instance():
    decomposer = resolve_decomposer("rule_based")
    assert isinstance(decomposer, RuleBasedSubclaimDecomposer)


def test_resolve_decomposer_default_is_holistic():
    decomposer = resolve_decomposer()
    assert isinstance(decomposer, HolisticSubclaimDecomposer)


def test_resolve_decomposer_rejects_unknown_mode():
    with pytest.raises(ValueError, match="Unknown decomposition mode"):
        resolve_decomposer("turbo")


def test_resolve_decomposition_mode_cli_wins_over_param_and_config():
    result = resolve_decomposition_mode(cli="rule_based", param="holistic", config_default="holistic")
    assert result == "rule_based"


def test_resolve_decomposition_mode_param_wins_over_config():
    result = resolve_decomposition_mode(param="rule_based", config_default="holistic")
    assert result == "rule_based"


def test_resolve_decomposition_mode_config_used_when_others_none():
    result = resolve_decomposition_mode(config_default="rule_based")
    assert result == "rule_based"


def test_resolve_decomposition_mode_defaults_to_holistic():
    result = resolve_decomposition_mode()
    assert result == "holistic"


def test_resolve_decomposition_mode_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown decomposition mode"):
        resolve_decomposition_mode(cli="bogus")


# ── Prompt builder personality injection tests ────────────────────────


def test_prompt_builder_injects_distinct_personality_per_profile():
    from symposia.jurors.llm import JurorPromptBuilder

    builder = JurorPromptBuilder()
    subclaim = Subclaim(subclaim_id="sc_001", text="Test claim.", kind="fact", depends_on=[])

    prompts = {}
    for pid in ["balanced_reviewer_v1", "sceptical_verifier_v1", "risk_sentinel_v1"]:
        role, _ = builder.build(
            subclaim=subclaim,
            domain="general",
            profile_id=pid,
            profile_set_id="general_default_v1",
        )
        prompts[pid] = role

    # Each profile must produce a different system prompt
    assert len(set(prompts.values())) == 3


def test_prompt_builder_system_prompt_contains_profile_fields():
    from symposia.jurors.llm import JurorPromptBuilder

    builder = JurorPromptBuilder()
    subclaim = Subclaim(subclaim_id="sc_001", text="Test claim.", kind="fact", depends_on=[])

    role, _ = builder.build(
        subclaim=subclaim, domain="general",
        profile_id="risk_sentinel_v1", profile_set_id="general_default_v1",
    )
    assert "Risk Sentinel" in role
    assert "risk-first" in role
    assert "high" in role  # evidence_demand and safety_bias
    assert "general claims and public-facing statements" in role


def test_prompt_builder_still_enforces_json_output_contract():
    from symposia.jurors.llm import JurorPromptBuilder

    builder = JurorPromptBuilder()
    subclaim = Subclaim(subclaim_id="sc_001", text="Test claim.", kind="fact", depends_on=[])

    role, prompt = builder.build(
        subclaim=subclaim, domain="general",
        profile_id="balanced_reviewer_v1", profile_set_id="general_default_v1",
    )
    assert "JSON" in role
    assert "JSON" in prompt
    assert "supported" in prompt
    assert "contradicted" in prompt
