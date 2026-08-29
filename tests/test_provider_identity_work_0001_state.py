import hashlib
import json
from pathlib import Path

PACKET = Path("docs/state/PROVIDER_IDENTITY_WORK_0001_33206402141.json")


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_provider_identity_work_is_bounded_targetless_and_safe():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    items = data["items"]
    assert data["items_count"] == len(items) == 10
    assert data["items_sha256"] == _sha(items) == "642abcfbdbb077840d1466be6624b799e4d16780a640484919fb1f2c03f62276"
    assert len({x["source_record_key"] for x in items}) == 10
    assert all(x["detail_url"].startswith("https://www.hotelleriesuisse.ch/") for x in items)
    assert all(not any(k in x for k in ("canonical_hotel_id", "matched_hotel_id", "allocated_hotel_id")) for x in items)
    assert data["review_only"] is True
    assert data["identity_decision_allowed"] is False
    assert data["terminal_mapping_allowed"] is False
    assert data["canonical_id_reservation_allowed"] is False
    assert data["authority_advanced"] is False
    assert data["h_id_allocations"] == 0
    assert data["crm_universe_complete"] is False
    assert data["outbound"] == "CLOSED"
    assert data["send_allowed"] == 0
