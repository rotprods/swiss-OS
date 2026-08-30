import hashlib
import json
from pathlib import Path

ARTIFACT = Path("docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json")


def test_lower49_materialized_queue_is_exact_and_fail_closed():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    keys = data["source_record_keys"]
    assert data["schema_version"] == "SRET-PROVIDER-IDENTITY-LOWER-QUEUE-1.0"
    assert data["snapshot_id"] == "HS-MEMBER-DE-33206402141"
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["source_records"] == 2061
    assert data["candidate_records"] == 1438
    assert data["terminal_source_mappings"] == 657
    assert data["reconcile_required"] == 1404
    assert data["items_count"] == len(keys) == len(set(keys)) == 49
    assert keys == sorted(keys)
    assert hashlib.sha256("\n".join(keys).encode()).hexdigest() == data["source_record_keys_sha256"]
    assert data["derivation"] == {
        "350_499": 49,
        "500_599": 46,
        "ge600": 20,
        "historical_500_599": 47,
        "post_terminal_similarity_total": 115,
        "terminalized_historical_medium_key": "MD-7c70baeb19408c2e971b",
        "terminalized_target": "H-0452",
    }
    assert data["review_state"] == "PENDING_PROVIDER_IDENTITY_REVIEW"
    assert data["similarity_authority"] == "REVIEW_SPACE_REDUCTION_ONLY"
    assert data["terminal_mapping_allowed"] is False
    assert data["canonical_id_reservation_allowed"] is False
    assert data["authority_advanced"] is False
    assert data["h_id_allocations"] == 0
    assert data["crm_universe_complete"] is False
    assert data["outbound"] == "CLOSED"
    assert data["send_allowed"] == 0


def test_historical_medium_terminalized_key_is_not_in_lower49():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert "MD-7c70baeb19408c2e971b" not in data["source_record_keys"]
