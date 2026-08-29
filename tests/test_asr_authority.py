import pytest

from swiss_os.asr_authority import (
    compile_authority_repair_expected,
    validate_authority_repair,
)
from swiss_os.asr_repair import (
    AliasRepairAction,
    AliasRepairPlan,
    plan_phantom_alias_quarantine,
)


def _fixture():
    catalog = [
        {"hotel_id": "H-0610", "canonical_name": "Hôtel Alpe Fleurie", "city": "Villars-sur-Ollon"},
        {"hotel_id": "H-0624", "canonical_name": "Hôtel Le Mont Paisible", "city": "Crans-Montana"},
        {"hotel_id": "H-0629", "canonical_name": "Stiftung Lilienberg Unternehmerforum", "city": "Ermatingen"},
        {"hotel_id": "H-0630", "canonical_name": "Strandhotel Iseltwald", "city": "Iseltwald"},
        {"hotel_id": "H-0656", "canonical_name": "Hotel Murtenhof & Krone", "city": "Murten"},
        {"hotel_id": "H-0639", "canonical_name": "Hotel Alpbach", "city": "Meiringen"},
        {"hotel_id": "H-0638", "canonical_name": "Jugendherberge Seelisberg", "city": "Seelisberg"},
        {"hotel_id": "H-0640", "canonical_name": "Hotel Central Luzern", "city": "Luzern"},
    ]
    aliases = [
        ["H-0610", "H-0656"],
        ["H-0624", "H-0639"],
        ["H-0629", "H-0638"],
        ["H-0630", "H-0640"],
    ]
    alias_rows = [
        {"alias_hotel_id": left, "canonical_hotel_id": right}
        for left, right in aliases
    ]
    resolutions = [
        {"candidate_name": "Hotel Murtenhof & Krone", "candidate_city": "Murten", "notes": "H-0610 superseded"},
        {"candidate_name": "Hotel Alpbach", "candidate_city": "Meiringen", "notes": "H-0624 superseded"},
        {"candidate_name": "Jugendherberge Seelisberg", "candidate_city": "Seelisberg", "notes": "H-0629 superseded"},
        {"candidate_name": "Hotel Central Luzern", "candidate_city": "Luzern", "notes": "H-0630 superseded"},
    ]
    plan = plan_phantom_alias_quarantine(catalog, alias_rows, resolutions)
    return compile_authority_repair_expected(
        parent_manifest="OPERATIONAL_DB_SHADOW_MANIFEST_V13",
        authority_epoch="HS_ENTITY_EPOCH_2026-08-25_E4",
        physical_ids=[row["hotel_id"] for row in catalog],
        current_alias_edges=aliases,
        plan=plan,
    )


def _valid_payload(expected):
    physical = sorted(expected.physical_ids)
    active = sorted(expected.active_ids)
    aliases = [list(edge) for edge in sorted(expected.alias_edges)]
    receipts = {
        "db": {"physical_ids": physical, "active_ids": active, "alias_edges": aliases},
        "hotels_master": {"physical_ids": physical, "active_ids": active, "alias_edges": aliases},
        "intelligence": {"active_ids": active},
        "operational_graph": {"active_hotel_ids": active, "alias_edges": aliases},
        "observability": {
            "metric_active_count": len(active),
            "checkpoint_active_count": len(active),
            "scheduler_denominator": len(active),
            "state_transition_emitted": True,
            "run_log_emitted": True,
            "issue_updated": True,
        },
    }
    capabilities = {
        "constrained_db_write": True,
        "native_hotels_master_write": True,
        "intelligence_write": True,
        "operational_graph_write": True,
        "observability_write": True,
    }
    qa = {
        "integrity_check": "ok",
        "foreign_key_violations": 0,
        "replay_unintended_mutations": 0,
        "restore_logical_differences": 0,
        "semantic_alias_violations": 0,
        "active_name_city_duplicates": 0,
        "invalid_alias_targets": 0,
    }
    governance = {
        "outbound": "CLOSED",
        "send_allowed": 0,
        "external_actions_performed": False,
    }
    return receipts, capabilities, qa, governance


def _validate(expected, receipts, capabilities, qa, governance, *, parent=None, epoch=None):
    return validate_authority_repair(
        expected,
        receipts,
        capabilities,
        qa,
        governance,
        live_parent_manifest=parent or expected.parent_manifest,
        live_authority_epoch=epoch or expected.authority_epoch,
    )


