import hashlib
import json
from pathlib import Path

PACKET = Path("docs/state/PROVIDER_IDENTITY_WORK_0002_33206402141.json")


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_provider_identity_work_sub03_is_bounded_targetless_and_safe():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    items = data["items"]
    assert data["batch_id"].endswith("PIE:050:SUB:0003")
    assert data["parent_git_sha"] == "678415e4a4594cdfc75ab001d35e304d4189985c"
    assert data["source_queue_sha256"] == "eed5f949c55da71b7a69d3dd481778992f316bfdd35e4655f85070dc46a14429"
    assert data["items_count"] == len(items) == 10
    assert data["items_sha256"] == _sha(items) == "07b12092f1e621f55a9e53df20b9d79465adbb989e1357307247af3714db3657"
    assert len({x["source_record_key"] for x in items}) == 10
    assert all(x["detail_url"].startswith("https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/mitgliederverzeichnis/") for x in items)
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
