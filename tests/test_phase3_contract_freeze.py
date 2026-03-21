import inspect
import pytest

pytestmark = pytest.mark.core


from symposia import (
    CompletionDecision,
    JurorDecision,
    InitialReviewEngine,
    InitialReviewResult,
    SubclaimDecision,
)
from symposia.models import CoreTrace


def test_phase3_contract_symbols_exported_and_stable():
    assert JurorDecision.__name__ == "JurorDecision"
    assert CompletionDecision.__name__ == "CompletionDecision"
    assert SubclaimDecision.__name__ == "SubclaimDecision"
    assert InitialReviewResult.__name__ == "InitialReviewResult"
    assert CoreTrace.__name__ == "CoreTrace"


def test_round0_engine_run_signature_stable():
    signature = inspect.signature(InitialReviewEngine.run)
    params = list(signature.parameters.keys())
    assert params == ["self", "content", "domain", "profile_set", "profile"]
