import json
from pathlib import Path

PLAN = Path("docs/state/CHECKPOINT_DENOMINATOR_RECONCILIATION_PLAN_2026-08-30.json")


def test_reconciliation_updates_only_control_plane_projection_fields():
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    mutations = data["mutations"]
    ids = {m["checkpoint_id"] for m in mutations}
    assert ids == {
        "CP-1500",
        "CP-INTEL-1000",
        "CP-INTEL-1500",
        "CP-2050-CANON",
        "CP-INTEL-2050-L1",
        "CP-0800-GRAPH-CUTOVER",
        "CP-0800-CURRENT-L4",
        "CP-0800-CURRENT-L9",
    }
    assert all(m["field"] in {"current", "target", "blocking_issues", "notes"} for m in mutations)
    inv = data["hard_invariants"]
    assert inv["authority_advanced"] is False
    assert inv["h_id_allocations"] == 0
    assert inv["canonical_id_reservations"] == 0
    assert inv["source_mapping_changes"] == 0
    assert inv["outbound"] == "CLOSED"
    assert inv["send_allowed"] == 0


def test_completed_graph_checkpoint_history_is_not_rewritten():
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    history = data["historical_semantics"]
    assert history["completed_checkpoint"] == "CP-0800-GRAPH-CUTOVER"
    assert history["completion_current"] == 686
    assert history["completion_target"] == 686
    assert history["rule"] == "PRESERVE_COMPLETION_TIME_NUMERATOR_AND_TARGET"
    graph_mutations = [m for m in data["mutations"] if m["checkpoint_id"] == "CP-0800-GRAPH-CUTOVER"]
    assert len(graph_mutations) == 1
    assert graph_mutations[0]["field"] == "notes"


def test_dynamic_denominators_reconcile_to_690_without_claiming_progress():
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    mutations = data["mutations"]
    by_key = {(m["checkpoint_id"], m["field"]): m for m in mutations}
    assert by_key[("CP-0800-CURRENT-L4", "target")]["new"] == 690
    assert by_key[("CP-0800-CURRENT-L9", "target")]["new"] == 690
    assert by_key[("CP-INTEL-1000", "current")]["new"] == 690
    assert by_key[("CP-INTEL-1000", "blocking_issues")]["new"] == "CANONICAL_CAPACITY_690"
    assert "105/690" in by_key[("CP-0800-CURRENT-L4", "notes")]["new"]
    assert "L9 remains 0" in by_key[("CP-0800-CURRENT-L9", "notes")]["new"]
