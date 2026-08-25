import unittest

from swiss_os.invariants import active_ids, duplicate_ids, numeric_id_gaps


class InvariantTests(unittest.TestCase):
    def test_duplicate_detection(self):
        self.assertEqual(duplicate_ids(["H-0001", "H-0002", "H-0001"]), {"H-0001"})

    def test_gap_detection_uses_physical_lineage(self):
        self.assertEqual(numeric_id_gaps(["H-0001", "H-0002", "H-0004"]), ["H-0003"])

    def test_superseded_rows_remain_physical_but_not_active(self):
        physical = {"H-0001", "H-0002", "H-0003"}
        self.assertEqual(active_ids(physical, {"H-0002"}), {"H-0001", "H-0003"})


if __name__ == "__main__":
    unittest.main()
