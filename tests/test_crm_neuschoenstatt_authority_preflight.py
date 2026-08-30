import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "docs/state/CRM_NEUSCHOENSTATT_TERMINAL_AUTHORITY_PREFLIGHT_2026-08-30.json"
REVIEW = ROOT / "docs/state/SRR_NEUSCHOENSTATT_ALIAS_EXISTING_REVIEW_2026-08-30.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_preflight_fails_closed_without_db_first_input():
    p = load(PREFLIGHT)
    r = load(REVIEW)
    assert p["parent_git_sha"] == "5b1d556f37c5ed2e2fe845a75207110dc2db39b3"
    assert p["source_record_key"] == r["source_record_key"] == "MD-33d867e983644585e4b2"
    assert p["proposed_action"] == r["resolution_review"]["action"] == "ALIAS_EXISTING"
    assert p["canonical_target"] == r["canonical_target"]["hotel_id"] == "H-0114"
    cp = p["live_cross_plane_readback"]
    assert cp["HOTELS_V2"]["present"] is True
    assert cp["HOTEL_INTELLIGENCE_V1"]["present"] is True
    assert cp["GRAPH_NODES_V2"]["present"] is True
    assert cp["ENTITY_RESOLUTION"]["source_record_key_present"] is False
    gate = p["authority_gate"]
    assert gate["eligible_now"] is False
    assert gate["blocker_code"] == "CONSTRAINED_DB_FIRST_TRANSACTION_INPUT_UNAVAILABLE"
    assert p["capability_probe"]["native_google_sheets_writer"] == "AVAILABLE_CANARY_VERIFIED"
    assert p["capability_probe"]["current_authoritative_sqlite_mutable_binary"] == "NOT_DISCOVERED_IN_CURRENT_DRIVE_OR_LIBRARY_RECOVERY_SEARCH"
    effect = p["effect_this_wave"]
    assert effect["authority_advanced"] is False
    assert effect["terminal_source_mappings"] == 657
    assert effect["reconcile_required"] == 1404
    assert effect["h_id_allocations"] == effect["canonical_id_reservations"] == 0
    assert effect["outbound"] == "CLOSED" and effect["send_allowed"] == 0
    assert effect["irreversible_external_actions"] == 0


def test_projected_effect_changes_only_mapping_frontier():
    p = load(PREFLIGHT)["projected_after_successful_authority_commit"]
    assert p == {
        "active_canonical": 690,
        "terminal_source_mappings": 658,
        "unique_canonical_targets": 656,
        "reconcile_required": 1403,
        "reverse_authority_source_gaps": 34,
        "next_h_id": "H-0691_UNALLOCATED",
        "h_id_allocations": 0,
    }


def test_preflight_packet_hash_is_deterministic():
    p = load(PREFLIGHT)
    expected = p.pop("packet_sha256")
    canonical = json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected
