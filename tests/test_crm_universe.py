import unittest

from swiss_os.crm_universe import (
    CRMUniverseMetrics,
    validate_crm_universe_gate,
    validate_mapping_states,
)


def _complete_metrics(**overrides):
    values = dict(
        snapshot_id="HS-FROZEN-TEST",
        snapshot_state="FROZEN_VERIFIED",
        snapshot_raw_records=10,
        active_canonical_mappings=8,
        alias_to_canonical_mappings=1,
        excluded_with_reason_mappings=1,
        reconcile_required=0,
        unmapped_records=0,
        unresolved_duplicate_conflicts=0,
        invalid_alias_targets=0,
        constrained_active_canonical=8,
        sheets_active_canonical=8,
        graph_active_canonical=8,
        intelligence_active_canonical=8,
        db_sheets_exact=True,
        graph_exact=True,
        intelligence_exact=True,
        coverage_snapshot_ids=("HS-FROZEN-TEST",) * 4,
    )
    values.update(overrides)
    return CRMUniverseMetrics(**values)


class CRMUniverseGateTests(unittest.TestCase):
    def test_complete_snapshot_passes(self) -> None:
        result = validate_crm_universe_gate(_complete_metrics())
        self.assertTrue(result.complete)
        self.assertEqual(result.violations, ())
        self.assertEqual(result.coverage_pct, 1.0)
        self.assertEqual(result.terminal_mapped_records, 10)

    def test_reconcile_required_fails_closed(self) -> None:
        result = validate_crm_universe_gate(
            _complete_metrics(active_canonical_mappings=7, reconcile_required=1)
        )
        self.assertFalse(result.complete)
        self.assertIn("reconcile_required must be zero", result.violations)
        self.assertTrue(
            any("mapping accounting mismatch" in item for item in result.violations)
        )

    def test_cross_plane_denominator_drift_fails(self) -> None:
        result = validate_crm_universe_gate(
            _complete_metrics(graph_active_canonical=7)
        )
        self.assertFalse(result.complete)
        self.assertIn(
            "active canonical denominator differs across planes", result.violations
        )

    def test_snapshot_lineage_mismatch_fails(self) -> None:
        result = validate_crm_universe_gate(
            _complete_metrics(
                coverage_snapshot_ids=("HS-FROZEN-TEST", "OTHER-SNAPSHOT")
            )
        )
        self.assertFalse(result.complete)
        self.assertIn(
            "coverage metrics are not bound to one snapshot_id", result.violations
        )

    def test_raw_count_is_not_active_canonical_count(self) -> None:
        metrics = _complete_metrics()
        result = validate_crm_universe_gate(metrics)
        self.assertTrue(result.complete)
        self.assertEqual(metrics.snapshot_raw_records, 10)
        self.assertEqual(metrics.constrained_active_canonical, 8)
        self.assertNotEqual(
            metrics.snapshot_raw_records, metrics.constrained_active_canonical
        )

    def test_only_terminal_mapping_states_pass_final_state_validation(self) -> None:
        invalid = validate_mapping_states(
            [
                "ACTIVE_CANONICAL",
                "ALIAS_TO_CANONICAL",
                "EXCLUDED_WITH_REASON",
                "RECONCILE_REQUIRED",
            ]
        )
        self.assertEqual(invalid, ("RECONCILE_REQUIRED",))


if __name__ == "__main__":
    unittest.main()
