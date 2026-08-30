import json
from pathlib import Path

MANIFEST = Path("docs/state/CRM_MASS_ANTI_JOIN_1403_MANIFEST_33206402141.json")
STAGE = Path("docs/state/CRM_UNRESOLVED_STAGE_0001_33206402141.json")

def test_mass_anti_join_1403_manifest_and_stage():
    m=json.loads(MANIFEST.read_text(encoding="utf-8"))
    s=json.loads(STAGE.read_text(encoding="utf-8"))
    a=m["anti_join"]
    assert m["candidate"]["records"] == 1438
    assert m["terminal_exceptions"]["count"] == 35
    assert a["unresolved_records"] == 1403
    assert a["unresolved_source_record_keys_sha256"] == "910cfd92974025a836430612387d380be0f15d173d41f20fda6fea2bcca48581"
    assert a["matches_full_658_unresolved_digest"] is True
    assert len(a["batches"]) == 22
    assert sum(b["records"] for b in a["batches"]) == 1403
    assert a["batches"][0]["records"] == 64
    assert a["batches"][-1]["records"] == 59
    assert s["records"] == 64
    assert s["source_record_keys_sha256"] == a["batches"][0]["source_record_keys_sha256"]
    assert s["source_record_keys"] == sorted(s["source_record_keys"])
    assert s["work_contract"]["allowed_terminal_decision"] is False
    assert m["safety"]["terminal_mapping_allowed"] is False
    assert m["safety"]["authority_advanced"] is False
    assert m["safety"]["canonical_id_reservations"] == 0
    assert m["safety"]["outbound"] == "CLOSED"
    assert m["safety"]["send_allowed"] == 0
