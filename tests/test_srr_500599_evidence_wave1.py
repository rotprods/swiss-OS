import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RISK = ROOT / "docs/state/SRET_SIMILARITY_RISK_QUEUE_050_059_33206402141.json"
PROVIDER = ROOT / "docs/state/SRET_PROVIDER_IDENTITY_050_SUB02_33206402141.json"
WAVE = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_500599_WAVE1_2026-08-30.json"
FIVE = "MD-7c70baeb19408c2e971b"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_wave1_exactly_types_provider_sub02_inside_effective_46_band():
    risk = load(RISK)
    provider = load(PROVIDER)
    wave = load(WAVE)
    raw_keys = {item["source_record_key"] for item in risk["items"]}
    effective = raw_keys - {FIVE}
    decision_keys = [item["source_record_key"] for item in wave["decisions"]]
    provider_keys = provider["selection"]["processed_source_keys"]
    assert risk["items_count"] == 47
    assert FIVE in raw_keys
    assert len(effective) == 46
    assert decision_keys == provider_keys
    assert len(decision_keys) == 10
    assert set(decision_keys) <= effective
    assert FIVE not in decision_keys
    assert canonical_sha(provider_keys) == provider["selection"]["processed_source_keys_sha256"]
    assert canonical_sha(wave["decisions"]) == wave["decisions_sha256"]


def test_wave1_new_canonical_is_strictly_preauthority():
    wave = load(WAVE)
    assert len(wave["decisions"]) == 10
    assert all(item["action"] == "NEW_CANONICAL" for item in wave["decisions"])
    assert all("canonical_hotel_id" not in item for item in wave["decisions"])
    assert all(item["evidence"] for item in wave["decisions"])
    sem = wave["decision_semantics"]["NEW_CANONICAL"]
    assert sem == {
        "mapping_state": "RECONCILE_REQUIRED",
        "authority_action": "ALLOCATE_NEW_CANONICAL_ON_AUTHORITY_COMMIT",
        "canonical_h_id_reserved": False,
        "operational_authority": False,
    }
    assert wave["counts"] == {
        "reviewed": 10,
        "new_canonical_preauth": 10,
        "relationship_unresolved": 0,
        "terminal_existing_or_alias": 0,
        "canonical_id_reservations": 0,
        "h_id_allocations": 0,
        "irreversible_external_actions": 0,
    }


def test_wave1_frontier_and_hard_locks_are_conservative():
    wave = load(WAVE)
    assert wave["band_frontier"] == {
        "source_queue_records": 47,
        "already_terminal_exception_records": 1,
        "effective_unresolved_records": 46,
        "reviewed": 10,
        "remaining": 36,
        "terminal_delta_from_wave": 0,
    }
    assert wave["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 29
    assert wave["cumulative_preauthority_frontier"]["overall_relationship_granularity_unresolved"] == 2
    safety = wave["safety"]
    assert safety["authority_advanced"] is False
    assert safety["canonical_id_reservations"] == 0
    assert safety["h_id_allocations"] == 0
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["crm_universe_complete"] is False
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0
    assert safety["irreversible_external_actions"] == 0
    assert wave["next"] == {
        "route": "BOUND_CURRENT_IDENTITY_EVIDENCE_REVIEW_500_599_WAVE2_WITHOUT_AUTOBIND",
        "band_total": 46,
        "reviewed": 10,
        "remaining": 36,
    }
