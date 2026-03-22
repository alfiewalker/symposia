from __future__ import annotations

import pytest

pytestmark = pytest.mark.ladder

from pathlib import Path

from symposia.smoke.openai_initial_trust_evaluation import (
    run_committee_trust_decomposition_experiment,
    run_openai_initial_trust_evaluation,
    run_openai_initial_trust_evaluation_v2,
)


def test_trust_runner_emits_required_artifacts_and_downgrades_on_sample_gate_fail(monkeypatch, tmp_path) -> None:
    fake_comparison = {
        "summary": {
            "efficiency_worth_it_decision": False,
        },
        "case_results": [
            {
                "case": {"case_id": "hard_general_fasting_reversal_claim", "expected_escalation": True},
                "single": {
                    "agreement": 1.0,
                    "escalation": True,
                    "completion_reason": "ok",
                    "per_juror": [
                        {
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.9,
                            "parsed_ok": True,
                            "error_code": None,
                        }
                    ],
                },
                "committee": {
                    "agreement": 0.75,
                    "escalation": True,
                    "completion_reason": "ok",
                    "per_juror": [
                        {
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.9,
                            "parsed_ok": True,
                            "error_code": None,
                        },
                        {
                            "supported": False,
                            "contradicted": True,
                            "sufficient": False,
                            "confidence": 0.85,
                            "parsed_ok": True,
                            "error_code": None,
                        },
                    ],
                },
            }
        ],
    }

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation.run_openai_initial_comparison",
        lambda **kwargs: fake_comparison,
    )

    report = run_openai_initial_trust_evaluation(
        output_dir=str(tmp_path),
    )

    assert report["summary"]["review_mode"] == "holistic_single_claim"
    assert report["summary"]["decomposition_mode"] == "no_decomposition"
    assert report["summary"]["final_decision"] == "insufficient_trust_evidence"
    assert report["summary"]["overall_default_status"] == "committee_opt_in"
    assert report["summary"]["trust_default_support"] is False

    required = [
        "trust_summary.json",
        "trust_summary.md",
        "agreement.json",
        "dissent.json",
        "independence.json",
        "trace_completeness.json",
        "trust_decision.md",
        "resolved_protocol.json",
    ]
    for name in required:
        assert (Path(tmp_path) / name).exists()


def test_trust_runner_tier_b_blocks_strongest_committee_default_claim(monkeypatch, tmp_path) -> None:
    fake_comparison = {
        "summary": {
            "efficiency_worth_it_decision": True,
        },
        "case_results": [
            {
                "case": {"case_id": "hard_general_fasting_reversal_claim", "expected_escalation": True},
                "single": {
                    "agreement": 1.0,
                    "escalation": True,
                    "completion_reason": "ok",
                    "per_juror": [{"supported": True, "contradicted": False, "sufficient": True, "confidence": 0.9, "parsed_ok": True, "error_code": None}],
                },
                "committee": {
                    "agreement": 1.0,
                    "escalation": True,
                    "completion_reason": "ok",
                    "per_juror": [
                        {"supported": True, "contradicted": False, "sufficient": True, "confidence": 0.9, "parsed_ok": True, "error_code": None},
                        {"supported": True, "contradicted": False, "sufficient": True, "confidence": 0.9, "parsed_ok": True, "error_code": None},
                        {"supported": False, "contradicted": True, "sufficient": False, "confidence": 0.85, "parsed_ok": True, "error_code": None},
                    ],
                },
            }
        ],
    }

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation.run_openai_initial_comparison",
        lambda **kwargs: fake_comparison,
    )
    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation._sample_size_gates",
        lambda rows, sample_gates, manifest: [
            type("Gate", (), {"metric": "global_min_cases", "passed": True, "reason": "ok"})(),
            type("Gate", (), {"metric": "per_slice_min_cases", "passed": True, "reason": "ok"})(),
        ],
    )

    report = run_openai_initial_trust_evaluation(output_dir=str(tmp_path), evidence_label_tier="tier_b_silver")
    assert report["summary"]["review_mode"] == "holistic_single_claim"
    assert report["summary"]["final_decision"] == "committee_opt_in_supported"
    assert report["summary"]["overall_default_status"] == "committee_opt_in"
    assert report["summary"]["trust_default_support"] is False


