from __future__ import annotations

import json
from pathlib import Path


STATE = Path(__file__).parents[1] / "docs/state/CRM_CURRENT_SOURCE_MAPPING_PROJECTION_33339392661.json"


def test_current_complete_projection_is_conservative() -> None:
    data = json.loads(STATE.read_text(encoding="utf-8"))
    source = data["source"]
    exact = data["exact_staging"]
    reviewed = data["reviewed_mapping_projection"]
    qa = data["qa"]

    assert source["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert source["coverage_complete"] is True
    assert source["records"] == 2061
    assert source["pages"] == 172
    assert source["violations"] == []

    assert exact["ACTIVE_MATCH"] == 623
    assert exact["ALIAS_MATCH"] == 0
    assert exact["TRUE_MISSING"] == 1438
    assert exact["CONFLICT"] == 0
    assert exact["EXCLUSION_CANDIDATE"] == 0
    assert exact["TOTAL"] == 2061
    assert exact["H_ID_ALLOCATIONS"] == 0
    assert exact["reverse_exact_gap_count"] == 67

    assert reviewed["reviewed_exceptional_mappings_carried"] == 35
    assert reviewed["carry_forward_missing"] == 0
    assert reviewed["terminal_source_mappings"] == 658
    assert reviewed["unique_canonical_targets"] == 656
    assert reviewed["reconcile_required"] == 1403
    assert reviewed["reverse_authority_source_gaps"] == 34
    assert len(reviewed["reverse_authority_source_gap_ids"]) == 34
    assert len(reviewed["carry_forward_mappings"]) == 35

    assert qa["source_manifest_coherent_complete"] is True
    assert qa["source_record_partition_conserved"] is True
    assert qa["terminal_source_keys_unique"] is True
    assert qa["all_terminal_targets_exist_in_690_projection"] is True
    assert qa["prior_reviewed_exceptions_all_projected"] is True
    assert qa["ragr34_gap_set_unchanged"] is True
    assert qa["fuzzy_autobind"] is False
    assert qa["authority_advanced"] is False
    assert qa["canonical_id_reservations"] == 0
    assert qa["h_id_allocations"] == 0
    assert qa["crm_universe_complete"] is False
    assert qa["outbound"] == "CLOSED"
    assert qa["send_allowed"] == 0
    assert qa["irreversible_external_actions"] == 0


def test_refresh_delta_is_bounded_and_reviewed_mappings_survive() -> None:
    data = json.loads(STATE.read_text(encoding="utf-8"))
    delta = data["historical_source"]["source_delta_to_current"]
    reviewed = data["reviewed_mapping_projection"]

    assert delta["common_identity_records"] == 2059
    assert delta["added_count"] == 2
    assert delta["removed_count"] == 2
    assert delta["detail_url_changed_on_common_identity_count"] == 0
    assert {row["name"] for row in delta["added"]} == {
        "Huus Bären 1602",
        "Huus Löwen 1878",
    }
    assert {row["name"] for row in delta["removed"]} == {
        "Appenzeller Huus, Huus Bären",
        "Appenzeller Huus, Huus Löwen",
    }

    carry = reviewed["carry_forward_mappings"]
    assert len({row["old_source_record_key"] for row in carry}) == 35
    assert len({row["new_source_record_key"] for row in carry}) == 35
    assert all(
        row["migration_basis"]
        == "UNCHANGED_NORMALIZED_NAME_CITY_AND_DETAIL_URL_FROM_REVIEWED_PRIOR_SNAPSHOT"
        for row in carry
    )
    assert all(row["canonical_hotel_id"] != "H-0691" for row in carry)
