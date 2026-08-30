import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWEEP = ROOT / "docs/state/RAGR34_SOURCE_IDENTITY_SWEEP_2026-08-30.json"
WORKSET = ROOT / "docs/state/RAGR34_POST_REVIEW_DISPOSITION_WORKSET_2026-08-30.json"


class Ragr34SourceIdentitySweepTests(unittest.TestCase):
    def setUp(self):
        self.sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
        self.workset = json.loads(WORKSET.read_text(encoding="utf-8"))

    def test_scope_is_exactly_the_24_in_scope_reverse_gaps(self):
        expected = [
            row["hotel_id"]
            for row in self.workset["rows"]
            if row["classification"] == "IN_SCOPE_NO_SOURCE_MATCH"
        ]
        self.assertEqual(len(expected), 24)
        self.assertEqual(self.sweep["scope"]["count"], 24)
        self.assertEqual(self.sweep["scope"]["hotel_ids"], expected)
        self.assertEqual(
            self.sweep["results"]["no_exact_frozen_source_key_hotel_ids"], expected
        )

    def test_frozen_source_and_candidate_lineage_is_exact(self):
        inputs = self.sweep["inputs"]
        self.assertEqual(inputs["source_artifact_id"], 9700376482)
        self.assertEqual(
            inputs["source_artifact_zip_sha256"],
            "721f9ff9f84e2d5d9df62c6b22f12e7354cef3a298cb8990be66a202e1e769ce",
        )
        self.assertEqual(inputs["source_snapshot_id"], "HS-MEMBER-DE-33206402141")
        self.assertEqual(inputs["source_records"], 2061)
        self.assertEqual(
            inputs["source_records_sha256"],
            "62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2",
        )
        self.assertEqual(inputs["source_pages_observed"], 172)
        self.assertEqual(inputs["source_expected_pages"], 172)
        self.assertEqual(inputs["candidate_artifact_id"], 9718866661)
        self.assertEqual(inputs["candidate_records"], 1438)
        self.assertEqual(
            inputs["candidate_records_sha256"],
            "34d9aa9cfa4fe896bf1dbf2e135b847101904644d16bba0",
        )
        self.assertEqual(
            inputs["candidate_artifact_zip_sha256"],
            "d58c57c5a83cd2ff740f0ec900163f5c7aa795b032045cf9d30ffd194733465e",
        )
        self.assertEqual(
            inputs["ragr_disposition_rows_sha256"], self.workset["rows_sha256"]
        )

    def test_sweep_is_fail_closed_and_does_not_terminalize_similarity(self):
        results = self.sweep["results"]
        self.assertEqual(results["reviewed"], 24)
        self.assertEqual(results["exact_frozen_source_key_hits"], 0)
        self.assertEqual(results["exact_candidate_source_key_hits"], 0)
        self.assertEqual(results["exact_stored_hs_slug_hits"], 0)
        self.assertFalse(self.sweep["method"]["fuzzy_autobind"])
        self.assertEqual(
            results["disposition"], "SNAPSHOT_TERMINALIZATION_NOT_AVAILABLE_FOR_24"
        )
        self.assertEqual(
            self.sweep["mapping_effect"],
            {
                "reverse_authority_gaps_after": 34,
                "reverse_authority_gaps_before": 34,
                "terminal_mappings_after": 658,
                "terminal_mappings_before": 658,
            },
        )

    def test_same_name_collision_is_explicit_negative_evidence(self):
        collisions = self.sweep["results"]["same_name_other_city_collisions"]
        self.assertEqual(len(collisions), 1)
        collision = collisions[0]
        self.assertEqual(collision["hotel_id"], "H-0677")
        self.assertEqual(collision["canonical_city"], "Chur")
        self.assertEqual(collision["decision"], "NEGATIVE_IDENTITY_EVIDENCE_DO_NOT_BIND")
        self.assertEqual(
            {item["city"] for item in collision["frozen_source"]},
            {"Einsiedeln", "Luzern"},
        )
        self.assertNotIn("Chur", {item["city"] for item in collision["frozen_source"]})

    def test_authority_and_outbound_boundaries_remain_closed(self):
        authority = self.sweep["authority"]
        safety = self.sweep["safety"]
        self.assertEqual(authority["epoch"], "HS_ENTITY_EPOCH_2026-08-25_E4")
        self.assertEqual(
            authority["materialized_sha256"],
            "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6",
        )
        self.assertEqual(authority["physical_rows"], 690)
        self.assertEqual(authority["active_canonical"], 690)
        self.assertEqual(authority["next_physical_id"], "H-0691_UNALLOCATED")
        self.assertFalse(authority["advanced"])
        self.assertEqual(safety["terminal_source_mappings_created"], 0)
        self.assertEqual(safety["canonical_deactivations"], 0)
        self.assertEqual(safety["canonical_id_reservations"], 0)
        self.assertEqual(safety["h_id_allocations"], 0)
        self.assertEqual(safety["h_0691"], "UNALLOCATED")
        self.assertFalse(safety["crm_universe_complete"])
        self.assertEqual(safety["outbound"], "CLOSED")
        self.assertEqual(safety["send_allowed"], 0)
        self.assertEqual(safety["irreversible_external_actions"], 0)

    def test_next_route_is_review_only_authority_repair(self):
        nxt = self.sweep["next"]
        self.assertEqual(nxt["route"], "RAGR34_AUTHORITY_REPAIR_PROPOSALS_10_REVIEW_ONLY")
        self.assertTrue(nxt["verify_live_truth_before_execution"])
        self.assertIn("cannot be terminalized", nxt["exact_dependency"])
        self.assertIn("durable DB-first receipt", nxt["exact_dependency"])


if __name__ == "__main__":
    unittest.main()
