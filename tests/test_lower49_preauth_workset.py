import json
from pathlib import Path

from scripts.compile_lower49_preauth_workset import compile_workset, sha256_json

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "docs/operations/CRM_LOWER49_PREAUTH_MATERIALIZATION_WORKSET_2026-08-30.json"
PARENT = "317d5892b5c80f0066a16339ed2a1f10dcdae1ef"


def test_lower49_workset_exact_set_conservation_and_fail_closed():
    payload = compile_workset(ROOT, parent_main_sha=PARENT)
    records = payload["records"]
    keys = [row["source_record_key"] for row in records]
    assert payload["schema_version"] == "CRM-LOWER49-PREAUTH-WORKSET-1.0"
    assert payload["compiled_from_main_sha"] == PARENT
    assert payload["authority"]["materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert payload["materialization_claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert payload["materialization_claim"]["fencing_token"] == 6
    assert payload["ordinary_reviewed_records"] == len(keys) == len(set(keys)) == 47
    assert keys == sorted(keys)
    assert payload["ordinary_source_record_keys_sha256"] == sha256_json(keys)
    assert payload["ordinary_source_record_keys_sha256"] == "be208a70de5850aec03a7c16bca21a589cfe4534943637323b784b45e03cb45d"
    assert payload["excluded_special_source_record_keys"] == [
        "MD-33d867e983644585e4b2",
        "MD-7976c173678dc89c9cf0",
    ]
    assert [batch["items"] for batch in payload["batches"]] == [10, 10, 10, 10, 7]
    flattened = [key for batch in payload["batches"] for key in batch["source_record_keys"]]
    assert flattened == keys
    assert all(row["review_outcome"] == "CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED" for row in records)
    assert all(row["new_identity_status"] == "UNALLOCATED_PREAUTH_CANDIDATE" for row in records)
    assert all(row["terminal_source_mapping"] == "NONE" for row in records)
    assert all(row["authority_effect"] == "NONE" for row in records)
    assert all(row["suggested_hotel_ids"] for row in records)
    assert payload["records_sha256"] == sha256_json(records)
    assert payload["mapping_effect"] == {
        "terminal_mapping_delta": 0,
        "terminal_source_mappings": 658,
        "reconcile_required": 1403,
    }
    assert payload["safety"]["authority_advanced"] is False
    assert payload["safety"]["h_id_allocations"] == 0
    assert payload["safety"]["canonical_id_reservations"] == 0
    assert payload["safety"]["h_0691"] == "UNALLOCATED"
    assert payload["safety"]["crm_universe_complete"] is False
    assert payload["safety"]["outbound"] == "CLOSED"
    assert payload["safety"]["send_allowed"] == 0
    assert payload["safety"]["irreversible_external_actions"] == 0
    assert payload["next"]["batch_id"] == "L49-B01"


def test_committed_workset_matches_compiler_when_materialized():
    if not COMMITTED.exists():
        return
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    expected = compile_workset(ROOT, parent_main_sha=PARENT)
    assert committed == expected
