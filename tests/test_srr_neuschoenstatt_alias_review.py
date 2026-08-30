import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/state/SRR_NEUSCHOENSTATT_ALIAS_EXISTING_REVIEW_2026-08-30.json"
CANDIDATE = ROOT / "docs/state/PIE050_NEUSCHOENSTATT_SAME_PROPERTY_CANDIDATE_2026-08-30.json"
LOWER49 = ROOT / "docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json"
REBUILD = ROOT / "docs/state/FULL_SOURCE_MAPPING_REBUILD_657_ATTESTATION_33206402141.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_review_is_evidence_backed_alias_candidate_and_not_authority():
    p = load(PACKET)
    c = load(CANDIDATE)
    q = load(LOWER49)
    r = load(REBUILD)
    assert p["parent_git_sha"] == "11a528dd1584b3606fed83356c006065e9785778"
    assert p["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert p["authority_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert p["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005" and p["fencing_token"] == 5
    key = p["source_record_key"]
    assert key == c["source_record_key"] == "MD-33d867e983644585e4b2"
    assert key in q["source_record_keys"]
    assert c["review_outcome"] == "STRONG_SAME_PROPERTY_CANDIDATE_REQUIRES_AUTHORITY_REVIEW"
    assert p["canonical_target"]["hotel_id"] == "H-0114"
    assert p["resolution_review"]["action"] == "ALIAS_EXISTING"
    assert p["resolution_review"]["terminal_mapping_candidate"] is True
    assert p["resolution_review"]["terminal_mapping_allowed_in_this_wave"] is False
    assert r["recovery_recipe"]["exceptional_mappings"]["MD-b1eb8f0ce9f3a4733c71"] == "H-0114"
    assert "H-0114" not in r["ragr"]["gap_hotel_ids"]
    projected = p["projected_effect_if_later_authority_commit_succeeds"]
    assert projected == {
        "terminal_source_mappings": 658,
        "unique_canonical_targets": 656,
        "reconcile_required": 1403,
        "reverse_authority_source_gaps": 34,
        "new_h_ids": 0,
    }
    e = p["effect_this_wave"]
    assert e["terminal_source_mappings"] == 657 and e["reconcile_required"] == 1404
    assert e["h_id_allocations"] == e["canonical_id_reservations"] == 0
    assert e["authority_advanced"] is False and e["crm_universe_complete"] is False
    assert e["outbound"] == "CLOSED" and e["send_allowed"] == 0
    assert e["irreversible_external_actions"] == 0


def test_review_packet_hash_is_deterministic():
    p = load(PACKET)
    expected = p.pop("packet_sha256")
    canonical = json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected
