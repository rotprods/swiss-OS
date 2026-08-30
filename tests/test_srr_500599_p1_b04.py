import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_500599_P1_B04_2026-08-30.json"
WORK = ROOT / "docs/operations/CRM_IDENTITY_REVIEW_WORKSET_500599_REMAINING36_2026-08-30.json"
NEXT = ROOT / "docs/state/NEXT.json"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_p1_b04_closes_exact_band_fail_closed():
    art = json.loads(ART.read_text(encoding="utf-8"))
    work = json.loads(WORK.read_text(encoding="utf-8"))
    nxt = json.loads(NEXT.read_text(encoding="utf-8"))
    expected = work["batches"][3]["source_record_keys"]
    decisions = art["decisions"]
    keys = [item["source_record_key"] for item in decisions]
    assert art["parent_git_sha"] == "2371679d6c9eafdf334217a253e86fdfda13e37b"
    assert art["claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert art["claim"]["fencing_token"] == 6
    assert art["authority"]["materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert art["batch"]["batch_id"] == "P1-B04"
    assert keys == expected
    assert len(keys) == len(set(keys)) == 6
    assert _sha(decisions) == art["decisions_sha256"]
    assert all(item["action"] == "NEW_CANONICAL" for item in decisions)
    assert all(item["mapping_state"] == "RECONCILE_REQUIRED" for item in decisions)
    assert all(item["canonical_h_id_reserved"] is False for item in decisions)
    assert all(item["h_id_allocated"] is False for item in decisions)
    assert all(len(item["evidence"]) >= 3 for item in decisions)
    assert art["counts"]["terminal_mapping_delta"] == 0
    assert art["band_frontier"]["reviewed_after"] == 46
    assert art["band_frontier"]["remaining_after"] == 0
    assert art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 65
    assert art["mapping_effect"]["terminal_mappings_after"] == 658
    assert art["mapping_effect"]["reconcile_required_after"] == 1403
    safety = art["safety"]
    assert safety["authority_advanced"] is False
    assert safety["canonical_id_reservations"] == 0
    assert safety["h_id_allocations"] == 0
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["crm_universe_complete"] is False
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0
    assert safety["irreversible_external_actions"] == 0
    assert nxt["next_route"] == "RESOLVE_REMAINING_RELATIONSHIP_GRANULARITY_DELTA_OVERLOOK_READ_ONLY"
    assert nxt["review_frontier"]["band500599"]["reviewed_after"] == 46
    assert nxt["review_frontier"]["band500599"]["remaining"] == 0
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound_allowed"] is False


def test_p1_b04_adversarial_confusables_stay_distinct():
    art = json.loads(ART.read_text(encoding="utf-8"))
    by_key = {item["source_record_key"]: item for item in art["decisions"]}
    assert by_key["MD-d71b02bc712af2543eae"]["reason_code"] == "SAME_ADDRESS_SAME_PROVIDER_BUT_DISTINCT_PROPERTY_CODES_PHONES_AND_BRANDS"
    assert by_key["MD-eaa9591c67a4016cf6c4"]["reason_code"] == "CURRENT_OFFICIAL_ADDRESS_BRAND_AND_DOMAIN_DISTINCT_FROM_IBIS_LAUSANNE_CRISSIER"
    assert by_key["MD-fe293753a2a9af0ca839"]["suggested_hotel_ids"] == ["H-0473", "H-0682"]
