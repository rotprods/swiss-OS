import unittest

from swiss_os.reconcile import reconcile_ids


class ReconcileTests(unittest.TestCase):
    def test_exact_reconciliation_with_superseded_physical_row(self):
        report = reconcile_ids(
            ["H-0001", "H-0002", "H-0003"],
            ["H-0001", "H-0003"],
            ["H-0002"],
        )
        self.assertTrue(report.exact)
        self.assertEqual(report.physical_count, 3)
        self.assertEqual(report.active_count, 2)

    def test_missing_active_pk_fails_exactness(self):
        report = reconcile_ids(["H-0001", "H-0002"], ["H-0001"])
        self.assertFalse(report.exact)
        self.assertEqual(report.missing_in_db, ("H-0002",))


if __name__ == "__main__":
    unittest.main()
