import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANTI = ROOT / "docs/state/SOURCE_RESOLUTION_REVIEW_UNRESOLVED_1403_33206402141.json"
FULL = ROOT / "docs/state/FULL_SOURCE_MAPPING_REBUILD_658_ATTESTATION_33206402141.json"
GRAPH = ROOT / "docs/state/META_GRAPH_DELTA_CRM_UNRESOLVED1403_2026-08-30.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_unresolved_anti_join_is_exact_and_conservative():
    anti = load(ANTI)
    full = load(FULL)
    assert anti["schema_version"] == "CRM-UNRESOLVED-ANTI-JOIN-STAGING-1.0"
    assert anti["parent_git_sha"] == "ca72ff9edd8b7da89a8289ee723a090ac86e0a69"
    assert anti["inputs"]["candidate_records"] == 1438
    assert anti["inputs"]["exceptional_terminal_source_keys"] == 35
    assert anti["inputs"]["terminal_source_mappings"] == full["rebuild"]["terminal_source_mappings"] == 658
    assert anti["inputs"]["terminal_pairs_sha256"] == full["rebuild"]["terminal_pairs_sha256"]
    aj = anti["anti_join"]
    assert aj["unresolved_candidate_records"] == full["rebuild"]["reconcile_required"] == 1403
    assert aj["unresolved_source_keys_sha256"] == full["rebuild"]["unresolved_source_keys_sha256"]
    assert aj["all_offsets_unique"] is True
    assert 35 + aj["unresolved_candidate_records"] == 1438
    assert full["rebuild"]["terminal_source_mappings"] + aj["unresolved_candidate_records"] == 2061


def test_staging_is_complete_29_batch_partition():
    anti = load(ANTI)
    staging = anti["staging"]
    assert staging["batch_size"] == 50
    assert staging["batches_count"] == 29
    batches = staging["batches"]
    assert len(batches) == 29
    assert [item["batch_id"] for item in batches] == [f"U1403-{i:02d}" for i in range(1, 30)]
    assert all(item["count"] == 50 for item in batches[:-1])
    assert batches[-1]["count"] == 3
    assert sum(item["count"] for item in batches) == 1403
    assert len({item["source_record_keys_sha256"] for item in batches}) == 29
    assert staging["batches_sha256"] == "2b699f7320d5c914d8e3fb3e2cff3c87a3332d6fd42fa1cdf6ef5cff6fe0f3e5"


def test_similarity_is_review_only_and_bands_cover_all_unresolved():
    anti = load(ANTI)
    pr = anti["review_priority"]
    assert pr["similarity_authority"] == "REVIEW_SPACE_REDUCTION_ONLY"
    assert pr["terminal_decision_allowed_from_similarity"] is False
    assert pr["bands"] == {
        "350000_499999": 48,
        "500000_599999": 46,
        "ge600000": 20,
        "lt350000": 1289,
    }
    assert sum(pr["bands"].values()) == 1403
    assert pr["priority_ge600_count"] == len(pr["priority_ge600_items"]) == 20
    assert pr["priority_ge600_items_sha256"] == "19b6fd5db0af403af689ae5d96f03f238858bd5325d5c00bd204cf7fa3c158b2"
    keys = set()
    for item in pr["priority_ge600_items"]:
        assert item["source_record_key"] not in keys
        keys.add(item["source_record_key"])
        assert item["max_token_jaccard_ppm"] >= 600000
        assert item["evidence_role"] == "REVIEW_SPACE_REDUCTION_ONLY"
        assert item["terminal_mapping_allowed"] is False
        assert item["canonical_id_reservation_allowed"] is False
        assert item["authority_action"] == "NONE"
        assert item["suggested_hotel_ids"]


def test_hard_locks_and_e4_egress_boundary_are_persisted():
    anti = load(ANTI)
    safety = anti["safety"]
    assert safety == {
        "authority_advanced": False,
        "canonical_id_reservations": 0,
        "crm_universe_complete": False,
        "h_0691": "UNALLOCATED",
        "h_id_allocations": 0,
        "irreversible_external_actions": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    graph = load(GRAPH)
    nodes = {item["id"]: item for item in graph["nodes"]}
    exact = nodes["EXACT-E4-LOCAL-RECONSTRUCTION"]
    assert exact["sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert exact["rows"] == 690
    assert exact["aliases"] == 0
    assert exact["integrity"] == "ok"
    assert exact["authority_effect"] == "NONE"
    blocked = nodes["BLOCK-E4-DURABLE-FILE-EGRESS"]
    assert blocked["result"] == "BLOCKED_FILE_REFERENCE"
    assert blocked["retry_same_route"] is False
    assert nodes["OUTBOUND"]["state"] == "CLOSED"
    assert nodes["OUTBOUND"]["send_allowed"] == 0
