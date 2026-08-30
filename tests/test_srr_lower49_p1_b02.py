import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_LOWER49_P1_B02_2026-08-30.json"
PACKET = ROOT / "docs/state/PIE050_LOWER49_REVIEW_PACKET_02_2026-08-30.json"
WORKSET = ROOT / "docs/operations/CRM_IDENTITY_WORKSET_LOWER49_ORDINARY_47_2026-08-30.json"
NEXT = ROOT / "docs/state/NEXT.json"


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_l49_p1_b02_exact_current_identity_decisions_fail_closed():
    art = json.loads(ART.read_text(encoding="utf-8"))
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    workset = json.loads(WORKSET.read_text(encoding="utf-8"))
    nxt = json.loads(NEXT.read_text(encoding="utf-8"))
    decisions = art["decisions"]
    expected_keys = [row["source_record_key"] for row in packet["reviews"]]

    assert art["parent_git_sha"] == "95a4d4acb317e996bebeeb27d5933432c9ad9599"
    assert art["batch"]["batch_id"] == "L49-P1-B02"
    assert art["batch"]["workset_sha256"] == workset["workset_sha256"] == "8817941127ede8f9329d81b4831b1fd6643e9ab4c19438c3fa612b78e1169050"
    assert art["batch"]["source_record_keys"] == expected_keys
    assert [d["source_record_key"] for d in decisions] == expected_keys
    assert len(decisions) == len(set(expected_keys)) == 10
    assert _sha(decisions) == art["decisions_sha256"] == "63892f2874a568751056b6eebe65ca6ec52c2d56c808daf6df1dbeb2894b6ccf"
    assert art["claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert art["claim"]["fencing_token"] == 6
    assert all(d["action"] == "NEW_CANONICAL" for d in decisions)
    assert all(d["mapping_state"] == "RECONCILE_REQUIRED" for d in decisions)
    assert all(d["canonical_h_id_reserved"] is False and d["h_id_allocated"] is False for d in decisions)
    assert all(d["operational_authority"] is False for d in decisions)
    for d in decisions:
        historical = [e for e in d["evidence"] if e["type"] == "HISTORICAL_CURRENT_DISTINCTNESS_EVIDENCE_ONLY"]
        assert len(historical) == 1
        assert historical[0]["authority"] == "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY"
        assert any(e["type"] == "CURRENT_SOURCE_WEB" for e in d["evidence"])
        assert any(e["type"] == "CANONICAL_COMPARATOR_READBACK" for e in d["evidence"])

    assert art["lower49_frontier"] == {"effective_ordinary_records": 47, "remaining_after": 27, "typed_srr_after": 20, "typed_srr_before": 10}
    assert art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 87
    assert art["mapping_effect"]["terminal_mappings_after"] == 658
    assert art["mapping_effect"]["reconcile_required_after"] == 1403
    assert art["safety"]["h_0691"] == "UNALLOCATED"
    assert art["safety"]["outbound"] == "CLOSED" and art["safety"]["send_allowed"] == 0
    assert art["safety"]["authority_advanced"] is False
    assert art["safety"]["canonical_id_reservations"] == 0
    assert art["safety"]["h_id_allocations"] == 0
    assert art["safety"]["irreversible_external_actions"] == 0
    assert nxt["next_route"] == "EXECUTE_LOWER49_L49_P1_B03_CURRENT_IDENTITY_EVIDENCE"
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound_allowed"] is False


def test_l49_p1_b02_adversarial_collisions_are_independently_distinct():
    art = json.loads(ART.read_text(encoding="utf-8"))
    by_key = {d["source_record_key"]: d for d in art["decisions"]}

    # Same-provider / adjacent-complex cases require independent provider IDs, not name similarity.
    expected_codes = {
        "MD-5b615884374622a092d0": {"9665", "8215"},
        "MD-62c2d857f1a02b87e6a7": {"5049", "5009"},
        "MD-68dfe05e742b42831a4e": {"2154", "3133"},
        "MD-6caa40a9d84392fffeac": {"6781", "6775"},
    }
    for key, codes in expected_codes.items():
        observed = {e.get("provider_property_code") for e in by_key[key]["evidence"] if e.get("provider_property_code")}
        assert observed == codes

    assert by_key["MD-52ceb75baa65fb5de17c"]["reason_code"] == "ADJACENT_UTOQUAI_PROPERTIES_HAVE_DISTINCT_CURRENT_FIRST_PARTY_IDENTITIES"
    assert by_key["MD-68a026173cd82d358ecd"]["suggested_hotel_ids"] == ["H-0021", "H-0023", "H-0025"]
    assert by_key["MD-68a026173cd82d358ecd"]["reason_code"] == "CURRENT_FIRST_PARTY_ADDRESS_DISTINCT_FROM_ALL_THREE_ZERMATT_COMPARATORS"
