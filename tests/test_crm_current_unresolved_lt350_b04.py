import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs/state/CRM_CURRENT_UNRESOLVED_LT350_B04_2026-08-31.json"
B03 = ROOT / "docs/state/CRM_CURRENT_UNRESOLVED_LT350_B03_2026-08-31.json"
GRAPH = ROOT / "docs/state/META_GRAPH_DELTA_CRM_CURRENT_LT350_B04_2026-08-31.json"
NEXT = ROOT / "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B04.json"
EXPECTED_KEYS = ["MD-0ec9184e0553996c8017","MD-11392326bb8d2e36b225","MD-12012a3229867154fec7","MD-12981db89c28b8b3af89","MD-12ddaa1053593368724c","MD-13927887bbb57d617e5e","MD-139b78cdebb6cec44ad5","MD-147ce42ea282ff9d8373","MD-14b893f819ede5ee43f9","MD-14f0349e0f07cd0d3ae0"]
EXPECTED_NEXT = ["MD-1523bc8c54a8f80c63a1","MD-15328beab2813a777e0d","MD-1679afa763ce7de7c324","MD-16d503bef0fa48f1d44d","MD-172e10497469ac29259e","MD-17a059dc9632c6ff4d1d","MD-17af64859ef43e875027","MD-1855265ec07d6b3c1a40","MD-18cbb9206e15539f177d","MD-18ddf5bd589df297650d"]

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def test_exact_fresh_main_continuation():
    data, b03 = load(STATE), load(B03)
    assert data["parent_git_sha"] == "a3299117a0fa1168b0b36f4da4b2f95cb1ea7719"
    assert data["selection"]["selected_source_record_keys"] == EXPECTED_KEYS
    assert b03["selection"]["selected_source_record_keys"][-1] == "MD-0dffa4b98adaf08c2499"
    assert data["selection"]["prior_current_reviewed"] == 30
    assert data["source"]["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert data["source"]["records"] == 2061 and data["source"]["coverage_complete"] is True

def test_all_rows_current_and_preauthority():
    data = load(STATE)
    assert len(data["decisions"]) == 10
    for row in data["decisions"]:
        assert row["same_city_canonical_count"] == 0
        assert row["current_max_same_city_token_jaccard_ppm"] == 0
        assert row["decision"] == "NEW_CANONICAL_PREAUTH"
        assert row["mapping_state"] == "RECONCILE_REQUIRED"
        assert row["canonical_h_id_reserved"] is False
        assert row["h_id_allocated"] is False
        assert row["terminal_mapping_created"] is False
        assert row["authority_effect"] == "NONE"
        assert row["current_evidence"]
        assert all(e["url"].startswith("https://") and e["fact"] for e in row["current_evidence"])

def test_high_similarity_radisson_collisions_fail_closed():
    data = load(STATE)
    for key in ("MD-0ec9184e0553996c8017", "MD-14f0349e0f07cd0d3ae0"):
        row = next(x for x in data["decisions"] if x["source_record_key"] == key)
        review = row["canonical_collision_review"]
        assert review["canonical_hotel_id"] == "H-0222"
        assert review["same_real_world_entity"] is False
        assert review["match_existing_proven"] is False
        assert row["global_max_token_jaccard_ppm"] >= 600000
        assert row["mapping_state"] == "RECONCILE_REQUIRED"

def test_solution_grischun_preserves_granularity():
    data = load(STATE)
    row = next(x for x in data["decisions"] if x["source_record_key"] == "MD-139b78cdebb6cec44ad5")
    egr = row["entity_granularity_review"]
    assert egr["protocol"] == "EGR-1.0"
    assert egr["relationship"] == "OPERATOR_MANAGED_MULTI_UNIT_HOLIDAY_APARTMENTS"
    assert egr["legal_seat_city"] == "Bonaduz" and egr["managed_accommodation_city"] == "Chur"
    assert egr["single_physical_hotel_identity_proven"] is False
    assert egr["collapse_to_alias_proven"] is False

def test_frontier_graph_next_and_safety():
    data, graph, nxt = load(STATE), load(GRAPH), load(NEXT)
    f = data["frontier"]
    assert f["current_lt350000_reviewed_cumulative"] == 40
    assert f["cumulative_new_canonical_preauth"] == 154
    assert f["historical_lt350000_unreviewed_tail_remaining"] == 1249
    assert f["zero_same_city_lane_remaining"] == 445
    assert f["terminal_source_mappings"] == 658 and f["reconcile_required"] == 1403
    assert f["h_id_allocations"] == 0 and f["canonical_id_reservations"] == 0
    assert data["authority"]["canonical_rows"] == 690
    assert data["authority"]["next_physical_id"] == "H-0691_UNALLOCATED"
    assert data["qa"]["authority_advanced"] is False
    assert data["qa"]["outbound"] == "CLOSED" and data["qa"]["send_allowed"] == 0
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["CURR-U1403-B04"]["terminal_mapping_delta"] == 0
    assert nodes["EGR-SOLUTION-GRISCHUN"]["single_physical_hotel_identity_proven"] is False
    assert nxt["parent_git_sha"] == "a3299117a0fa1168b0b36f4da4b2f95cb1ea7719"
    assert nxt["route"] == "CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B05"
    assert nxt["b04_source_record_keys"] == EXPECTED_KEYS and nxt["b05_source_record_keys"] == EXPECTED_NEXT
    assert nxt["authority_advance_allowed"] is False and nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound"] == "CLOSED" and nxt["send_allowed"] == 0
