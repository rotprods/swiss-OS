import hashlib
import json
from pathlib import Path

QUEUE = Path("docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json")
PACKET = Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_01_2026-08-30.json")


def test_packet_lineage_scope_and_fail_closed_effects():
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    reviews = data["reviews"]
    keys = [item["source_record_key"] for item in reviews]

    assert data["schema_version"] == "PIE050-LOWER49-REVIEW-PACKET-1.0"
    assert data["parent_git_sha"] == "8fcc1b188060de84a3e57d1878ec00a543e2f240"
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert data["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
    assert data["fencing_token"] == 5
    assert data["reviewed_count"] == len(keys) == len(set(keys)) == 10
    assert data["pending_lower49_after"] == 39
    assert set(keys) <= set(queue["source_record_keys"])
    assert hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest() == data["reviewed_source_record_keys_sha256"]

    for item in reviews:
        assert item["evidence_tier"] == "CURRENT_PUBLIC_DESTINATION_LISTING"
        assert item["review_outcome"] == "CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED"
        assert item["terminal_source_mapping"] == "NONE"
        assert item["new_identity_status"] == "UNALLOCATED_PREAUTH_CANDIDATE"
        assert item["authority_effect"] == "NONE"
        assert item["current_public_evidence_urls"]

    effect = data["effect"]
    assert effect["similarity_collision_reviews_cleared"] == 10
    assert effect["terminal_source_mappings_added"] == 0
    assert effect["terminal_source_mappings_total"] == 657
    assert effect["reconcile_required_before"] == effect["reconcile_required_after"] == 1404
    assert effect["h_id_allocations"] == 0
    assert effect["canonical_id_reservations"] == 0
    assert effect["authority_advanced"] is False
    assert effect["crm_universe_complete"] is False
    assert effect["outbound"] == "CLOSED"
    assert effect["send_allowed"] == 0


def test_packet_content_hash_detects_silent_rewrite():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    expected = data.pop("packet_sha256")
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected
