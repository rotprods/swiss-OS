import hashlib
import json
from pathlib import Path

EVIDENCE = Path("docs/state/SRET_PROVIDER_IDENTITY_050_SUB03_33206402141.json")
WORK = Path("docs/state/PROVIDER_IDENTITY_WORK_0003_33206402141.json")


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_sub03_evidence_does_not_overclaim_identity_or_mapping():
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert data["provider_enrichment"]["results_count"] == 10
    assert data["provider_enrichment"]["state"] == "EXECUTED_VALIDATED_REVIEW_ONLY"
    assert data["review"]["review_state"] == "EVIDENCE_CAPTURED_REVIEW_REQUIRED"
    assert data["review"]["terminal_decision_allowed"] is False
    assert data["mapping_effect"]["terminal_mappings"] == 0
    assert data["mapping_effect"]["reconcile_required_delta"] == 0
    assert data["mapping_effect"]["effective_reconcile_required"] == 1404
    assert data["frontier"] == {"provider_evidence_executed":30,"identity_review_completed":20,"identity_review_pending_from_evidence":10,"unprocessed_in_050_059":17}
    inv = data["hard_invariants"]
    assert inv["authority_advanced"] is False
    assert inv["h_id_allocations"] == 0
    assert inv["canonical_id_reservations"] == 0
    assert inv["outbound"] == "CLOSED"
    assert inv["send_allowed"] == 0


def test_final17_packet_is_exact_targetless_and_safe():
    data = json.loads(WORK.read_text(encoding="utf-8"))
    items = data["items"]
    assert data["items_count"] == len(items) == 17
    assert data["items_sha256"] == _sha(items) == "a0799fd578ed008bbef2896b2c3d4fbfc4269ef82afafbc5cc29a80d537073b6"
    assert len({x["source_record_key"] for x in items}) == 17
    assert all(x["detail_url"].startswith("https://www.hotelleriesuisse.ch/") for x in items)
    assert all(not any(k in x for k in ("canonical_hotel_id", "matched_hotel_id", "allocated_hotel_id")) for x in items)
    assert data["identity_decision_allowed"] is False
    assert data["terminal_mapping_allowed"] is False
    assert data["canonical_id_reservation_allowed"] is False
    assert data["authority_advanced"] is False
    assert data["h_id_allocations"] == 0
    assert data["crm_universe_complete"] is False
    assert data["outbound"] == "CLOSED"
    assert data["send_allowed"] == 0
