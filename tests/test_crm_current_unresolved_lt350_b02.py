import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs/state/CRM_CURRENT_UNRESOLVED_LT350_B02_2026-08-31.json"
B01 = ROOT / "docs/state/CRM_CURRENT_UNRESOLVED_LT350_B01_2026-08-31.json"
GRAPH = ROOT / "docs/state/META_GRAPH_DELTA_CRM_CURRENT_LT350_B02_2026-08-31.json"
NEXT = ROOT / "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B02.json"

EXPECTED_KEYS = [
    "MD-035b5210d0ba7c40e2dc",
    "MD-0533f553d1515e575678",
    "MD-05437a0df9c5f16eb59f",
    "MD-05712ee9e6b1b30f6115",
    "MD-05a7076d9d28f407abc9",
    "MD-065efacba8eac2661541",
    "MD-0679b9bde241ca8a8656",
    "MD-06c32cbfa2c70b940bd9",
    "MD-076dcaba17c708193252",
    "MD-090ec6200cc0bd1136f3"
]
EXPECTED_NEXT_KEYS = [
    "MD-093d8446cfe53ffec88b",
    "MD-09963b437cb80cee857c",
    "MD-09a234f3dc4beac16e95",
    "MD-0a64704ec8d9b0ca8a70",
    "MD-0a77a406de39fa90cbab",
    "MD-0c0ecaa4c33ef165153c",
    "MD-0d0e11f71cd8fa3382d9",
    "MD-0d8236983bc08da309d7",
    "MD-0ddfa1e31ababc955395",
    "MD-0dffa4b98adaf08c2499"
]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_b02_selection_continues_exactly_after_b01():
    data = _load(STATE)
    b01 = _load(B01)
    assert data["schema_version"] == "CRM-CURRENT-UNRESOLVED-ENTITY-RESOLUTION-WAVE-1.0"
    assert data["wave_id"] == "CURR-U1403-B02"
    assert data["parent_git_sha"] == "0807b4a81f8b8efc71040b6631f15bc1ee21c0cf"
    assert b01["selection"]["selected_source_record_keys"][-1] == "MD-033dbc82f02485146685"
    assert data["selection"]["selected_source_record_keys"] == EXPECTED_KEYS
    assert data["selection"]["prior_current_reviewed"] == 10
    assert data["selection"]["batch_size"] == 10
    assert data["selection"]["selection_is_authority"] is False
    source = data["source"]
    assert source["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert source["artifact_id"] == 9740219406
    assert source["records"] == 2061
    assert source["pages"] == 172
    assert source["coverage_complete"] is True
    assert source["records_sha256"] == "b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404"


def test_every_b02_decision_is_current_evidence_backed_and_preauthority():
    data = _load(STATE)
    decisions = data["decisions"]
    assert len(decisions) == 10
    assert [row["source_record_key"] for row in decisions] == EXPECTED_KEYS
    assert len({row["source_record_key"] for row in decisions}) == 10
    for ordinal, row in enumerate(decisions, start=1):
        assert row["ordinal"] == ordinal
        assert row["historical_similarity_band"] == "lt350000"
        assert row["same_city_canonical_count"] == 0
        assert row["current_max_same_city_token_jaccard_ppm"] == 0
        assert row["decision"] == "NEW_CANONICAL_PREAUTH"
        assert row["mapping_state"] == "RECONCILE_REQUIRED"
        assert row["canonical_h_id_reserved"] is False
        assert row["h_id_allocated"] is False
        assert row["terminal_mapping_created"] is False
        assert row["authority_effect"] == "NONE"
        assert row["current_evidence"]
        assert row["source_evidence_ref"].startswith("HS-MEMBER-DE-33339392661:")
        for evidence in row["current_evidence"]:
            assert evidence["tier"] in {"FIRST_PARTY", "QUALIFIED_DESTINATION"}
            assert evidence["url"].startswith("https://")
            assert evidence["fact"]


def test_meisser_granularity_is_explicit_and_does_not_alias():
    data = _load(STATE)
    meisser = next(row for row in data["decisions"] if row["source_record_key"] == "MD-06c32cbfa2c70b940bd9")
    egr = meisser["entity_granularity_review"]
    assert egr["protocol"] == "EGR-1.0"
    assert egr["related_source_record_key"] == "MD-01f7bc45d9b68ffa2950"
    assert egr["relationship"] == "SIBLING_ACCOMMODATION_PRODUCTS_WITHIN_MEISSER_RESORT"
    assert egr["collapse_to_alias_proven"] is False
    assert egr["relationship_metadata_preserved"] is True
    assert meisser["mapping_state"] == "RECONCILE_REQUIRED"
    assert meisser["terminal_mapping_created"] is False


def test_b02_frontier_and_safety_remain_fail_closed():
    data = _load(STATE)
    authority = data["authority"]
    assert authority == {
        "canonical_rows": 690,
        "effect": "NONE",
        "epoch": "HS_ENTITY_EPOCH_2026-08-25_E4",
        "materialized_sha256": "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6",
        "next_physical_id": "H-0691_UNALLOCATED",
    }
    frontier = data["frontier"]
    assert frontier["batch_reviewed"] == 10
    assert frontier["batch_new_canonical_preauth"] == 10
    assert frontier["batch_terminal_mapping_delta"] == 0
    assert frontier["current_lt350000_reviewed_cumulative"] == 20
    assert frontier["historical_lt350000_unreviewed_tail_remaining"] == 1269
    assert frontier["zero_same_city_lane_remaining"] == 465
    assert frontier["cumulative_new_canonical_preauth"] == 134
    assert frontier["terminal_source_mappings"] == 658
    assert frontier["reconcile_required"] == 1403
    assert frontier["h_id_allocations"] == 0
    assert frontier["canonical_id_reservations"] == 0
    qa = data["qa"]
    assert qa["authority_advanced"] is False
    assert qa["h_id_allocations"] == 0
    assert qa["canonical_id_reservations"] == 0
    assert qa["crm_universe_complete"] is False
    assert qa["irreversible_external_actions"] == 0
    assert qa["outbound"] == "CLOSED"
    assert qa["send_allowed"] == 0


def test_graph_and_next_pointer_chain_to_b03_without_authority_change():
    graph = _load(GRAPH)
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert graph["authority_effect"] == "NONE"
    assert nodes["AUTHORITY-E4"]["sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert nodes["CURR-U1403-B02"]["reviewed"] == 10
    assert nodes["CURR-U1403-B02"]["terminal_mapping_delta"] == 0
    assert nodes["EGR-MEISSER-HOTEL-LODGE"]["identity_collapse_proven"] is False
    assert nodes["OUTBOUND"]["state"] == "CLOSED"
    assert nodes["OUTBOUND"]["send_allowed"] == 0
    nxt = _load(NEXT)
    assert nxt["route"] == "CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B03"
    assert nxt["parent_git_sha"] == "0807b4a81f8b8efc71040b6631f15bc1ee21c0cf"
    assert nxt["b02_source_record_keys"] == EXPECTED_KEYS
    assert nxt["b03_source_record_keys"] == EXPECTED_NEXT_KEYS
    assert nxt["historical_lt350000_unreviewed_tail_remaining"] == 1269
    assert nxt["zero_same_city_remaining"] == 465
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound"] == "CLOSED"
    assert nxt["send_allowed"] == 0
