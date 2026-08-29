import json
from pathlib import Path

ATTEST = Path("docs/state/CHECKPOINT_DENOMINATOR_RECONCILIATION_ATTESTATION_2026-08-30.json")
GRAPH = Path("docs/state/META_GRAPH_DELTA_CHECKPOINT_RECONCILIATION_2026-08-30.json")


def test_drive_reconciliation_preserves_history_and_updates_dynamic_denominators():
    data = json.loads(ATTEST.read_text(encoding="utf-8"))
    assert data["precondition_reread"]["result"] == "PASS"
    assert data["write"]["result"] == "PASS"
    assert data["post_write_verification"]["result"] == "PASS"
    post = data["post_write_verification"]
    assert post["cp_1500_current"] == 690
    assert post["cp_intel_1000_current"] == 690
    assert post["cp_intel_1000_blocker"] == "CANONICAL_CAPACITY_690"
    assert post["cp_0800_graph_cutover"] == "686/686 COMPLETE historical preserved"
    assert post["cp_0800_current_l4"] == "105/690"
    assert post["cp_0800_current_l9"] == "0/690"
    assert post["H_0691_present"] is False
    assert post["all_send_allowed_zero"] is True


def test_attestation_has_no_authority_or_outbound_effect():
    data = json.loads(ATTEST.read_text(encoding="utf-8"))
    inv = data["hard_invariants"]
    assert inv["authority_advanced"] is False
    assert inv["h_id_allocations"] == 0
    assert inv["canonical_id_reservations"] == 0
    assert inv["source_mapping_changes"] == 0
    assert inv["crm_universe_complete"] is False
    assert inv["outbound"] == "CLOSED"
    assert inv["send_allowed"] == 0
    assert inv["external_irreversible_actions"] == 0
    assert data["concurrency"]["fencing_token"] == 3
    assert data["concurrency"]["entity_review_scope_touched"] is False
    assert data["concurrency"]["collision"] is False


def test_meta_graph_records_resolution_without_promoting_authority():
    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    node_ids = {n["id"] for n in data["nodes"]}
    assert "DEC-0103" in node_ids
    assert "DRIFT-CHECKPOINT-DENOMINATOR-686-690" in node_ids
    assert "AUTH-E4-690" in node_ids
    assert data["invariants"]["authority_advanced"] is False
    assert data["invariants"]["canonical_id_reservations"] == 0
    assert data["invariants"]["outbound"] == "CLOSED"
    assert data["invariants"]["send_allowed"] == 0
