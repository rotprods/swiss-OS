import json
from pathlib import Path

ART = Path("docs/state/DB_AUTHORITY_ARTIFACT_RECOVERY_PREFLIGHT_2026-08-30.json")


def test_recovery_preflight_proves_exact_reconstruction_but_fails_closed_on_egress():
    data = json.loads(ART.read_text(encoding="utf-8"))
    assert data["schema_version"] == "DB-AUTHORITY-ARTIFACT-RECOVERY-PREFLIGHT-1.0"
    assert data["parent_git_sha"] == "41e4721d7b47779aac32f9998da7ac27b25de6d5"
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"

    v13 = data["drive_v13"]
    assert v13["file_id"] == "1rIL6x_bmBoCbxVSAGFvdjoKnUqSX3YnT"
    assert v13["size_bytes"] == 3059712
    assert v13["expected_sha256"] == v13["reverified_sha256"] == "0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5"
    assert v13["raw_fetch_result"] == "PASS"

    repair = data["deterministic_repair"]
    assert repair["source_copy_only"] is True
    assert repair["source_file_mutated"] is False
    assert repair["result_sha256"] == repair["expected_result_sha256"] == data["authority_materialized_sha256"]
    assert repair["byte_exact_expected_result"] is True
    assert repair["sqlite_integrity_check"] == "ok"
    assert repair["foreign_key_violations"] == 0
    assert repair["physical_hotel_rows"] == 690
    assert repair["hotel_alias_rows_after_repair"] == 0
    assert len(repair["sql"]) == 2

    egress = data["durable_egress_probe"]
    assert egress["result"] == "BLOCKED_FILE_REFERENCE"
    assert egress["durable_repaired_db_created"] is False
    assert egress["existing_v13_overwritten"] is False
    assert data["blocker_refinement"]["authority_promotion_eligible"] is False

    effect = data["authority_effect"]
    assert effect["authority_advanced"] is False
    assert effect["hotels_master_mutations"] == 0
    assert effect["terminal_source_mapping_delta"] == 0
    assert effect["h_id_allocations"] == effect["canonical_id_reservations"] == 0
    assert effect["crm_universe_complete"] is False
    assert effect["outbound"] == "CLOSED"
    assert effect["send_allowed"] == 0
    assert effect["irreversible_external_actions"] == 0
