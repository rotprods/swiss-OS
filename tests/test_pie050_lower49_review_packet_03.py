import hashlib
import json
from pathlib import Path

QUEUE = Path("docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json")
PACKETS = [
    Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_01_2026-08-30.json"),
    Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_02_2026-08-30.json"),
    Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_03_2026-08-30.json"),
]

def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def test_packet_03_exact_scope_disjointness_and_fail_closed():
    queue = _load(QUEUE)
    p1, p2, p3 = map(_load, PACKETS)
    k1 = {r["source_record_key"] for r in p1["reviews"]}
    k2 = {r["source_record_key"] for r in p2["reviews"]}
    k3 = [r["source_record_key"] for r in p3["reviews"]]
    assert p3["parent_git_sha"] == "cffdb3259acd703e4c6250f42e49597a37d9a761"
    assert p3["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert p3["authority_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert p3["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
    assert p3["fencing_token"] == 5
    assert p3["reviewed_count"] == len(k3) == len(set(k3)) == 10
    assert p3["reviewed_cumulative"] == 30
    assert p3["pending_lower49_after"] == 19
    assert set(k3) <= set(queue["source_record_keys"])
    assert not (set(k3) & k1)
    assert not (set(k3) & k2)
    assert len(k1 | k2 | set(k3)) == 30
    assert hashlib.sha256("\n".join(sorted(k3)).encode()).hexdigest() == p3["reviewed_source_record_keys_sha256"]
    for item in p3["reviews"]:
        assert item["review_outcome"] == "CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED"
        assert item["terminal_source_mapping"] == "NONE"
        assert item["new_identity_status"] == "UNALLOCATED_PREAUTH_CANDIDATE"
        assert item["authority_effect"] == "NONE"
        assert item["current_public_evidence_urls"]
        assert 350000 <= item["max_token_jaccard_ppm"] < 500000
    e=p3["effect"]
    assert e["terminal_source_mappings_added"] == 0
    assert e["terminal_source_mappings_total"] == 657
    assert e["reconcile_required_before"] == e["reconcile_required_after"] == 1404
    assert e["h_id_allocations"] == e["canonical_id_reservations"] == 0
    assert e["authority_advanced"] is False
    assert e["crm_universe_complete"] is False
    assert e["outbound"] == "CLOSED" and e["send_allowed"] == 0

def test_packet_03_hash_detects_silent_rewrite():
    data = _load(PACKETS[-1])
    expected=data.pop("packet_sha256")
    canonical=json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",",":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected
