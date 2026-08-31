import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_LOW_COLLISION_BATCH_0001_33339392661.json"
GRAPH = ROOT / "docs/state/META_GRAPH_DELTA_CRM_CURRENT_LOW_COLLISION_B01_2026-08-31.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_batch_0001_exact_and_fail_closed():
    a = load(ART)
    assert a["schema_version"] == "SRR-CURRENT-LOW-COLLISION-BATCH-1.0"
    assert a["parent_git_sha"] == "cbd3a98c8c0f7c1e35a086fe110f7bdab8032652"
    assert a["source_snapshot"]["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert a["source_snapshot"]["records"] == 2061
    assert a["source_snapshot"]["pages"] == 172
    assert a["source_snapshot"]["coverage_complete"] is True
    assert a["authority"]["materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert a["authority"]["active_canonical"] == 690
    assert a["authority"]["next_physical_id"] == "H-0691_UNALLOCATED"
    assert a["batch"]["count"] == len(a["decisions"]) == 50
    assert len(set(a["batch"]["historical_offsets"])) == 50


def test_batch_0001_selection_contract_is_review_only():
    a = load(ART)
    contract = a["selection_contract"]
    assert contract["fuzzy_autobind"] is False
    assert contract["terminal_mapping_allowed"] is False
    assert contract["canonical_id_reservation_allowed"] is False
    assert contract["similarity_authority"] == "VETO_AND_REVIEW_TRIAGE_ONLY"
    hist = set()
    current = set()
    for d in a["decisions"]:
        assert d["action"] == "NEW_CANONICAL"
        assert d["mapping_state"] == "RECONCILE_REQUIRED"
        assert d["operational_authority"] is False
        assert d["canonical_h_id_reserved"] is False
        assert d["h_id_allocated"] is False
        assert d["global_name_token_jaccard_max_ppm"] < 250000
        hist.add(d["historical_candidate_source_key"])
        current.add(d["current_source_record_key"])
    assert len(hist) == len(current) == 50
    assert a["qa"]["exceptional_terminal_overlap"] == 0
    assert a["qa"]["same_city_collision_count"] == 0
    assert a["qa"]["name_containment_collision_count"] == 0
    assert a["qa"]["max_jaccard_ppm_observed"] <= 200000


def test_batch_0001_counts_do_not_forge_mapping_progress():
    a = load(ART)
    c = a["counts"]
    assert c["cumulative_new_canonical_preauth_before"] == 114
    assert c["cumulative_new_canonical_preauth_after"] == 164
    assert c["remaining_unreviewed_preauthority_after"] == 1239
    assert c["terminal_mapping_delta"] == 0
    assert c["reconcile_required_before"] == c["reconcile_required_after"] == 1403
    assert a["mapping_effect"]["terminal_mappings_before"] == a["mapping_effect"]["terminal_mappings_after"] == 658


def test_batch_0001_hard_locks_and_meta_next():
    a = load(ART)
    s = a["safety"]
    assert s["authority_advanced"] is False
    assert s["h_id_allocations"] == 0
    assert s["canonical_id_reservations"] == 0
    assert s["h_0691"] == "UNALLOCATED"
    assert s["crm_universe_complete"] is False
    assert s["outbound"] == "CLOSED"
    assert s["send_allowed"] == 0
    assert s["irreversible_external_actions"] == 0

    g = load(GRAPH)
    assert g["graph_impact"] == "META"
    next_nodes = [n for n in g["nodes"] if n["type"] == "NEXT"]
    assert len(next_nodes) == 1
    nxt = next_nodes[0]
    assert nxt["route"] == "CURRENT_UNRESOLVED_1403_LOW_COLLISION_BATCH_0002"
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound_allowed"] is False