def test_trust_runner_tier_c_allows_committee_default_when_conditions_hold(monkeypatch, tmp_path) -> None:
    fake_comparison = {
        "summary": {
            "efficiency_worth_it_decision": True,
        },
        "case_results": [
            {
                "case": {"case_id": "hard_general_fasting_reversal_claim", "expected_escalation": True},
                "single": {
                    "agreement": 1.0,
                    "escalation": True,
                    "completion_reason": "ok",
                    "per_juror": [{"supported": True, "contradicted": False, "sufficient": True, "confidence": 0.9, "parsed_ok": True, "error_code": None}],
                },
                "committee": {
                    "agreement": 1.0,
                    "escalation": True,
                    "completion_reason": "ok",
                    "per_juror": [
                        {"supported": True, "contradicted": False, "sufficient": True, "confidence": 0.9, "parsed_ok": True, "error_code": None},
                        {"supported": True, "contradicted": False, "sufficient": True, "confidence": 0.9, "parsed_ok": True, "error_code": None},
                        {"supported": False, "contradicted": True, "sufficient": False, "confidence": 0.85, "parsed_ok": True, "error_code": None},
                    ],
                },
            }
        ],
    }

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation.run_openai_initial_comparison",
        lambda **kwargs: fake_comparison,
    )
    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation._sample_size_gates",
        lambda rows, sample_gates, manifest: [
            type("Gate", (), {"metric": "global_min_cases", "passed": True, "reason": "ok"})(),
            type("Gate", (), {"metric": "per_slice_min_cases", "passed": True, "reason": "ok"})(),
        ],
    )

    report = run_openai_initial_trust_evaluation(output_dir=str(tmp_path), evidence_label_tier="tier_c_human")
    assert report["summary"]["review_mode"] == "holistic_single_claim"
    assert report["summary"]["final_decision"] == "committee_default_supported"
    assert report["summary"]["overall_default_status"] == "committee_default_supported"
    assert report["summary"]["trust_default_support"] is True


def test_trust_runner_v2_emits_rubric_artifacts(monkeypatch, tmp_path) -> None:
    fake_comparison = {
        "summary": {
            "efficiency_worth_it_decision": False,
        },
        "case_results": [
            {
                "case": {
                    "case_id": "trust_v2_holdout_lowrisk_01",
                    "expected_escalation": False,
                },
                "single": {
                    "agreement": 1.0,
                    "escalation": False,
                    "completion_reason": "ok",
                    "per_juror": [
                        {
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.8,
                            "parsed_ok": True,
                            "error_code": None,
                        }
                    ],
                },
                "committee": {
                    "agreement": 1.0,
                    "escalation": False,
                    "completion_reason": "ok",
                    "per_juror": [
                        {
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.8,
                            "parsed_ok": True,
                            "error_code": None,
                        },
                        {
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.7,
                            "parsed_ok": True,
                            "error_code": None,
                        },
                    ],
                },
            }
        ],
    }

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation.run_openai_initial_comparison",
        lambda **kwargs: fake_comparison,
    )

    report = run_openai_initial_trust_evaluation_v2(
        output_dir=str(tmp_path),
        committee_route_set_id="default_initial_openai_nano",
        single_route_set_id="default_initial_openai_nano",
        split_id="holdout",
        cases=[],
    )

    assert report["run_metadata"]["route_set_id"] == "default_initial_openai_nano"
    assert report["run_metadata"]["committee_route_set_id"] == "default_initial_openai_nano"
    assert report["run_metadata"]["single_route_set_id"] == "default_initial_openai_nano"
    assert report["run_metadata"]["review_mode"] == "holistic_single_claim"
    assert report["summary"]["review_mode"] == "holistic_single_claim"
    assert report["summary"]["rubric_case_count_scored"] == 1
    assert (Path(tmp_path) / "rubric_per_case.json").exists()
    assert (Path(tmp_path) / "rubric_summary.json").exists()
    assert (Path(tmp_path) / "rubric_default_proof.json").exists()


def test_trust_runner_v2_blocks_committee_default_without_proof_gates(monkeypatch, tmp_path) -> None:
    fake_comparison = {
        "summary": {
            "efficiency_worth_it_decision": True,
        },
        "case_results": [
            {
                "case": {
                    "case_id": "trust_v2_holdout_danger_01",
                    "expected_escalation": True,
                },
                "single": {
                    "agreement": 1.0,
                    "escalation": True,
                    "completion_reason": "ok",
                    "per_juror": [
                        {
                            "supported": False,
                            "contradicted": True,
                            "sufficient": False,
                            "confidence": 0.9,
                            "parsed_ok": True,
                            "error_code": None,
                        }
                    ],
                },
                "committee": {
                    "agreement": 1.0,
                    "escalation": False,
                    "completion_reason": "ok",
                    "per_juror": [
                        {
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.95,
                            "parsed_ok": True,
                            "error_code": None,
                        },
                        {
                            "supported": True,
                            "contradicted": False,
                            "sufficient": True,
                            "confidence": 0.95,
                            "parsed_ok": True,
                            "error_code": None,
                        },
                    ],
                },
            }
        ],
    }

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation.run_openai_initial_comparison",
        lambda **kwargs: fake_comparison,
    )
    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation._build_trust_decision",
        lambda **kwargs: {
            "efficiency_default_support": True,
            "trust_default_support": True,
            "overall_default_status": "committee_default_supported",
            "trust_worth_it_decision": True,
            "final_decision": "committee_default_supported",
            "reason": "forced_in_test",
        },
    )
    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation._sample_size_gates",
        lambda rows, sample_gates, manifest: [
            type("Gate", (), {"metric": "global_min_cases", "passed": True, "reason": "ok"})(),
            type("Gate", (), {"metric": "per_slice_min_cases", "passed": True, "reason": "ok"})(),
        ],
    )

    report = run_openai_initial_trust_evaluation_v2(
        output_dir=str(tmp_path),
        committee_route_set_id="default_initial_openai_nano",
        single_route_set_id="default_initial_openai_nano",
        split_id="holdout",
        cases=[],
        evidence_label_tier="tier_c_human",
    )

    assert report["summary"]["final_decision"] == "committee_opt_in_supported"
    assert report["summary"]["trust_default_support"] is False
    assert report["rubric_default_proof"]["all_required_passed"] is False
    assert "no_hard_fail_triggered" in report["rubric_default_proof"]["blocked_reasons"]


