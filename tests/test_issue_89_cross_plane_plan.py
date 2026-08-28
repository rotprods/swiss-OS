from __future__ import annotations

from pathlib import Path
import unittest

from swiss_os.alias_cross_plane import load_and_validate


class Issue89CrossPlanePlanTests(unittest.TestCase):
    def test_persisted_issue_89_write_set_is_exact_and_non_authorizing(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = load_and_validate(root / "docs/state/ISSUE_89_CROSS_PLANE_WRITESET.json")
        self.assertTrue(result.valid, result.as_dict())
        self.assertEqual(result.entities, 4)
        self.assertFalse(result.as_dict()["authority_advanced"])
        self.assertEqual(result.as_dict()["h_id_allocations"], 0)
        self.assertFalse(result.as_dict()["outbound_opened"])
        self.assertEqual(result.as_dict()["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
