import json
from pathlib import Path

ART = Path("docs/recovery/CRM_E4_DURABLE_EGRESS_MEP_FALLBACK_2026-08-30.json")


def test_e4_egress_mep_is_exact_and_fail_closed():
    data = json.loads(ART.read_text(encoding="utf-8"))
    assert data["schema_version"] == "CRM-E4-DURABLE-EGRESS-MEP-1.0"
    assert data["parent_git_sha"] == "78daa43661867cfcb66a379a367380eb1fe9b22b"
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"

    src = data["source_v13"]
    assert src["drive_file_id"] == "1rIL6x_bmBoCbxVSAGFvdjoKnUqSX3YnT"
    assert src["sha256"] == "0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5"
    assert src["size_bytes"] == 3059712
    assert src["raw_fetch"] == "PASS"

    rec = data["reconstruction"]
    assert rec["copy_only"] is True
    assert rec["result_sha256"] == data["authority_materialized_sha256"]
    assert rec["sqlite_integrity_check"] == "ok"
    assert rec["foreign_key_violations"] == 0
    assert rec["physical_hotel_rows"] == 690
    assert rec["hotel_alias_rows"] == 0

    egress = data["egress_mep"]
    assert egress["strategy_1"]["result"] == "BLOCKED_FILE_REFERENCE"
    assert egress["strategy_2"]["result"] == "BLOCKED_FILE_REFERENCE"
    assert egress["probe_copy_postcondition"] == "RENAMED_EXPLICITLY_AS_SOURCE_V13_COPY_NOT_E4"
    assert egress["durable_e4_binary_published"] is False

    effect = data["authority_effect"]
    assert effect["authority_advanced"] is False
    assert effect["terminal_source_mapping_delta"] == 0
    assert effect["hotels_master_mutations"] == 0
    assert effect["h_id_allocations"] == 0
    assert effect["canonical_id_reservations"] == 0
    assert effect["crm_universe_complete"] is False
    assert effect["outbound"] == "CLOSED"
    assert effect["send_allowed"] == 0
    assert effect["irreversible_external_actions"] == 0

    safety = data["safety"]
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["never_reserve_from_staging"] is True
    assert safety["never_promote_from_canary_or_cache"] is True
    assert safety["verify_live_truth_before_execution"] is True
