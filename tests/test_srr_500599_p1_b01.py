import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_500599_P1_B01_2026-08-30.json"
WORK = ROOT / "docs/operations/CRM_IDENTITY_REVIEW_WORKSET_500599_REMAINING36_2026-08-30.json"
NEXT = ROOT / "docs/state/NEXT.json"


def test_p1_b01_is_exact_evidence_bound_and_fail_closed():
    art = json.loads(ART.read_text(encoding="utf-8"))
    work = json.loads(WORK.read_text(encoding="utf-8"))
    nxt = json.loads(NEXT.read_text(encoding="utf-8"))

    expected = work["batches"][0]["source_record_keys"]
    decisions = art["decisions"]
    keys = [item["source_record_key"] for item in decisions]

    assert art["parent_git_sha"] == "3b2945d2f2df855b048d7d80ddd8e843fecb78e8"
    assert art["claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert art["claim"]["fencing_token"] == 6
    assert art["authority"]["materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert art["batch"]["batch_id"] == "P1-B01"
    assert keys == expected
    assert len(keys) == len(set(keys)) == 10
    assert all(item["action"] == "NEW_CANONICAL" for item in decisions)
    assert all(item["mapping_state"] == "RECONCILE_REQUIRED" for item in decisions)
    assert all(item["canonical_h_id_reserved"] is False for item in decisions)
    assert all(item["h_id_allocated"] is False for item in decisions)
    assert all(len(item["evidence"]) >= 2 for item in decisions)

    assert art["counts"]["terminal_mapping_delta"] == 0
    assert art["band_frontier"]["reviewed_after"] == 20
    assert art["band_frontier"]["remaining_after"] == 26
    assert art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 39
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

    assert nxt["next_route"] == "EXECUTE_500599_P1_B02_CURRENT_IDENTITY_REVIEW_WITHOUT_AUTOBIND"
    assert nxt["review_frontier"]["band500599"]["reviewed_after"] == 20
    assert nxt["review_frontier"]["band500599"]["remaining"] == 26
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound_allowed"] is False
