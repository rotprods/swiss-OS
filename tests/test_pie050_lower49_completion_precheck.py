import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRECHECK = ROOT / "docs/recovery/PIE050_LOWER49_COMPLETION_PRECHECK_2026-08-30.json"
QUEUE = ROOT / "docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json"
PACKETS = [
    ROOT / f"docs/state/PIE050_LOWER49_REVIEW_PACKET_{i:02d}_2026-08-30.json"
    for i in range(1, 6)
]
NEU = ROOT / "docs/state/PIE050_NEUSCHOENSTATT_SAME_PROPERTY_CANDIDATE_2026-08-30.json"
DELTA = ROOT / "docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json"
AUTHORITY_EPOCH = "HS_ENTITY_EPOCH_2026-08-25_E4"
AUTHORITY_SHA = "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def assert_fail_closed_effect(effect):
    assert effect["authority_advanced"] is False
    assert effect["h_id_allocations"] == 0
    assert effect["canonical_id_reservations"] == 0
    assert effect["crm_universe_complete"] is False
    assert effect["outbound"] == "CLOSED"
    assert effect["send_allowed"] == 0


def test_lower49_exact_set_coverage_is_49_of_49_without_terminalization():
    queue = load(QUEUE)
    packets = [load(path) for path in PACKETS]
    neu = load(NEU)
    delta = load(DELTA)

    queue_keys = queue["source_record_keys"]
    assert queue["items_count"] == 49
    assert len(queue_keys) == 49
    assert len(set(queue_keys)) == 49
    assert queue["authority_epoch"] == AUTHORITY_EPOCH
    assert queue["authority_materialized_sha256"] == AUTHORITY_SHA
    assert queue["terminal_mapping_allowed"] is False
    assert queue["canonical_id_reservation_allowed"] is False
    assert queue["h_id_allocations"] == 0
    assert queue["authority_advanced"] is False
    assert queue["crm_universe_complete"] is False
    assert queue["outbound"] == "CLOSED"
    assert queue["send_allowed"] == 0
    assert queue["terminal_source_mappings"] == 657
    assert queue["reconcile_required"] == 1404

    assert [p["reviewed_count"] for p in packets] == [10, 10, 10, 10, 7]
    assert [p.get("reviewed_cumulative", p["reviewed_count"]) for p in packets] == [10, 20, 30, 40, 47]
    assert [p["pending_lower49_after"] for p in packets] == [39, 29, 19, 9, 2]

    ordinary = []
    for packet in packets:
        assert packet["authority_epoch"] == AUTHORITY_EPOCH
        assert packet["authority_materialized_sha256"] == AUTHORITY_SHA
        assert packet["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
        assert packet["fencing_token"] == 5
        assert_fail_closed_effect(packet["effect"])
        assert packet["effect"]["terminal_source_mappings_added"] == 0
        assert packet["effect"]["terminal_source_mappings_total"] == 657
        assert packet["effect"]["reconcile_required_before"] == 1404
        assert packet["effect"]["reconcile_required_after"] == 1404
        for review in packet["reviews"]:
            assert review["source_record_key"] in queue_keys
            assert review["terminal_source_mapping"] == "NONE"
            assert review["authority_effect"] == "NONE"
            assert review["new_identity_status"] == "UNALLOCATED_PREAUTH_CANDIDATE"
            ordinary.append(review["source_record_key"])

    assert len(ordinary) == 47
    assert len(set(ordinary)) == 47

    special_keys = {neu["source_record_key"], delta["source_record_key"]}
    assert special_keys == set(packets[-1]["pending_special_relationship_keys"])
    assert special_keys == {"MD-33d867e983644585e4b2", "MD-7976c173678dc89c9cf0"}
    assert set(ordinary).isdisjoint(special_keys)
    assert set(ordinary) | special_keys == set(queue_keys)

    for special in (neu, delta):
        assert special["authority_epoch"] == AUTHORITY_EPOCH
        assert special["authority_materialized_sha256"] == AUTHORITY_SHA
        assert special["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
        assert special["fencing_token"] == 5
        assert_fail_closed_effect(special["effect"])
        assert special["effect"]["terminal_source_mappings_added"] == 0
        assert special["effect"]["terminal_source_mappings_total"] == 657
        assert special["effect"]["reconcile_required_before"] == 1404
        assert special["effect"]["reconcile_required_after"] == 1404

    assert neu["proposed_terminal_mapping"]["state"] == "PROPOSED_ONLY"
    assert neu["proposed_terminal_mapping"]["terminal_mapping_allowed"] is False
    assert delta["terminal_mapping"]["state"] == "NOT_PROPOSED"
    assert delta["terminal_mapping"]["allowed"] is False


def test_precheck_matches_exact_evidence_and_does_not_authorize_claim_transition():
    precheck = load(PRECHECK)
    queue = load(QUEUE)
    packets = [load(path) for path in PACKETS]
    neu = load(NEU)
    delta = load(DELTA)

    assert precheck["schema_version"] == "PIE050-LOWER49-COMPLETION-PRECHECK-1.0"
    assert precheck["authority"] == "PREAUTH_COMPLETION_EVIDENCE_ONLY"
    assert precheck["authority_epoch"] == AUTHORITY_EPOCH
    assert precheck["authority_revision_sha256"] == AUTHORITY_SHA
    assert precheck["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
    assert precheck["fencing_token"] == 5
    assert precheck["queue"] == str(QUEUE.relative_to(ROOT))
    assert precheck["review_packets"] == [str(p.relative_to(ROOT)) for p in PACKETS]
    assert precheck["special_review_artifacts"] == [str(NEU.relative_to(ROOT)), str(DELTA.relative_to(ROOT))]

    expected = precheck["expected"]
    assert expected == {
        "queue_records": 49,
        "ordinary_reviewed": 47,
        "special_reviewed": 2,
        "classification_coverage": "49/49",
        "terminal_source_mapping_delta": 0,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "crm_universe_complete": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    assert sum(p["reviewed_count"] for p in packets) == expected["ordinary_reviewed"]
    assert len({neu["source_record_key"], delta["source_record_key"]}) == expected["special_reviewed"]
    assert queue["items_count"] == expected["queue_records"]
    assert precheck["claim_transition_authorized_by_this_artifact"] is False
    assert precheck["verify_live_truth_before_execution"] is True
    assert "must not terminalize" in precheck["next_if_ci_and_adversarial_review_pass"]
