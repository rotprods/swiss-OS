import json
import unittest
from pathlib import Path


class HslcaLiveCaptureRequestContractTests(unittest.TestCase):
    def test_request_is_exact_and_fail_closed(self):
        req = json.loads(
            Path("docs/state/source/HSLCA_LIVE_CAPTURE_REQUEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(req["schema_version"], "HSLCA-LIVE-CAPTURE-REQUEST-1.0")
        self.assertTrue(req["active"])
        self.assertEqual(req["route"], "R2_HSLCA_COHERENT_MEMBER_DIRECTORY_RECAPTURE")
        self.assertEqual(req["expected_before_sha"], "b0ec94f4a13fb7c24d39454439d9792d90bb7e46")
        self.assertEqual(req["authority_epoch"], "HS_ENTITY_EPOCH_2026-08-25_E4")
        self.assertEqual(
            req["authority_parent_materialized_sha256"],
            "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6",
        )
        self.assertEqual(req["source"]["provider"], "HotellerieSuisse")
        self.assertEqual(req["source"]["surface"], "member-directory")
        self.assertEqual(req["source"]["locale"], "de")
        self.assertTrue(req["capture"]["sequential"])
        self.assertEqual(req["capture"]["max_parallel"], 1)
        self.assertEqual(req["capture"]["delay_seconds"], 1.0)
        self.assertFalse(req["safety"]["authority_advance_allowed"])
        self.assertFalse(req["safety"]["canonical_id_allocation_allowed"])
        self.assertEqual(req["safety"]["canonical_id_reservations"], 0)
        self.assertFalse(req["safety"]["crm_universe_complete"])
        self.assertEqual(req["safety"]["outbound"], "CLOSED")
        self.assertEqual(req["safety"]["send_allowed"], 0)
        self.assertEqual(req["safety"]["irreversible_external_actions"], 0)

    def test_workflow_is_single_lane_main_scoped_and_fail_closed(self):
        workflow = Path(".github/workflows/hslca-pcf-live-canary.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("push:", workflow)
        self.assertIn("- main", workflow)
        self.assertIn("docs/state/source/HSLCA_LIVE_CAPTURE_REQUEST.json", workflow)
        self.assertIn("hslca-pcf-live-canary-main", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("EVENT_BEFORE", workflow)
        self.assertIn("expected_before_sha", workflow)
        self.assertIn("--delay 1", workflow)
        self.assertIn("assert capture['max_parallel'] == 1", workflow)
        self.assertIn("assert safety['authority_advance_allowed'] is False", workflow)
        self.assertIn("assert safety['canonical_id_allocation_allowed'] is False", workflow)
        self.assertIn("assert safety['outbound'] == 'CLOSED'", workflow)
        self.assertIn("assert safety['send_allowed'] == 0", workflow)
        self.assertIn("coverage_complete", workflow)
        self.assertNotIn("smtp", workflow.lower())
        self.assertNotIn("sendgrid", workflow.lower())
        self.assertNotIn("mailgun", workflow.lower())

    def test_blocker_cannot_be_misread_as_complete_snapshot(self):
        blocker = json.loads(
            Path("docs/state/source/HSLCA_R2_COHERENCE_BLOCKER_2026-08-30.json").read_text(encoding="utf-8")
        )
        source = blocker["source_evidence"]
        self.assertEqual(source["materialized_records"], 2061)
        self.assertFalse(source["coverage_complete"])
        self.assertEqual(source["capture_mode"], "LIVE_PARTIAL")
        self.assertIn("PAGE_COUNT_DRIFT:171,172", source["capture_violations"])
        self.assertEqual(blocker["ragr24_exact_partial_snapshot_scan"]["input_count"], 24)
        self.assertEqual(blocker["ragr24_exact_partial_snapshot_scan"]["exact_name_city_matches"], 0)
        self.assertFalse(blocker["safety"]["authority_advanced"])
        self.assertEqual(blocker["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(blocker["safety"]["outbound"], "CLOSED")
        self.assertEqual(blocker["safety"]["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
