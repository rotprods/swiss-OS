import hashlib
import json
from pathlib import Path

QUEUE=Path("docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json")
P1=Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_01_2026-08-30.json")
P2=Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_02_2026-08-30.json")
P3=Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_03_2026-08-30.json")
P4=Path("docs/state/PIE050_LOWER49_REVIEW_PACKET_04_2026-08-30.json")

def load(p): return json.loads(p.read_text(encoding="utf-8"))

def test_packet_04_lineage_disjointness_and_fail_closed():
    q,p1,p2,p3,p4=map(load,[QUEUE,P1,P2,P3,P4])
    prior={r["source_record_key"] for p in [p1,p2,p3] for r in p["reviews"]}
    keys=[r["source_record_key"] for r in p4["reviews"]]
    assert p4["parent_git_sha"]=="8571a0166c0e4f6a0325a0c4ebf8151844e7ea36"
    assert p4["authority_epoch"]=="HS_ENTITY_EPOCH_2026-08-25_E4"
    assert p4["authority_materialized_sha256"]=="70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert p4["claim_id"]=="CLAIM-CRM-PIE050-LOWER49-005" and p4["fencing_token"]==5
    assert len(keys)==len(set(keys))==p4["reviewed_count"]==10
    assert not (set(keys)&prior)
    assert set(keys)<=set(q["source_record_keys"])
    assert len(prior|set(keys))==40
    assert p4["reviewed_cumulative"]==40 and p4["pending_lower49_after"]==9
    assert hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()==p4["reviewed_source_record_keys_sha256"]
    for r in p4["reviews"]:
        assert r["review_outcome"]=="CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED"
        assert r["terminal_source_mapping"]=="NONE" and r["authority_effect"]=="NONE"
        assert r["new_identity_status"]=="UNALLOCATED_PREAUTH_CANDIDATE"
        assert 350000<=r["max_token_jaccard_ppm"]<500000 and r["current_public_evidence_urls"]
    e=p4["effect"]
    assert e["terminal_source_mappings_added"]==0 and e["terminal_source_mappings_total"]==657
    assert e["reconcile_required_before"]==e["reconcile_required_after"]==1404
    assert e["h_id_allocations"]==e["canonical_id_reservations"]==0
    assert e["authority_advanced"] is False and e["crm_universe_complete"] is False
    assert e["outbound"]=="CLOSED" and e["send_allowed"]==0

def test_packet_04_hash():
    d=load(P4); expected=d.pop("packet_sha256")
    assert hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()==expected
