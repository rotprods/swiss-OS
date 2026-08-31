from __future__ import annotations

import hashlib
import json
from pathlib import Path


STATE = Path(__file__).parents[1] / "docs/state/CRM_CURRENT_GONTEN_ECV_SRR_LINEAGE_33339392661.json"


def _load() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8"))


def test_current_gonten_lineage_is_exact_and_conservative() -> None:
    data = _load()
    assert data["parent_git_sha"] == "df375cf63200ed83fdc172ae7d1274e4bb458a34"
    assert data["source"]["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert data["source"]["coverage_complete"] is True
    assert data["source"]["records"] == 2061
    assert data["source"]["pages"] == 172

    transfers = data["transfers"]
    assert len(transfers) == 2
    assert {row["old_source_record_key"] for row in transfers} == {
        "MD-1776f584db74aa28b566",
        "MD-602d416c1e4106d2e085",
    }
    assert {row["new_source_record_key"] for row in transfers} == {
        "MD-a954ba352532b916caa2",
        "MD-5ab40d162390a7b74c5f",
    }
    assert {row["current_source_name"] for row in transfers} == {
        "Huus Bären 1602",
        "Huus Löwen 1878",
    }
    assert {row["current_first_party"]["address"] for row in transfers} == {
        "Dorfstrasse 40, 9108 Gonten",
        "Dorfstrasse 29, 9108 Gonten",
    }
    assert all(row["prior_review"]["action"] == "NEW_CANONICAL" for row in transfers)
    assert all(row["prior_review"]["canonical_comparator_id"] == "H-0063" for row in transfers)
    assert all(row["prior_review"]["canonical_comparator_property"] == "HUUS QUELL" for row in transfers)
    assert all(row["current_review"]["action"] == "NEW_CANONICAL_PREAUTH_RECONFIRMED" for row in transfers)
    assert all(row["current_review"]["mapping_state"] == "RECONCILE_REQUIRED" for row in transfers)
    assert all(row["current_review"]["canonical_h_id_reserved"] is False for row in transfers)
    assert all(row["current_review"]["h_id_allocated"] is False for row in transfers)
    assert all(row["current_review"]["operational_authority"] is False for row in transfers)


def test_current_gonten_lineage_preserves_authority_and_outbound_locks() -> None:
    data = _load()
    authority = data["authority"]
    frontier = data["frontier"]
    qa = data["qa"]

    assert authority["epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert authority["effect"] == "NONE"
    assert authority["canonical_rows"] == 690
    assert authority["next_physical_id"] == "H-0691_UNALLOCATED"
    assert frontier["terminal_source_mappings"] == 658
    assert frontier["reconcile_required"] == 1403
    assert frontier["canonical_id_reservations"] == 0
    assert frontier["h_id_allocations"] == 0
    assert qa["old_source_keys_not_reused_as_current"] is True
    assert qa["fuzzy_autobind"] is False
    assert qa["authority_advanced"] is False
    assert qa["crm_universe_complete"] is False
    assert qa["outbound"] == "CLOSED"
    assert qa["send_allowed"] == 0
    assert qa["irreversible_external_actions"] == 0


def test_current_gonten_lineage_payload_hash_is_self_validating() -> None:
    data = _load()
    expected = data.pop("payload_sha256")
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == expected
