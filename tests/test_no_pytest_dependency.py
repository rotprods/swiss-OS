import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NoPytestDependencyTests(unittest.TestCase):
    def test_new_locality_tests_do_not_import_pytest(self):
        text = (ROOT / "tests/test_locality_normalization_guard.py").read_text(encoding="utf-8")
        self.assertNotIn("import pytest", text)
        self.assertIn("import unittest", text)


if __name__ == "__main__":
    unittest.main()
