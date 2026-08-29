import hashlib
import json
from pathlib import Path

REVIEW = Path("docs/state/SRET_PROVIDER_IDENTITY_050_REVIEW_WAVE01_33206402141.json")
NEXT = Path("docs/state/NEXT.json")
EXPECTED_KEYS = {
    "MD-93d88fb61a77fd5a967d",
    "MD-a5398d49d8ecd5b730d7",
    "MD-eaa9591c67a4016cf6c4",
    "MD-6a4331093c8de2eca2fb",
    "MD-6c3153de9fbb5a337f6f",
    "MD-c6bfaec6d1420cb70c35",
    "MD-699c71bb6bce540f641c",
    "MD-6d5fffc699aa640f4bb8",
}


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_review_wave_is_evidence_only_and_bounded():
    data = json.loads(REVIEW.read_text(encoding="utf-8"))
    items = data["items"]
    assert data["parent_git_sha"] == "56345881f20f4fa03c45442430359ecd9c0aeb7e"
    assert len(items) == data["selection"]["processed_items"] == 8
    assert {item["source_record_key"] for item in items} == EXPECTED_KEYS
    assert data["items_sha256"] == _sha(items) == "488ae59ffa1a873ffbbd94aec37ca3c779f5608f7e2a0314ae8bdb68712b687d"
    assert all(item["review_state"] == "NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED" for item in items)
    assert all(item["source_identity"]["evidence_url"].startswith("https://") for item in items)
    assert all(all(candidate["evidence_url"].startswith("https://") for candidate in item["candidate_identities"]) for item in items)
    forbidden = {"proposed_canonical_hotel_id", "canonical_hotel_id", "allocated_hotel_id", "matched_hotel_id"}
    assert all(forbidden.isdisjoint(item) for item in items)
    assert data["mapping_effect"]["terminal_mappings"] == 0
    assert data["mapping_effect"]["reconcile_required_delta"] == 0
    assert data["mapping_effect"]["effective_reconcile_required"] == 1404
    inv = data["hard_invariants"]
    assert inv == {
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "crm_universe_complete": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def test_next_advances_review_frontier_without_authority_mutation():
    data = json.loads(NEXT.read_text(encoding="utf-8"))
    p = data["provider_identity_frontier"]
    assert (p["provider_evidence_executed"], p["identity_review_completed"], p["identity_review_pending_from_evidence"], p["unprocessed"]) == (47, 28, 19, 0)
    assert p["distinctness_corroborated"] == 27
    assert p["match_existing_applied_preauthority"] == 1
    assert p["latest_identity_review_items_sha256"] == "488ae59ffa1a873ffbbd94aec37ca3c779f5608f7e2a0314ae8bdb68712b687d"
    assert data["mapping_frontier"]["terminal_source_mappings"] == 657
    assert data["mapping_frontier"]["reconcile_required"] == 1404
    assert data["authority_state"]["next_physical_id"] == "H-0691_UNALLOCATED"
    assert data["authority_state"]["crm_universe_complete"] is False
    assert data["authority_state"]["outbound"] == "CLOSED"
    assert data["authority_state"]["send_allowed"] == 0
    assert data["next_route"] == "PIE_050_CAPTURED_19_IDENTITY_REVIEW_THEN_LOWER_49"
    assert data["authority_advance_allowed"] is False
    assert data["canonical_id_allocation_allowed"] is False
    assert data["outbound_allowed"] is False
