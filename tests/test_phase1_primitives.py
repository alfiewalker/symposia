import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from symposia.kernel import RuleBasedSubclaimDecomposer
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


def test_golden_locked_fixtures_meet_min_subclaims():
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
