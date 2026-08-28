from __future__ import annotations

import unittest

from swiss_os.meta_execution import (
    ExecutionMode,
    MetaCapabilities,
    MetaRoute,
    choose_meta_route,
)


class MetaExecutionTests(unittest.TestCase):
    def test_stale_ancestry_forces_recovery(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                authority_reconstructable=True,
                ancestry_current=False,
                github_read=True,
                drive_mount_read=True,
            )
        )
        self.assertEqual(decision.execution_mode, ExecutionMode.RECOVERY_RECONCILE)
        self.assertEqual(decision.route, MetaRoute.AUTHORITY_RECOVERY)
        self.assertFalse(decision.authority_advance_allowed)
        self.assertFalse(decision.canonical_id_allocation_allowed)
        self.assertFalse(decision.outbound_allowed)

    def test_only_authority_blocking_p0_forces_recovery(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                authority_blocking_p0=True,
                web_research=True,
                unresolved_source_records=10,
            )
        )
        self.assertEqual(decision.route, MetaRoute.AUTHORITY_RECOVERY)
        self.assertIn("OPEN_AUTHORITY_BLOCKING_P0", decision.hard_blocks)

    def test_structured_capture_wins_when_key_available(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                discover_swiss_subscription=True,
                discover_capture_valid=False,
                github_write=True,
                github_ci=True,
            )
        )
        self.assertEqual(decision.route, MetaRoute.STRUCTURED_SOURCE_CAPTURE)
        self.assertEqual(decision.execution_mode, ExecutionMode.DEGRADED_CANARY)

    def test_directory_manifest_is_no_key_fallback(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                discover_swiss_subscription=False,
                discover_capture_valid=False,
                member_directory_evidence=True,
                web_research=True,
            )
        )
        self.assertEqual(decision.route, MetaRoute.MEMBER_DIRECTORY_MANIFEST)
        self.assertEqual(decision.execution_mode, ExecutionMode.READ_ONLY_RESEARCH)
        self.assertIn("member_directory_evidence", decision.capabilities_used)
        self.assertFalse(decision.authority_advance_allowed)
        self.assertFalse(decision.canonical_id_allocation_allowed)
        self.assertFalse(decision.outbound_allowed)

    def test_directory_manifest_follows_valid_capture(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                discover_capture_valid=True,
                member_directory_manifest_complete=False,
                web_research=True,
            )
        )
        self.assertEqual(decision.route, MetaRoute.MEMBER_DIRECTORY_MANIFEST)
        self.assertEqual(decision.execution_mode, ExecutionMode.READ_ONLY_RESEARCH)

    def test_ssr_follows_complete_source_sets(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                discover_capture_valid=True,
                member_directory_manifest_complete=True,
                source_scope_reconciled=False,
            )
        )
        self.assertEqual(decision.route, MetaRoute.SOURCE_SCOPE_RECONCILIATION)

    def test_candidate_export_precedes_mass_ingest(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                source_scope_reconciled=True,
                frozen_candidate=True,
                ingest_records_ready=False,
            )
        )
        self.assertEqual(decision.route, MetaRoute.FROZEN_CANDIDATE_EXPORT)
        self.assertFalse(decision.canonical_id_allocation_allowed)

    def test_mass_stage_never_allocates_canonical_ids(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                source_scope_reconciled=True,
                frozen_candidate=True,
                ingest_records_ready=True,
                constrained_db_write=True,
            )
        )
        self.assertEqual(decision.route, MetaRoute.MASS_INGEST_STAGING)
        self.assertFalse(decision.authority_advance_allowed)
        self.assertFalse(decision.canonical_id_allocation_allowed)
        self.assertFalse(decision.outbound_allowed)

    def test_exact_current_refresh_precedes_terminal_mapping(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                member_directory_manifest_complete=True,
                source_scope_reconciled=True,
                reconcile_required=50,
                exact_current_refresh_backlog=20,
                web_research=True,
            )
        )
        self.assertEqual(decision.route, MetaRoute.EXACT_CURRENT_REFRESH)
        self.assertEqual(decision.execution_mode, ExecutionMode.READ_ONLY_RESEARCH)

    def test_terminal_mapping_runs_after_refresh_backlog_clears(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                member_directory_manifest_complete=True,
                source_scope_reconciled=True,
                reconcile_required=50,
                exact_current_refresh_backlog=0,
                web_research=False,
            )
        )
        self.assertEqual(decision.route, MetaRoute.TERMINAL_MAPPING)
        self.assertEqual(decision.execution_mode, ExecutionMode.DEGRADED_CANARY)

    def test_unresolved_records_route_to_exact_current_refresh(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                member_directory_manifest_complete=True,
                unresolved_source_records=50,
                web_research=True,
            )
        )
        self.assertEqual(decision.route, MetaRoute.EXACT_CURRENT_REFRESH)
        self.assertEqual(decision.execution_mode, ExecutionMode.READ_ONLY_RESEARCH)

    def test_drive_mount_is_safe_fallback_for_native_sheet_outage(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                member_directory_manifest_complete=True,
                drive_mount_read=True,
                native_sheets_read=False,
            )
        )
        self.assertEqual(decision.route, MetaRoute.DRIVE_MOUNT_REHYDRATION)
        self.assertEqual(decision.execution_mode, ExecutionMode.RECOVERY_RECONCILE)

    def test_authoritative_promotion_requires_all_write_planes(self) -> None:
        base = dict(
            constrained_db_write=True,
            native_sheets_write=True,
            operational_graph_write=True,
            intelligence_write=True,
            observability_write=True,
            promotion_ready=True,
        )
        decision = choose_meta_route(MetaCapabilities(**base))
        self.assertEqual(decision.route, MetaRoute.AUTHORITATIVE_PROMOTION)
        self.assertEqual(decision.execution_mode, ExecutionMode.AUTHORITATIVE_WRITE)
        self.assertTrue(decision.authority_advance_allowed)
        self.assertTrue(decision.canonical_id_allocation_allowed)
        self.assertFalse(decision.outbound_allowed)

        base["native_sheets_write"] = False
        degraded = choose_meta_route(MetaCapabilities(**base, github_write=True, github_ci=True))
        self.assertNotEqual(degraded.route, MetaRoute.AUTHORITATIVE_PROMOTION)
        self.assertFalse(degraded.authority_advance_allowed)

    def test_post_crm_returns_to_global_scheduler(self) -> None:
        decision = choose_meta_route(
            MetaCapabilities(
                crm_universe_complete=True,
                scheduler_task_available=True,
            )
        )
        self.assertEqual(decision.route, MetaRoute.NEXT_GOAL_SCHEDULER)
        self.assertFalse(decision.outbound_allowed)

    def test_unknown_capability_key_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MetaCapabilities.from_mapping({"not_a_capability": True})

    def test_string_false_is_not_truthy_capability(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON boolean"):
            MetaCapabilities.from_mapping({"native_sheets_write": "false"})

    def test_integer_fields_are_strict_and_non_negative(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            MetaCapabilities.from_mapping({"unresolved_source_records": "10"})
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            MetaCapabilities.from_mapping({"unresolved_source_records": -1})

    def test_no_safe_route_is_typed_p0(self) -> None:
        decision = choose_meta_route(MetaCapabilities(crm_universe_complete=True))
        self.assertEqual(decision.execution_mode, ExecutionMode.BLOCKED_P0)
        self.assertEqual(decision.route, MetaRoute.NO_SAFE_ROUTE)
        self.assertIn("NO_SAFE_PRODUCTIVE_ROUTE", decision.hard_blocks)


if __name__ == "__main__":
    unittest.main()
