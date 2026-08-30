import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAVE = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_GE600_WAVE1_2026-08-30.json"
ANTI = ROOT / "docs/state/SOURCE_RESOLUTION_REVIEW_UNRESOLVED_1403_33206402141.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha(payload):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_wave1_is_bounded_subset_of_ge600_priority_and_digest_exact():
    wave = load(WAVE)
    anti = load(ANTI)
    assert wave["schema_version"] == "SRR-CURRENT-IDENTITY-EVIDENCE-WAVE-1.0"
    assert wave["parent_git_sha"] == "30a1e975b72f1db30682ba93bf1b2827cda5892a"
    decisions = wave["decisions"]
    assert len(decisions) == 10
    assert canonical_sha(decisions) == wave["decisions_sha256"]
    priority = {item["source_record_key"] for item in anti["review_priority"]["priority_ge600_items"]}
    keys = [item["source_record_key"] for item in decisions]
    assert len(set(keys)) == 10
    assert set(keys) <= priority
    assert wave["next"]["ge600_priority_total"] == 20
    assert wave["next"]["reviewed"] == 10
    assert wave["next"]["remaining"] == 10


def test_new_canonical_decisions_are_preauthority_without_id_reservation():
    wave = load(WAVE)
    actions = [item["action"] for item in wave["decisions"]]
    assert actions.count("NEW_CANONICAL") == 9
    assert actions.count("UNRESOLVED") == 1
    semantics = wave["decision_semantics"]["NEW_CANONICAL"]
    assert semantics["mapping_state"] == "RECONCILE_REQUIRED"
    assert semantics["authority_action"] == "ALLOCATE_NEW_CANONICAL_ON_AUTHORITY_COMMIT"
    assert semantics["canonical_h_id_reserved"] is False
    assert semantics["operational_authority"] is False
    for item in wave["decisions"]:
        if item["action"] == "NEW_CANONICAL":
            assert "canonical_hotel_id" not in item
            assert item["evidence"]
            assert item["reason_code"].startswith("CURRENT_")


def test_overlook_relationship_stays_unresolved_and_hard_locks_hold():
    wave = load(WAVE)
    unresolved = [item for item in wave["decisions"] if item["action"] == "UNRESOLVED"]
    assert len(unresolved) == 1
    item = unresolved[0]
    assert item["source_record_key"] == "MD-6d39a6c4d43987703b3c"
    assert item["relationship"] == "COMPONENT_OF_OR_OPERATED_WITHIN:H-0012"
    assert item["reason_code"] == "CURRENT_FIRST_PARTY_COMPONENT_RELATIONSHIP_ENTITY_GRANULARITY_UNRESOLVED"
    assert wave["counts"] == {
        "canonical_id_reservations": 0,
        "h_id_allocations": 0,
        "irreversible_external_actions": 0,
        "new_canonical_preauth": 9,
        "relationship_unresolved": 1,
        "reviewed": 10,
        "terminal_existing_or_alias": 0,
    }
    safety = wave["safety"]
    assert safety["authority_advanced"] is False
    assert safety["canonical_id_reservations"] == 0
    assert safety["h_id_allocations"] == 0
    assert safety["irreversible_external_actions"] == 0
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["crm_universe_complete"] is False
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0
