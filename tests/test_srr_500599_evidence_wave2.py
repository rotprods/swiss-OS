import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RISK = ROOT / "docs/state/SRET_SIMILARITY_RISK_QUEUE_050_059_33206402141.json"
PROVIDER = ROOT / "docs/state/SRET_PROVIDER_IDENTITY_050_SUB01_33206402141.json"
WAVE1 = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_500599_WAVE1_2026-08-30.json"
WAVE2 = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_500599_WAVE2_2026-08-30.json"
FIVE = "MD-7c70baeb19408c2e971b"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_wave2_exactly_types_distinct_provider_sub01_items_inside_effective_band():
    risk = load(RISK)
    provider = load(PROVIDER)
    wave1 = load(WAVE1)
    wave2 = load(WAVE2)
    raw_keys = {item["source_record_key"] for item in risk["items"]}
    effective = raw_keys - {FIVE}
    expected = [
        item["source_record_key"]
        for item in provider["items"]
        if item["source_record_key"] != FIVE
        and item["review_state"] == "NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED"
    ]
    actual = [item["source_record_key"] for item in wave2["decisions"]]
    wave1_keys = {item["source_record_key"] for item in wave1["decisions"]}
    assert risk["items_count"] == 47
    assert len(effective) == 46
    assert len(provider["items"]) == 10
    assert provider["result_counts"]["NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED"] == 9
    assert provider["result_counts"]["MATCH_EXISTING_REVIEW_CORROBORATED"] == 1
    assert actual == expected
    assert len(actual) == 9
    assert set(actual) <= effective
    assert not (set(actual) & wave1_keys)
    assert FIVE not in actual
    assert canonical_sha(wave2["decisions"]) == wave2["decisions_sha256"]


def test_wave2_is_preauthority_only_and_evidence_backed():
    wave2 = load(WAVE2)
    assert all(item["action"] == "NEW_CANONICAL" for item in wave2["decisions"])
    assert all(item["provider_review_state"] == "NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED" for item in wave2["decisions"])
    assert all(item["evidence_basis"] == "docs/state/SRET_PROVIDER_IDENTITY_050_SUB01_33206402141.json" for item in wave2["decisions"])
    assert all("canonical_hotel_id" not in item for item in wave2["decisions"])
    sem = wave2["decision_semantics"]["NEW_CANONICAL"]
    assert sem["mapping_state"] == "RECONCILE_REQUIRED"
    assert sem["canonical_h_id_reserved"] is False
    assert sem["operational_authority"] is False
    assert wave2["counts"] == {
        "reviewed": 9,
        "new_canonical_preauth": 9,
        "relationship_unresolved": 0,
        "terminal_existing_or_alias": 0,
        "canonical_id_reservations": 0,
        "h_id_allocations": 0,
        "irreversible_external_actions": 0,
    }


def test_wave2_frontier_and_hard_locks_are_conservative():
    wave2 = load(WAVE2)
    assert wave2["band_frontier"] == {
        "source_queue_records": 47,
        "already_terminal_exception_records": 1,
        "effective_unresolved_records": 46,
        "prior_reviewed": 10,
        "reviewed_this_wave": 9,
        "reviewed_cumulative": 19,
        "remaining": 27,
        "terminal_delta_from_wave": 0,
    }
    assert wave2["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 38
    assert wave2["cumulative_preauthority_frontier"]["overall_relationship_granularity_unresolved"] == 2
    safety = wave2["safety"]
    assert safety["authority_advanced"] is False
    assert safety["canonical_id_reservations"] == 0
    assert safety["h_id_allocations"] == 0
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["crm_universe_complete"] is False
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0
    assert safety["irreversible_external_actions"] == 0
    assert wave2["next"] == {
        "route": "BOUND_CURRENT_IDENTITY_EVIDENCE_REVIEW_500_599_WAVE3_WITHOUT_AUTOBIND",
        "band_total": 46,
        "reviewed": 19,
        "remaining": 27,
    }
