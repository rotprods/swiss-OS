import unittest

from swiss_os.directory_coverage import build_directory_coverage_plan


class DirectoryCoveragePlannerTests(unittest.TestCase):
    def test_missing_pages_generate_idempotent_tasks(self):
        observations = [
            {"locale": "de", "epoch": "E1", "page": 1},
            {"locale": "de", "epoch": "E1", "page": 3},
        ]
        result = build_directory_coverage_plan(observations, locale="de", epoch="E1", expected_pages=4)
        self.assertEqual(result["missing_pages"], [2, 4])
        self.assertEqual([t["task_key"] for t in result["tasks"]], [
            "DIRECTORY:E1:de:PAGE:2:MISSING",
            "DIRECTORY:E1:de:PAGE:4:MISSING",
        ])

    def test_conflict_has_higher_priority(self):
        observations = [{"locale": "de", "epoch": "E1", "page": 1}]
        result = build_directory_coverage_plan(observations, locale="de", epoch="E1", expected_pages=2, conflict_pages=[1])
        self.assertEqual(result["tasks"][0]["priority"], 950)
        self.assertEqual(result["tasks"][0]["page"], 1)

    def test_foreign_epoch_does_not_count_as_coverage(self):
        observations = [
            {"locale": "de", "epoch": "OLD", "page": 1},
            {"locale": "de", "epoch": "E1", "page": 2},
        ]
        result = build_directory_coverage_plan(observations, locale="de", epoch="E1", expected_pages=2)
        self.assertEqual(result["observed_pages"], 1)
        self.assertEqual(result["missing_pages"], [1])
        self.assertEqual(result["foreign_scope_observations"], 1)

    def test_complete_only_without_missing_or_conflicts(self):
        observations = [
            {"locale": "de", "epoch": "E1", "page": 1},
            {"locale": "de", "epoch": "E1", "page": 2},
        ]
        result = build_directory_coverage_plan(observations, locale="de", epoch="E1", expected_pages=2)
        self.assertTrue(result["complete"])
        self.assertEqual(result["coverage_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
