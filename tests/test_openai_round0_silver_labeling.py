from __future__ import annotations

import pytest

pytestmark = pytest.mark.ladder

from symposia.smoke.openai_round0_silver_labeling import (
    SilverLabelCandidate,
    run_openai_round0_silver_labeling,
)


def test_silver_labeling_marks_outputs_provisional_and_emits_artifacts(monkeypatch, tmp_path) -> None:
    fake_comparison = {
        "summary": {
            "efficiency_worth_it_decision": False,
            "review_mode": "holistic_single_claim",
        },
        "case_results": [
            {
                "case": {"case_id": "c1"},
                "committee": {
                    "per_juror": [
                        {"juror_id": "j1", "contradicted": True, "confidence": 0.9, "parsed_ok": True, "error_code": None},
                        {"juror_id": "j2", "contradicted": True, "confidence": 0.9, "parsed_ok": True, "error_code": None},
                        {"juror_id": "j3", "contradicted": True, "confidence": 0.9, "parsed_ok": True, "error_code": None},
                    ]
                },
            }
        ],
    }

    monkeypatch.setattr(
        "symposia.smoke.openai_round0_silver_labeling.run_openai_round0_comparison",
        lambda **kwargs: fake_comparison,
    )

    report = run_openai_round0_silver_labeling(
        output_dir=str(tmp_path),
        candidates=[
            SilverLabelCandidate(
                case_id="c1",
                domain="general",
                content="sample",
                expected_escalation=True,
                split_id="development",
                slice_ids=["high_risk_overclaim"],
                source_type="benchmark",
                provenance_reference="unit-test",
            )
        ],
    )

    assert report["summary"]["label_tier"] == "tier_b_silver"
    assert report["summary"]["review_mode"] == "holistic_single_claim"
    assert "provisional trust assessment" in report["summary"]["claim_scope"]
    assert len(report["labels"]) == 1
    assert report["labels"][0]["provisional"] is True
    assert report["labels"][0]["review_mode"] == "holistic_single_claim"

    assert (tmp_path / "silver_summary.json").exists()
    assert (tmp_path / "silver_labels.json").exists()
    assert (tmp_path / "silver_rejections.json").exists()
    assert (tmp_path / "silver_summary.md").exists()
