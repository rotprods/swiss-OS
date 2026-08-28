from __future__ import annotations

import unittest

from swiss_os.alias_cross_plane import validate_cross_plane_write_set


def valid_plan() -> dict[str, object]:
    alias = "H-0001"
    target = "H-0002"
    return {
        "schema_version": "ASR_CROSS_PLANE_WRITESET_V1",
        "observed_spreadsheet_revision": "488",
        "rollback_copy_id": "drive-copy-id",
        "execution_authorized": False,
        "resolution_rule": "Resolve every live row by stable PK/entity_key/edge_id immediately before mutation. Observed row numbers are diagnostics only.",
        "entities": [{"hotel_id": alias, "invalid_target": target, "hotel_name": "Hotel A", "city": "Bern"}],
        "planes": {
            "constrained_db": {
                "action": "REPLAY_ARR_1_0_FROM_EXACT_V13_PARENT",
                "expected_output_sha256_observation": "a" * 64,
                "active_denominator_after_replay": None,
                "denominator_state": "RECONCILE_REQUIRED_CROSS_PLANE",
            },
            "HOTELS_V2": {"mutations": [{"keys": [alias], "set": {"state": "CANONICAL_CURRENT_RECONCILED"}}]},
            "HOTEL_INTELLIGENCE_V1": {"mutations": [{"keys": [alias], "set": {"enrichment_level": "L1", "identity_state": "CANONICAL_INDEXED_RECONCILE_SEED"}}]},
            "GRAPH_NODES_V2": {"mutations": [{"keys": [f"HOTEL:{alias}", f"INTEL:{alias}"]}]},
            "GRAPH_EDGES_V2": {"mutations": [
                {"action": "REMOVE_INVALID_ALIAS_EDGE", "keys": [f"EDGE:ALIAS:{alias}:{target}"]},
                {"action": "RESTORE_EXISTING_EDGE_FIELDS", "keys": [f"EDGE:HOTEL_INTEL:{alias}"]},
            ]},
            "ENTITY_RESOLUTION": {"records": ["ER-1"], "action": "PRESERVE_RESEARCH_ANTI_JOIN_EVIDENCE"},
            "STATE_TRANSITIONS": {
                "preserve_original_transition_ids": ["TR-1"],
                "append_template": {"from_state": "SUPERSEDED_DUPLICATE", "to_state": "CANONICAL_CURRENT_RECONCILED", "reversible": True},
            },
            "observability_and_scheduler": {"required": [
                "active denominator", "Intelligence denominator", "Operational Graph denominator", "scheduler tasks", "engine metrics"
            ]},
        },
        "promotion_gates": [
            "ASR-1.0 = EXACT after repair",
            "DB↔HOTELS_V2 exact",
            "restore/replay/idempotency PASS",
            "production readiness gauntlet PASS",
        ],
        "authority_advance_allowed": False,
        "canonical_id_allocation_allowed": False,
        "crm_universe_complete": False,
        "outbound_allowed": False,
        "send_allowed": 0,
    }


class AliasCrossPlaneTests(unittest.TestCase):
    def test_complete_plan_is_exact(self) -> None:
        result = validate_cross_plane_write_set(valid_plan())
        self.assertTrue(result.valid, result.as_dict())
        self.assertEqual(result.entities, 1)
        self.assertFalse(result.as_dict()["authority_advanced"])
        self.assertEqual(result.as_dict()["h_id_allocations"], 0)
        self.assertFalse(result.as_dict()["outbound_opened"])

    def test_missing_plane_fails(self) -> None:
        plan = valid_plan()
        del plan["planes"]["GRAPH_EDGES_V2"]
        result = validate_cross_plane_write_set(plan)
        self.assertIn("PLANE_SET_MISMATCH", {x.code for x in result.violations})

    def test_entity_and_plane_key_drift_fails(self) -> None:
        plan = valid_plan()
        plan["planes"]["HOTELS_V2"]["mutations"][0]["keys"] = ["H-0003"]
        result = validate_cross_plane_write_set(plan)
        self.assertIn("HOTEL_SET_MISMATCH", {x.code for x in result.violations})

    def test_alias_edge_target_must_match_entity(self) -> None:
        plan = valid_plan()
        plan["planes"]["GRAPH_EDGES_V2"]["mutations"][0]["keys"] = ["EDGE:ALIAS:H-0001:H-0003"]
        result = validate_cross_plane_write_set(plan)
        self.assertIn("ALIAS_EDGE_SET_MISMATCH", {x.code for x in result.violations})

    def test_historical_intelligence_seed_is_required(self) -> None:
        plan = valid_plan()
        plan["planes"]["HOTEL_INTELLIGENCE_V1"]["mutations"][0]["set"]["enrichment_level"] = "L0"
        result = validate_cross_plane_write_set(plan)
        self.assertIn("HISTORICAL_INTELLIGENCE_STATE_REQUIRED", {x.code for x in result.violations})

    def test_denominator_cannot_be_inferred_pre_reconciliation(self) -> None:
        plan = valid_plan()
        plan["planes"]["constrained_db"]["active_denominator_after_replay"] = 1
        result = validate_cross_plane_write_set(plan)
        self.assertIn("DENOMINATOR_INFERENCE_FORBIDDEN", {x.code for x in result.violations})

    def test_row_offset_and_rollback_requirements_fail_closed(self) -> None:
        plan = valid_plan()
        plan["resolution_rule"] = "write row 611"
        plan["rollback_copy_id"] = ""
        result = validate_cross_plane_write_set(plan)
        codes = {x.code for x in result.violations}
        self.assertIn("PK_RESOLUTION_RULE_REQUIRED", codes)
        self.assertIn("ROLLBACK_COPY_REQUIRED", codes)

    def test_irreversible_permissions_are_rejected(self) -> None:
        plan = valid_plan()
        plan["execution_authorized"] = True
        plan["authority_advance_allowed"] = True
        plan["canonical_id_allocation_allowed"] = True
        plan["outbound_allowed"] = True
        plan["send_allowed"] = 1
        result = validate_cross_plane_write_set(plan)
        codes = {x.code for x in result.violations}
        self.assertIn("PREAUTHORIZATION_FORBIDDEN", codes)
        self.assertIn("NONZERO_IRREVERSIBLE_PERMISSION", codes)

    def test_non_object_raises(self) -> None:
        with self.assertRaises(ValueError):
            validate_cross_plane_write_set([])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
