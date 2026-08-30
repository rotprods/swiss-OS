import json
from pathlib import Path

POINTER = Path("docs/recovery/DB_EGRESS_CAPABILITY_GAUNTLET_2026-08-30.json")
CANONICAL = Path("docs/recovery/CRM_E4_DURABLE_EGRESS_MEP_FALLBACK_2026-08-30.json")


def test_historical_gauntlet_path_is_non_authoritative_supersession_pointer():
    pointer = json.loads(POINTER.read_text(encoding="utf-8"))
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))

    assert pointer["schema_version"] == "RECOVERY-SUPERSESSION-POINTER-1.0"
    assert pointer["authority"] == "SUPERSEDED_POINTER_ONLY"
    assert pointer["superseded_by"] == str(CANONICAL)
    assert pointer["canonical_surface_schema_version"] == canonical["schema_version"] == "CRM-E4-DURABLE-EGRESS-MEP-1.1"
    assert pointer["canonical_merge_pr"] == 342
    assert pointer["canonical_merge_sha"] == "3afe2ef55acdc41b82f7899dec5bf9e7f7f40f6a"
    assert pointer["failure_family"] == canonical["egress_mep"]["failure_family"] == "GENERATED_LOCAL_FILE_REFERENCE_EGRESS_UNAVAILABLE"
    assert pointer["retry_same_file_reference_strategy_allowed"] is False
    assert pointer["verify_live_truth_before_execution"] is True

    effect = pointer["authority_effect"]
    assert effect["authority_advanced"] is False
    assert effect["hotels_master_mutations"] == effect["terminal_mapping_delta"] == 0
    assert effect["h_id_allocations"] == effect["canonical_id_reservations"] == 0
    assert effect["crm_universe_complete"] is False
    assert effect["outbound"] == "CLOSED" and effect["send_allowed"] == 0
    assert effect["irreversible_external_actions"] == 0