def test_trust_runner_v2_normalizes_runtime_domains(monkeypatch, tmp_path) -> None:
    captured_domains: list[str] = []

    def _fake_comparison(**kwargs):
        for c in kwargs.get("cases", []):
            captured_domains.append(c.domain)
        return {
            "summary": {"efficiency_worth_it_decision": False},
            "case_results": [
                {
                    "case": {"case_id": "trust_v2_holdout_highstakes_01", "expected_escalation": True},
                    "single": {
                        "agreement": 1.0,
                        "escalation": True,
                        "completion_reason": "ok",
                        "per_juror": [
                            {
                                "supported": False,
                                "contradicted": True,
                                "sufficient": False,
                                "confidence": 0.8,
                                "parsed_ok": True,
                                "error_code": None,
                            }
                        ],
                    },
                    "committee": {
                        "agreement": 1.0,
                        "escalation": True,
                        "completion_reason": "ok",
                        "per_juror": [
                            {
                                "supported": False,
                                "contradicted": True,
                                "sufficient": False,
                                "confidence": 0.8,
                                "parsed_ok": True,
                                "error_code": None,
                            }
                        ],
                    },
                }
            ],
        }

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation.run_openai_initial_comparison",
        _fake_comparison,
    )

    report = run_openai_initial_trust_evaluation_v2(
        output_dir=str(tmp_path),
        committee_route_set_id="default_initial_openai_nano",
        single_route_set_id="default_initial_openai_nano",
        split_id="holdout",
        cases=[
            type(
                "Case",
                (),
                {
                    "case_id": "trust_v2_holdout_highstakes_01",
                    "domain": "high_risk",
                    "content": "x",
                    "expected_escalation": True,
                },
            )()
        ],
    )

    assert report["summary"]["case_count"] == 1
    assert captured_domains == ["general"]


def test_committee_trust_decomposition_experiment_emits_cross_arm_outputs(monkeypatch, tmp_path) -> None:
    def fake_v2_run(**kwargs):
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        committee_route_set_id = kwargs["committee_route_set_id"]
        if committee_route_set_id == "single_initial_openai_nano_balanced_v1":
            target_match = 0.2
            weighted_score = 1.4
        elif committee_route_set_id == "committee_initial_openai_nano_triplet_v1":
            target_match = 0.3
            weighted_score = 1.6
        else:
            target_match = 0.4
            weighted_score = 1.8

        (output_dir / "rubric_per_case.json").write_text(
            """[
  {"case_id": "trust_v2_dev_lowrisk_01", "target_match": true, "weighted_score": 2.0},
  {"case_id": "trust_v2_dev_highstakes_01", "target_match": false, "weighted_score": 1.0}
]\n""",
            encoding="utf-8",
        )
        return {
            "summary": {
                "rubric_target_match_rate": target_match,
                "rubric_average_weighted_score": weighted_score,
                "weighted_agreement_rate": target_match,
                "critical_dissent_rate": 0.1,
                "trace_completeness_score": 1.0,
                "case_count": 2,
                "final_decision": "committee_opt_in_supported",
            }
        }

    monkeypatch.setattr(
        "symposia.smoke.openai_initial_trust_evaluation.run_openai_initial_trust_evaluation_v2",
        fake_v2_run,
    )

    report = run_committee_trust_decomposition_experiment(
        output_dir=str(tmp_path),
        split_id="development",
    )

    assert (tmp_path / "arm_comparison_summary.json").exists()
    assert (tmp_path / "arm_slice_comparison.json").exists()
    assert (tmp_path / "experiment_readout.md").exists()
    assert report["arm_comparison_summary"]["comparisons"]["plurality_effect_arm2_minus_arm1"]["rubric_target_match_rate"] == 0.1
    assert report["arm_comparison_summary"]["comparisons"]["cross_family_diversity_effect_arm3_minus_arm2"]["rubric_average_weighted_score"] == 0.2
