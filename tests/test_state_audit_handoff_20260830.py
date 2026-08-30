import json
from pathlib import Path

ART = Path("docs/recovery/STATE_AUDIT_HANDOFF_2026-08-30.json")
HANDOFF = Path("docs/handoffs/META_20260830_STATE_AUDIT_DB_EGRESS_HANDOFF.md")


def test_state_audit_handoff_is_exact_scoped_and_fail_closed():
    data = json.loads(ART.read_text(encoding="utf-8"))

    assert data["schema_version"] == "STATE-AUDIT-HANDOFF-1.0"
    assert data["project"] == "SWITZERLAND_JOB_OS"
    assert data["authority"] == "CONTINUITY_AND_RECOVERY_ONLY"

    wave = data["wave"]
    assert wave["parent_main_sha"] == "69fb96168479b210379d83937e8bf041944da450"
    assert wave["execution_mode"] == "RECOVERY_RECONCILE"
    assert wave["closure"] == "COMPLETE_READ_ONLY"
    assert wave["graph_impact"] == "META"

    authority = data["authority_state"]
    assert authority["epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert authority["logical_revision_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert authority["physical_hotels"] == authority["active_canonical"] == 690
    assert authority["persisted_alias_edges"] == 0
    assert authority["next_physical_id"] == "H-0691_UNALLOCATED"
    assert authority["crm_universe_complete"] is False
    assert authority["outbound"] == "CLOSED"
    assert authority["send_allowed"] == 0
    assert authority["authority_advanced_by_audit"] is False

    crm = data["crm_frontier"]
    assert crm["source_records"] == 2061 and crm["source_pages"] == 172
    assert crm["candidate_records"] == crm["exact_current_verified"] == crm["exact_current_total"] == 1438
    assert crm["terminal_source_mappings"] == 657
    assert crm["unique_canonical_targets"] == 656
    assert crm["reconcile_required"] == 1404
    assert crm["reverse_authority_gaps"] == 34
    assert crm["lower_similarity_tail"] == 49

    concurrency = data["concurrency"]
    assert concurrency["active_claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
    assert concurrency["active_fencing_token"] == 5
    assert concurrency["claim_state"] == "ACTIVE_UNTIL_EXPLICIT_RELEASE_OR_SUPERSESSION"
    assert concurrency["token6_branch"]["current_authority"] is False
    assert concurrency["token6_branch"]["pull_request_present"] is False
    assert concurrency["drive_claim_mirror"]["effect"] == "NO_AUTHORITY_CHANGE; GITHUB ACTIVE CLAIM REMAINS BINDING"

    control = data["control_plane_verification"]
    assert control["hotels_v2"]["highest_verified_id"] == "H-0690"
    assert control["hotels_v2"]["h_0691_present"] is False
    assert control["hotels_v2"]["repaired_ids"] == ["H-0610", "H-0624", "H-0629", "H-0630"]
    assert control["operational_graph"]["aliases_to_edges"] == 0
    assert control["checkpoint_registry"] == {
        "l4_current": 105,
        "l4_target": 690,
        "l9_current": 0,
        "l9_target": 690,
    }
    assert set(control["outreach_gates"].values()) == {0}

    recovery = data["durable_db_recovery"]
    v13 = recovery["drive_v13"]
    assert v13["file_id"] == "1rIL6x_bmBoCbxVSAGFvdjoKnUqSX3YnT"
    assert v13["sha256"] == "0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5"
    assert v13["size_bytes"] == 3059712
    assert v13["sqlite_integrity_check"] == "ok"
    assert v13["foreign_key_violations"] == 0
    assert v13["physical_hotel_rows"] == 690
    assert v13["hotel_alias_rows"] == 4
    assert v13["source_mutated"] is False

    e4 = recovery["deterministic_e4_reconstruction"]
    assert e4["sha256"] == authority["logical_revision_sha256"]
    assert e4["sqlite_integrity_check"] == "ok"
    assert e4["foreign_key_violations"] == 0
    assert e4["physical_hotel_rows"] == 690
    assert e4["hotel_alias_rows"] == 0
    assert e4["durably_published"] is False
    assert recovery["failure_family"] == "GENERATED_LOCAL_FILE_REFERENCE_EGRESS_UNAVAILABLE"
    assert recovery["failure_result"] == "BLOCKED_FILE_REFERENCE"
    assert recovery["same_strategy_retry_allowed"] is False
    assert recovery["cross_plane_promotion_eligible"] is False

    pointers = data["pointer_state"]
    assert pointers["pointer_parent_is_ancestor_of_audit_parent"] is True
    assert pointers["shared_pointer_paths_claimed_by_token5"] is True
    assert pointers["audit_rewrote_shared_pointer_paths"] is False

    structured = data["structured_acquisition"]
    assert structured["discover_swiss_subscription_key_present"] is False
    assert structured["capture_valid_manifest_present"] is False
    assert structured["ssr_1_0_state"].startswith("BLOCKED_")

    safety = data["safety"]
    assert safety["never_reserve_canonical_id_from_staging"] is True
    assert safety["never_promote_from_canary_or_cache"] is True
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["authority_advanced"] is False
    assert safety["hotels_master_mutations"] == 0
    assert safety["terminal_mapping_delta"] == 0
    assert safety["h_id_allocations"] == 0
    assert safety["canonical_id_reservations"] == 0
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0
    assert safety["irreversible_external_actions"] == 0

    text = HANDOFF.read_text(encoding="utf-8")
    for required in (
        "VERIFY LIVE TRUTH BEFORE EXECUTION",
        "H-0691 UNALLOCATED",
        "OUTBOUND",
        "BLOCKED_FILE_REFERENCE",
        "CLAIM-CRM-PIE050-LOWER49-005",
        "state/crm-pie050-close-token5-srr-token6-20260830",
        "Never reserve canonical IDs from staging",
        "Never perform a Sheets-first authority mutation",
    ):
        assert required in text
