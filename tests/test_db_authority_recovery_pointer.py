import json
from pathlib import Path

POINTER = Path("docs/recovery/DB_AUTHORITY_EGRESS_RECOVERY_POINTER_2026-08-30.json")


def test_recovery_pointer_is_explicit_and_fail_closed():
    data = json.loads(POINTER.read_text(encoding="utf-8"))
    assert data["schema_version"] == "RECOVERY-NEXT-POINTER-1.0"
    assert data["authority"] == "RECOVERY_ONLY_NOT_CANONICAL_STATE"
    assert data["verify_live_truth_before_execution"] is True
    assert data["parent_main_sha"] == "78daa43661867cfcb66a379a367380eb1fe9b22b"
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority_materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert data["next_route"] == "PROVIDER_EGRESS_CAPABILITY_OR_DURABLE_FILE_REFERENCE_BRIDGE_THEN_FRESH_CROSS_PLANE_AUTHORITY_TRANSACTION"

    blockers = {b["id"]: b for b in data["exact_blockers"]}
    assert blockers["DB-EGRESS-BLOCKED-FILE-REFERENCE"]["state"] == "BLOCKED_PROVIDER_RUNTIME_BOUNDARY"
    assert blockers["DISCOVER-SWISS-INFOCENTER-KEY"]["state"] == "BLOCKED_PROVIDER_CREDENTIAL_BOUNDARY"
    assert blockers["PIE050-SPECIAL-AUTHORITY"]["state"] == "BLOCKED_AUTHORITY_UNTIL_REVALIDATED"

    recovery = data["recovery_inputs"]
    assert recovery["drive_recovery_document_id"] == "17qlWRTTXc44jTAkuZRI5ZYWoZZEQUCb0d6uqy0fbaWs"
    assert recovery["drive_v13_file_id"] == "1rIL6x_bmBoCbxVSAGFvdjoKnUqSX3YnT"
    assert recovery["drive_v13_sha256"] == "0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5"
    assert recovery["source_actions_artifact_id"] == 9700376482
    assert recovery["candidate_actions_artifact_id"] == 9718866661

    frontier = data["known_frontier"]
    assert frontier["source_records"] == 2061
    assert frontier["candidate_records"] == frontier["exact_current_verified"] == 1438
    assert frontier["terminal_source_mappings"] == 657
    assert frontier["reconcile_required"] == 1404
    assert frontier["active_canonical"] == 690
    assert frontier["next_h_id"] == "H-0691_UNALLOCATED"

    locks = data["hard_invariants"]
    assert locks["crm_universe_complete"] is False
    assert locks["outbound"] == "CLOSED"
    assert locks["send_allowed"] == 0
    assert locks["authority_advanced_by_this_pointer"] is False
    assert locks["terminal_mapping_delta"] == 0
    assert locks["h_id_allocations"] == locks["canonical_id_reservations"] == 0
    assert locks["authority_from_canary_or_cache"] is False
    assert locks["irreversible_external_actions"] == 0
