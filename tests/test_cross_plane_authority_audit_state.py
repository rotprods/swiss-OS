import json
from pathlib import Path

AUDIT = Path("docs/state/CROSS_PLANE_AUTHORITY_AUDIT_2026-08-30.json")


def test_visible_frontier_is_690_but_no_authority_promotion_is_claimed():
    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    checks = data["visible_plane_checks"]
    assert checks["github"]["authority_pointer_active_canonical"] == 690
    assert checks["drive_hotels_v2"]["H-0690_present"] is True
    assert checks["drive_hotels_v2"]["H-0691_present"] is False
    assert checks["drive_hotel_intelligence_v1"]["H-0690_present"] is True
    assert checks["drive_hotel_intelligence_v1"]["H-0691_present"] is False
    assert checks["drive_graph_v2"]["H-0690_hotel_node_present"] is True
    assert checks["drive_graph_v2"]["H-0690_intelligence_node_present"] is True
    assert checks["drive_graph_v2"]["H-0690_has_intelligence_edge_present"] is True
    assert data["audit_result"]["authority_promotion_eligible"] is False
    assert data["hard_invariants"]["authority_advanced"] is False


def test_stale_686_checkpoint_denominators_are_explicit_and_not_silently_authoritative():
    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    cp = data["visible_plane_checks"]["drive_checkpoint_registry"]
    assert cp["CP-0750_current"] == 690
    assert cp["CP-0800-GRAPH-CUTOVER_current"] == 686
    assert cp["CP-0800-CURRENT-L4_target"] == 686
    assert cp["CP-0800-CURRENT-L9_target"] == 686
    assert cp["CP-INTEL-1000_current"] == 686
    finding = data["findings"][0]
    assert finding["id"] == "DRIFT-CHECKPOINT-DENOMINATOR-686-690"
    assert finding["severity"] == "P1_OBSERVABILITY_CONTINUITY"
    assert "Do not patch these rows in isolation" in finding["repair_rule"]
    assert data["next_pointer"]["next_route"] == "CHECKPOINT_DENOMINATOR_RECONCILIATION_PREFLIGHT"
