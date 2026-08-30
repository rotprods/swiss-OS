import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/state/SRR_DELTA_RESORT_NEW_CANONICAL_REVIEW_2026-08-30.json"
REL = ROOT / "docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json"
LOWER49 = ROOT / "docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_delta_review_preserves_distinct_product_and_never_reserves_id():
    p = load(PACKET)
    rel = load(REL)
    q = load(LOWER49)
    assert p["parent_git_sha"] == "41e4721d7b47779aac32f9998da7ac27b25de6d5"
    assert p["source_record_key"] == rel["source_record_key"] == "MD-7976c173678dc89c9cf0"
    assert p["source_record_key"] in q["source_record_keys"]
    assert rel["review_outcome"] == "COLOCATED_SUBPROPERTY_RELATION_REQUIRES_AUTHORITY_REVIEW"
    assert rel["relationship_hypothesis"]["relation"] == "OPERATED_AS_SUBPROPERTY_OF"
    assert p["resolution_review"]["action"] == "NEW_CANONICAL"
    assert p["resolution_review"]["new_canonical_candidate"] is True
    assert p["resolution_review"]["h_id_allocation_allowed_in_this_wave"] is False
    assert p["resolution_review"]["terminal_mapping_allowed_in_this_wave"] is False
    assert p["relationship_proposal"]["parent_hotel_id"] == "H-0220"
    assert p["relationship_proposal"]["authority"] == "PROPOSED_ONLY"
    e = p["effect_this_wave"]
    assert e["active_canonical"] == 690
    assert e["terminal_source_mappings"] == 657 and e["reconcile_required"] == 1404
    assert e["h_id_allocations"] == e["canonical_id_reservations"] == 0
    assert e["authority_advanced"] is False and e["crm_universe_complete"] is False
    assert e["outbound"] == "CLOSED" and e["send_allowed"] == 0
    assert e["irreversible_external_actions"] == 0


def test_delta_projected_authority_effect_is_conditional_only():
    p = load(PACKET)["projected_effect_if_later_authority_commit_succeeds"]
    assert p == {
        "active_canonical": 691,
        "terminal_source_mappings": 658,
        "unique_canonical_targets": 657,
        "reconcile_required": 1403,
        "next_h_id_after_commit": "H-0692_UNALLOCATED",
        "h_id_allocations_in_authority_transaction": 1,
    }


def test_lower49_review_frontier_is_exhaustively_classified_without_terminalization():
    f = load(PACKET)["lower49_resolution_frontier_after_review"]
    assert f["ordinary_distinctness_reviewed"] == 47
    assert f["alias_existing_candidate"] == 1
    assert f["new_canonical_candidate"] == 1
    assert f["relationship_sensitive_unclassified"] == 0
    assert f["total"] == 49


def test_packet_hash_is_deterministic():
    p = load(PACKET)
    expected = p.pop("packet_sha256")
    canonical = json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected
