from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from symposia.routing import get_route_set


pytestmark = pytest.mark.core


def test_trust_ladder_protocol_rungs_resolve_registered_routes() -> None:
    protocol_path = Path("symposia/smoke/protocol/trust_ladder_protocol.v1.yaml")
    protocol = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))

    assert protocol["version"] == "trust_ladder_protocol_v1_2026_03_22"

    rung_ids = [str(r["rung_id"]) for r in protocol["canonical_rungs"]]
    assert rung_ids == [
        "rung_1_single_weak",
        "rung_2_same_family_weak_committee",
        "rung_3_mixed_family_weak_committee",
        "rung_4_single_strong",
        "rung_5_smaller_stronger_committee",
    ]

    minimal_rungs = [str(v) for v in protocol["minimal_rungs_now"]]
    assert minimal_rungs == [
        "rung_1_single_weak",
        "rung_2_same_family_weak_committee",
        "rung_3_mixed_family_weak_committee",
        "rung_4_single_strong",
    ]

    for rung in protocol["canonical_rungs"]:
        committee_route = get_route_set(str(rung["committee_route_set_id"]))
        single_route = get_route_set(str(rung["single_route_set_id"]))
        assert committee_route.route_set_id == str(rung["committee_route_set_id"])
        assert single_route.route_set_id == str(rung["single_route_set_id"])