def test_compile_preserves_physical_ids_and_reactivates_phantom_alias_sides():
    expected = _fixture()
    assert len(expected.physical_ids) == 8
    assert expected.alias_edges == frozenset()
    assert expected.active_ids == expected.physical_ids
    assert len(expected.quarantined_edges) == 4
    assert expected.as_dict()["authority_advanced"] is False


def test_exact_receipts_are_eligible_but_validator_does_not_advance_authority():
    expected = _fixture()
    receipts, capabilities, qa, governance = _valid_payload(expected)
    result = _validate(expected, receipts, capabilities, qa, governance)
    assert result.promotion_eligible is True
    assert result.state == "COMPLETE_AUTHORITY_ELIGIBLE"
    assert result.as_dict()["authority_advanced"] is False
    assert result.as_dict()["send_allowed"] == 0


def test_missing_native_sheets_writer_blocks_promotion():
    expected = _fixture()
    receipts, capabilities, qa, governance = _valid_payload(expected)
    capabilities["native_hotels_master_write"] = False
    result = _validate(expected, receipts, capabilities, qa, governance)
    assert "CAPABILITY_UNAVAILABLE:native_hotels_master_write" in result.violations


def test_string_boolean_capability_fails_closed():
    expected = _fixture()
    receipts, capabilities, qa, governance = _valid_payload(expected)
    capabilities["operational_graph_write"] = "true"
    result = _validate(expected, receipts, capabilities, qa, governance)
    assert any("must be a JSON boolean" in item for item in result.violations)


def test_parent_and_epoch_drift_block_promotion():
    expected = _fixture()
    receipts, capabilities, qa, governance = _valid_payload(expected)
    result = _validate(
        expected, receipts, capabilities, qa, governance,
        parent="OTHER", epoch="OTHER",
    )
    assert set(result.violations) >= {"PARENT_MANIFEST_DRIFT", "AUTHORITY_EPOCH_DRIFT"}


@pytest.mark.parametrize(
    ("plane", "key", "value", "expected_code"),
    [
        ("db", "active_ids", ["H-0610"], "DB_ACTIVE_PK_MISMATCH"),
        ("hotels_master", "active_ids", ["H-0610"], "SHEETS_ACTIVE_PK_MISMATCH"),
        ("intelligence", "active_ids", ["H-0610"], "INTELLIGENCE_ACTIVE_PK_MISMATCH"),
        ("operational_graph", "active_hotel_ids", ["H-0610"], "GRAPH_ACTIVE_PK_MISMATCH"),
    ],
)
def test_any_plane_pk_drift_blocks_promotion(plane, key, value, expected_code):
    expected = _fixture()
    receipts, capabilities, qa, governance = _valid_payload(expected)
    receipts[plane][key] = value
    result = _validate(expected, receipts, capabilities, qa, governance)
    assert expected_code in result.violations


def test_observability_qa_and_governance_failures_block_promotion():
    expected = _fixture()
    receipts, capabilities, qa, governance = _valid_payload(expected)
    receipts["observability"]["checkpoint_active_count"] -= 1
    qa["restore_logical_differences"] = 1
    governance["outbound"] = "OPEN"
    result = _validate(expected, receipts, capabilities, qa, governance)
    assert "OBSERVABILITY_MISMATCH:checkpoint_active_count" in result.violations
    assert "QA_NONZERO:restore_logical_differences" in result.violations
    assert "OUTBOUND_NOT_CLOSED" in result.violations


def test_compile_rejects_absent_quarantine_edge():
    plan = AliasRepairPlan(
        state="CANARY_ELIGIBLE",
        actions=(AliasRepairAction(
            alias_hotel_id="H-0610",
            erroneous_target_id="H-0656",
            action="QUARANTINE_ALIAS_EDGE_REACTIVATE_PHYSICAL_ID",
            reason_code="PHANTOM_ALIAS_H_ID_ROW_DRIFT",
        ),),
        blocked_alias_ids=(),
    )
    with pytest.raises(ValueError, match="absent alias edges"):
        compile_authority_repair_expected(
            parent_manifest="OPERATIONAL_DB_SHADOW_MANIFEST_V13",
            authority_epoch="HS_ENTITY_EPOCH_2026-08-25_E4",
            physical_ids=["H-0610", "H-0656"],
            current_alias_edges=[],
            plan=plan,
        )
