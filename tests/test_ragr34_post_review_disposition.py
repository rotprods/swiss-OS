import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSET_PATH = ROOT / "docs/state/RAGR34_POST_REVIEW_DISPOSITION_WORKSET_2026-08-30.json"
QUEUE_PATH = ROOT / "docs/state/RAGR_REVIEW_QUEUE_34_33206402141.json"

EXPECTED_COUNTS = {
    "COMPONENT/GROUP GRANULARITY": 2,
    "DATA DEFECT": 3,
    "IN_SCOPE_NO_SOURCE_MATCH": 24,
    "SUPERSEDED/RENAMED WITH EVIDENCE": 5,
}
EXPECTED_ROWS_SHA256 = "c856954186f45c149cd7547852d86b87c54b24e19a7aa31859d971b77cf9c975"
SOURCE_PATHS = {
    "RAGR34-B01": "docs/state/RAGR_CURRENT_EVIDENCE_B01_2026-08-30.json",
    "RAGR34-B02": "docs/state/RAGR_CURRENT_EVIDENCE_B02_2026-08-30.json",
    "RAGR34-B03": "docs/state/RAGR_CURRENT_EVIDENCE_B03_2026-08-30.json",
    "RAGR34-B04": "docs/state/RAGR_CURRENT_EVIDENCE_B04_2026-08-30.json",
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_rows(rows):
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def test_workset_is_exact_queue_order_and_complete():
    workset = _load(WORKSET_PATH)
    queue = _load(QUEUE_PATH)
    rows = workset["rows"]
    expected_ids = queue["ragr"]["gap_hotel_ids"]

    assert len(rows) == 34
    assert [row["ordinal"] for row in rows] == list(range(1, 35))
    assert [row["hotel_id"] for row in rows] == expected_ids
    assert workset["queue"]["ordered_hotel_ids"] == expected_ids
    assert len(set(expected_ids)) == 34


def test_workset_hash_and_classification_conservation():
    workset = _load(WORKSET_PATH)
    rows = workset["rows"]
    counts = Counter(row["classification"] for row in rows)

    assert dict(counts) == EXPECTED_COUNTS
    assert workset["classification_counts"] == EXPECTED_COUNTS
    assert _sha_rows(rows) == EXPECTED_ROWS_SHA256
    assert workset["rows_sha256"] == EXPECTED_ROWS_SHA256


def test_workset_preserves_source_decisions_without_promoting_them():
    workset = _load(WORKSET_PATH)
    source_meta = {item["source_batch"]: item for item in workset["source_batches"]}

    for batch_id, rel_path in SOURCE_PATHS.items():
        source = _load(ROOT / rel_path)
        assert source_meta[batch_id]["path"] == rel_path
        assert source_meta[batch_id]["decisions_sha256"] == source["decisions_sha256"]

    for row in workset["rows"]:
        source = _load(ROOT / SOURCE_PATHS[row["source_batch"]])
        decision = source["decisions"][row["source_decision_index"]]

        assert row["hotel_id"] == decision["hotel_id"]
        assert row["classification"] == decision["classification"]
        assert row["reason_code"] == decision["reason_code"]
        assert row["review_only"] is True
        assert row["terminal_source_mapping_created"] is False
        assert row["authority_mutation_allowed"] is False

        if "followup" in decision:
            assert row["followup"] == decision["followup"]
            assert row["followup_origin"] == "SOURCE"
        else:
            assert row["source_batch"] == "RAGR34-B01"
            assert row["followup_origin"] == "DERIVED_SAFE_PARTITION"


def test_safety_and_authority_boundaries_remain_closed():
    workset = _load(WORKSET_PATH)
    safety = workset["safety"]
    authority = workset["authority"]
    effect = workset["mapping_effect"]

    assert authority["epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert authority["materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert authority["physical_rows"] == 690
    assert authority["active_canonical"] == 690
    assert authority["next_physical_id"] == "H-0691_UNALLOCATED"
    assert authority["advanced"] is False

    assert safety == {
        "authority_advanced": False,
        "canonical_deactivations": 0,
        "canonical_id_reservations": 0,
        "crm_universe_complete": False,
        "h_0691": "UNALLOCATED",
        "h_id_allocations": 0,
        "irreversible_external_actions": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "terminal_source_mappings_created": 0,
    }

    assert effect == {
        "reverse_authority_gaps_after": 34,
        "reverse_authority_gaps_before": 34,
        "terminal_mappings_after": 658,
        "terminal_mappings_before": 658,
    }


def test_next_route_is_safe_review_only_source_identity_sweep():
    workset = _load(WORKSET_PATH)
    assert workset["next"]["route"] == "RAGR34_IN_SCOPE_NO_SOURCE_MATCH_SOURCE_IDENTITY_SWEEP"
    assert workset["next"]["verify_live_truth_before_execution"] is True
    assert "durable receipt" in workset["next"]["exact_dependency"]
    assert "Do not promote" in workset["next"]["exact_dependency"]
