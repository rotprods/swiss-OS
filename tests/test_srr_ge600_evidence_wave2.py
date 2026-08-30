import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAVE1 = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_GE600_WAVE1_2026-08-30.json"
WAVE2 = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_GE600_WAVE2_2026-08-30.json"
ANTI = ROOT / "docs/state/SOURCE_RESOLUTION_REVIEW_UNRESOLVED_1403_33206402141.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha(payload):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_wave2_is_exact_complement_of_wave1_and_closes_ge600_queue():
    w1 = load(WAVE1)
    w2 = load(WAVE2)
    anti = load(ANTI)
    priority = {item["source_record_key"] for item in anti["review_priority"]["priority_ge600_items"]}
    keys1 = {item["source_record_key"] for item in w1["decisions"]}
    keys2 = {item["source_record_key"] for item in w2["decisions"]}
    assert len(keys1) == len(keys2) == 10
    assert keys1.isdisjoint(keys2)
    assert keys1 | keys2 == priority
    assert w2["next"]["ge600_priority_total"] == 20
    assert w2["next"]["reviewed"] == 20
    assert w2["next"]["remaining"] == 0
    assert w2["next"]["route"] == "BOUND_CURRENT_IDENTITY_EVIDENCE_REVIEW_500_599_WAVE1_WITHOUT_AUTOBIND"
    assert canonical_sha(w2["decisions"]) == w2["decisions_sha256"]


def test_wave2_all_new_canonical_decisions_remain_preauthority_without_ids():
    w2 = load(WAVE2)
    assert len(w2["decisions"]) == 10
    assert all(item["action"] == "NEW_CANONICAL" for item in w2["decisions"])
    assert w2["counts"] == {
        "canonical_id_reservations": 0,
        "h_id_allocations": 0,
        "irreversible_external_actions": 0,
        "new_canonical_preauth": 10,
        "relationship_unresolved": 0,
        "reviewed": 10,
        "terminal_existing_or_alias": 0,
    }
    sem = w2["decision_semantics"]["NEW_CANONICAL"]
    assert sem["mapping_state"] == "RECONCILE_REQUIRED"
    assert sem["authority_action"] == "ALLOCATE_NEW_CANONICAL_ON_AUTHORITY_COMMIT"
    assert sem["canonical_h_id_reserved"] is False
    assert sem["operational_authority"] is False
    for item in w2["decisions"]:
        assert "canonical_hotel_id" not in item
        assert item["evidence"]
        assert item["reason_code"].startswith("CURRENT_")


def test_cumulative_ge600_is_19_new_one_unresolved_zero_terminal_and_hard_locks_hold():
    w1 = load(WAVE1)
    w2 = load(WAVE2)
    actions = [item["action"] for item in w1["decisions"] + w2["decisions"]]
    assert actions.count("NEW_CANONICAL") == 19
    assert actions.count("UNRESOLVED") == 1
    assert not any(action in {"MATCH_EXISTING", "ALIAS_EXISTING"} for action in actions)
    assert w2["cumulative_ge600"] == {
        "new_canonical_preauth": 19,
        "priority_total": 20,
        "relationship_unresolved": 1,
        "reviewed": 20,
        "terminal_existing_or_alias": 0,
    }
    safety = w2["safety"]
    assert safety["authority_advanced"] is False
    assert safety["canonical_id_reservations"] == 0
    assert safety["h_id_allocations"] == 0
    assert safety["irreversible_external_actions"] == 0
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["crm_universe_complete"] is False
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0
