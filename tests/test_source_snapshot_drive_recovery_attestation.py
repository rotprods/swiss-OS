import json
from pathlib import Path

ATTEST = Path("docs/state/SOURCE_SNAPSHOT_DRIVE_RECOVERY_ATTESTATION_2026-08-30.json")


def test_source_snapshot_recovery_is_exact_but_non_authoritative():
    data = json.loads(ATTEST.read_text(encoding="utf-8"))
    source = data["source_snapshot"]
    assert source["snapshot_id"] == "HS-MEMBER-DE-33206402141"
    assert source["records"] == 2061
    assert source["pages"] == 172
    assert source["coverage_rows"] == 2061
    assert source["coverage_pct"] == 1.0
    assert source["ssr_equivalence"] is False
    assert data["drive_projection"]["exact_readback"] is True
    assert data["drive_projection"]["decision_id"] == "DEC-0104"


def test_mep_fallback_and_safety_are_fail_closed():
    data = json.loads(ATTEST.read_text(encoding="utf-8"))
    mep = data["mep_fallback"]
    assert mep["triggered"] is True
    assert mep["partial_state_qualified"] is False
    assert mep["final_state_qualified"] is True
    assert data["post_reconciliation_audit"]["stale_dynamic_686_remaining"] == 0
    assert data["concurrency"]["fencing_token"] == 3
    assert data["concurrency"]["source_recovery_scope_disjoint"] is True
    inv = data["hard_invariants"]
    assert inv["authority_advanced"] is False
    assert inv["h_id_allocations"] == 0
    assert inv["canonical_id_reservations"] == 0
    assert inv["source_mapping_changes"] == 0
    assert inv["crm_universe_complete"] is False
    assert inv["outbound"] == "CLOSED"
    assert inv["send_allowed"] == 0
    assert inv["external_irreversible_actions"] == 0
