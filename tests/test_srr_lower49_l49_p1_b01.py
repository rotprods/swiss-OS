import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_LOWER49_L49_P1_B01_2026-08-30.json"
WORKSET = ROOT / "docs/operations/CRM_IDENTITY_WORKSET_LOWER49_ORDINARY_47_2026-08-30.json"
PACKET = ROOT / "docs/state/PIE050_LOWER49_REVIEW_PACKET_01_2026-08-30.json"
NEXT = ROOT / "docs/state/NEXT.json"


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_l49_p1_b01_exact_current_identity_decisions_fail_closed():
    art = json.loads(ART.read_text(encoding="utf-8"))
    workset = json.loads(WORKSET.read_text(encoding="utf-8"))
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    nxt = json.loads(NEXT.read_text(encoding="utf-8"))
    decisions = art["decisions"]
    expected_keys = [row["source_record_key"] for row in packet["reviews"]]
    assert art["parent_git_sha"] == "aa7b9964acefc5f86548cf618c3d91e3c68edaf7"
    assert art["batch"]["batch_id"] == "L49-P1-B01"
    assert art["batch"]["workset_sha256"] == workset["workset_sha256"] == "8817941127ede8f9329d81b4831b1fd6643e9ab4c19438c3fa612b78e1169050"
    assert [d["source_record_key"] for d in decisions] == expected_keys
    assert len(decisions) == len(expected_keys) == 10
    assert len(set(expected_keys)) == 10
    assert _sha(decisions) == art["decisions_sha256"]
    assert art["claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert art["claim"]["fencing_token"] == 6
    assert art["batch"]["historical_evidence_fencing_token"] == 5
    assert art["batch"]["historical_evidence_use"] == "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY"
    assert all(d["action"] == "NEW_CANONICAL" for d in decisions)
    assert all(d["mapping_state"] == "RECONCILE_REQUIRED" for d in decisions)
    assert all(d["canonical_h_id_reserved"] is False and d["h_id_allocated"] is False for d in decisions)
    assert all(d["operational_authority"] is False for d in decisions)
    assert all(len(d["evidence"]) >= 4 for d in decisions)
    for d in decisions:
        hist = [e for e in d["evidence"] if e["type"] == "HISTORICAL_REVIEW_EVIDENCE"]
        assert len(hist) == 1
        assert hist[0]["historical_fencing_token"] == 5
        assert hist[0]["use"] == "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY"
        assert any(e["type"] in {"CURRENT_FIRST_PARTY_SOURCE", "CURRENT_QUALIFIED_PUBLIC_SOURCE"} for e in d["evidence"])
        assert any(e["type"] == "CANONICAL_COMPARATOR_READBACK" for e in d["evidence"])
    assert art["lower49_frontier"] == {"effective_ordinary_records": 47, "remaining_after": 37, "typed_srr_after": 10, "typed_srr_before": 0}
    assert art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 77
    assert art["mapping_effect"]["terminal_mappings_after"] == 658
    assert art["mapping_effect"]["reconcile_required_after"] == 1403
    assert art["safety"]["h_0691"] == "UNALLOCATED"
    assert art["safety"]["outbound"] == "CLOSED"
    assert art["safety"]["send_allowed"] == 0
    assert nxt["next_route"] == "EXECUTE_LOWER49_L49_P1_B02_CURRENT_IDENTITY_EVIDENCE"
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound_allowed"] is False


def test_l49_p1_b01_adversarial_confusables_are_independently_distinct():
    art = json.loads(ART.read_text(encoding="utf-8"))
    by_key = {d["source_record_key"]: d for d in art["decisions"]}
    holiday = by_key["MD-0cc595328fe9e3294e79"]
    assert holiday["reason_code"] == "CURRENT_IHG_ADDRESS_AND_BRAND_DISTINCT_FROM_RADISSON_ZURICH_AIRPORT"
    assert holiday["suggested_hotel_ids"] == ["H-0222"]
    ibis = by_key["MD-2f5b1d55e1010fda2a92"]
    codes = {e.get("provider_property_code") for e in ibis["evidence"] if e.get("provider_property_code")}
    assert codes == {"9577", "3133"}
    radisson = by_key["MD-111c2041bb11793c5fb0"]
    assert radisson["suggested_hotel_ids"] == ["H-0050", "H-0081", "H-0467"]
    for key in ["MD-29672bcf8c25067c096c", "MD-33afe5e373cb1739a4d8", "MD-3d8d74f2ccdf0a01cbf6"]:
        assert by_key[key]["suggested_hotel_ids"] == ["H-0368"]
        source_addresses = {e.get("address") for e in by_key[key]["evidence"] if e["type"] in {"CURRENT_FIRST_PARTY_SOURCE", "CURRENT_QUALIFIED_PUBLIC_SOURCE"}}
        comparator_addresses = {e.get("address") for e in by_key[key]["evidence"] if "COMPARATOR" in e["type"] and e.get("address")}
        assert source_addresses and comparator_addresses and source_addresses.isdisjoint(comparator_addresses)
