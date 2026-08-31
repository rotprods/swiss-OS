import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs/state/CRM_CURRENT_UNRESOLVED_LT350_B01_2026-08-31.json"
GRAPH = ROOT / "docs/state/META_GRAPH_DELTA_CRM_CURRENT_LT350_B01_2026-08-31.json"
NEXT = ROOT / "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B01.json"

EXPECTED_KEYS = [
    "MD-006cf8014a406f7c860b",
    "MD-00b5a813d1a39d693130",
    "MD-0178d918d3d8d28271d6",
    "MD-01ae76ba000233702676",
    "MD-01e9ea0e18fbcd931df8",
    "MD-01f7bc45d9b68ffa2950",
    "MD-020599fdbb6c434c0696",
    "MD-02e7960f5bfbc403aafe",
    "MD-0300afd3df838ed5fc0e",
    "MD-033dbc82f02485146685",
]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_b01_selection_and_current_source_are_exact_and_bounded():
    data = _load(STATE)
    assert data["schema_version"] == "CRM-CURRENT-UNRESOLVED-ENTITY-RESOLUTION-WAVE-1.0"
    assert data["wave_id"] == "CURR-U1403-B01"
    assert data["parent_git_sha"] == "cbd3a98c8c0f7c1e35a086fe110f7bdab8032652"
    source = data["source"]
    assert source["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert source["artifact_id"] == 9740219406
    assert source["records"] == 2061
    assert source["pages"] == 172
    assert source["coverage_complete"] is True
    assert source["records_sha256"] == "b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404"

    selection = data["selection"]
    assert selection["historical_lt350000_unreviewed_identity_lineage"] == 1289
    assert selection["same_city_zero_canonical_population"] == 485
    assert selection["batch_size"] == 10
    assert selection["selected_source_record_keys"] == EXPECTED_KEYS
    assert selection["selection_is_authority"] is False


def test_every_b01_decision_is_evidence_backed_preauthority_only():
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
        assert row["cross_city_distinctness_basis"] == "CURRENT_PROPERTY_CITY/ADDRESS_EVIDENCE_DIFFERS_FROM_ALL_GLOBAL_TOP_NAME_CANDIDATE_CITIES"
        assert row["current_evidence"]
        for evidence in row["current_evidence"]:
            assert evidence["tier"] in {"FIRST_PARTY", "QUALIFIED_DESTINATION"}
            assert evidence["url"].startswith("https://")
            assert evidence["fact"]
        assert row["source_evidence_ref"].startswith("HS-MEMBER-DE-33339392661:")


def test_b01_frontier_and_safety_fail_closed():
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
    assert frontier["historical_lt350000_unreviewed_tail_remaining"] == 1279
    assert frontier["terminal_source_mappings"] == 658
    assert frontier["reconcile_required"] == 1403
    assert frontier["h_id_allocations"] == 0
    assert frontier["canonical_id_reservations"] == 0

    qa = data["qa"]
    assert qa["all_decisions_current_evidence_backed"] is True
    assert qa["all_selected_same_city_canonical_count_zero"] is True
    assert qa["cross_city_name_collisions_reviewed"] is True
    assert qa["fuzzy_autobind"] is False
    assert qa["authority_advanced"] is False
    assert qa["h_id_allocations"] == 0
    assert qa["canonical_id_reservations"] == 0
    assert qa["crm_universe_complete"] is False
    assert qa["irreversible_external_actions"] == 0
    assert qa["outbound"] == "CLOSED"
    assert qa["send_allowed"] == 0


def test_graph_and_explicit_next_pointer_preserve_authority_boundary():
    graph = _load(GRAPH)
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert graph["authority_effect"] == "NONE"
    assert nodes["AUTHORITY-E4"]["sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert nodes["CURR-U1403-B01"]["reviewed"] == 10
    assert nodes["CURR-U1403-B01"]["terminal_mapping_delta"] == 0
    assert nodes["OUTBOUND"]["state"] == "CLOSED"
    assert nodes["OUTBOUND"]["send_allowed"] == 0

    nxt = _load(NEXT)
    assert nxt["route"] == "CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B02"
    assert nxt["parent_git_sha"] == "cbd3a98c8c0f7c1e35a086fe110f7bdab8032652"
    assert nxt["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert nxt["authority_parent_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert nxt["historical_lt350000_unreviewed_tail_remaining"] == 1279
    assert nxt["outbound"] == "CLOSED"
    assert nxt["send_allowed"] == 0
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["authority_advance_allowed"] is False
