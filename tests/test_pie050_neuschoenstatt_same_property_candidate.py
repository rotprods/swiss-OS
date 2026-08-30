import hashlib
import json
from pathlib import Path

ARTIFACT = Path("docs/state/PIE050_NEUSCHOENSTATT_SAME_PROPERTY_CANDIDATE_2026-08-30.json")
QUEUE = Path("docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json")


def test_neuschoenstatt_candidate_is_strong_but_non_authoritative():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))

    assert data["schema_version"] == "PIE050-SAME-PROPERTY-CANDIDATE-1.0"
    assert data["parent_git_sha"] == "8b0be38dc1dcf3aa64b0e617552962977f4b584f"
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert data["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
    assert data["fencing_token"] == 5
    assert data["source_record_key"] == "MD-33d867e983644585e4b2"
    assert data["source_record_key"] in queue["source_record_keys"]
    assert data["canonical_candidate"]["hotel_id"] == "H-0114"
    assert data["canonical_candidate"]["name"] == "Hostel Neu-Schönstatt"
    assert data["review_outcome"] == "STRONG_SAME_PROPERTY_CANDIDATE_REQUIRES_AUTHORITY_REVIEW"
    assert data["similarity"]["role"] == "REVIEW_SPACE_REDUCTION_ONLY"
    assert len(data["current_first_party_evidence"]) >= 4
    assert all(item["url"].startswith("https://neuschoenstatt.ch/") for item in data["current_first_party_evidence"])

    proposal = data["proposed_terminal_mapping"]
    assert proposal["source_record_key"] == data["source_record_key"]
    assert proposal["candidate_hotel_id"] == "H-0114"
    assert proposal["state"] == "PROPOSED_ONLY"
    assert proposal["terminal_mapping_allowed"] is False

    effect = data["effect"]
    assert effect["terminal_source_mappings_added"] == 0
    assert effect["terminal_source_mappings_total"] == 657
    assert effect["reconcile_required_before"] == effect["reconcile_required_after"] == 1404
    assert effect["h_id_allocations"] == 0
    assert effect["canonical_id_reservations"] == 0
    assert effect["authority_advanced"] is False
    assert effect["crm_universe_complete"] is False
    assert effect["outbound"] == "CLOSED"
    assert effect["send_allowed"] == 0


def test_neuschoenstatt_candidate_content_hash_detects_silent_rewrite():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    expected = data.pop("packet_sha256")
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected
