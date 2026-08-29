from __future__ import annotations

import unittest
from pathlib import Path

from swiss_os.candidate_entity_partition import (
    CandidateEntityRecord,
    build_candidate_entity_partition,
    load_current_candidate_partition,
    validate_candidate_entity_partition,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


class CandidateEntityPartitionTests(unittest.TestCase):
    def test_exact_url_duplicates_cluster_without_allocating_ids(self) -> None:
        records = [
            CandidateEntityRecord("001:001:test", "Hotel A", "Bern", "https://x.test/a"),
            CandidateEntityRecord("001:002:test", "Hotel A Annex", "Bern", "https://x.test/a"),
            CandidateEntityRecord("001:003:test", "Hotel B", "Bern", "https://x.test/b"),
        ]
        partition = build_candidate_entity_partition(
            snapshot_id="SNAPSHOT",
            records=records,
            candidate_records_sha256=SHA_A,
            candidate_gzip_sha256=SHA_B,
        )
        summary = partition["summary"]
        self.assertEqual(summary["candidate_records"], 3)
        self.assertEqual(summary["partition_clusters"], 2)
        self.assertEqual(summary["stable_detail_url_clusters"], 1)
        self.assertEqual(summary["stable_detail_url_cluster_members"], 2)
        self.assertEqual(summary["exact_assignment_count"], 3)
        self.assertEqual(summary["assignment_duplicates"], 0)
        self.assertFalse(partition["authority_advanced"])
        self.assertEqual(partition["h_id_allocations"], 0)
        self.assertEqual(partition["canonical_id_reservations"], 0)
        self.assertEqual(partition["outbound"], "CLOSED")
        self.assertEqual(partition["send_allowed"], 0)
        self.assertEqual(validate_candidate_entity_partition(partition), ())

    def test_name_city_collision_is_review_only_not_automerged(self) -> None:
        records = [
            CandidateEntityRecord("001:001:test", "Hôtel Alpha", "Zürich", "https://x.test/a"),
            CandidateEntityRecord("001:002:test", "Hotel Alpha", "Zurich", "https://x.test/b"),
        ]
        partition = build_candidate_entity_partition(
            snapshot_id="SNAPSHOT",
            records=records,
            candidate_records_sha256=SHA_A,
            candidate_gzip_sha256=SHA_B,
        )
        summary = partition["summary"]
        self.assertEqual(summary["partition_clusters"], 2)
        self.assertEqual(summary["name_city_collision_groups"], 1)
        self.assertEqual(summary["review_required_records"], 2)
        self.assertEqual(partition["partition_state"], "PARTITION_COMPLETE_REVIEW_REQUIRED")

    def test_current_durable_candidate_transport_is_1438_exact_singletons(self) -> None:
        root = Path(__file__).resolve().parents[1]
        partition = load_current_candidate_partition(
            root,
            root / "docs/state/CRM_CANDIDATE_EXPORT_33206402141.manifest.json",
        )
        summary = partition["summary"]
        self.assertEqual(partition["snapshot_id"], "HS-MEMBER-DE-33206402141")
        self.assertEqual(
            partition["candidate_records_sha256"],
            "34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0",
        )
        self.assertEqual(
            partition["candidate_gzip_sha256"],
            "071e2cf1b895b63457c56066de7d8653b3182a12d1260ff9be7709a684fcf194",
        )
        self.assertEqual(summary["candidate_records"], 1438)
        self.assertEqual(summary["partition_clusters"], 1438)
        self.assertEqual(summary["singleton_clusters"], 1438)
        self.assertEqual(summary["stable_detail_url_clusters"], 0)
        self.assertEqual(summary["stable_detail_url_cluster_members"], 0)
        self.assertEqual(summary["review_conflict_groups"], 0)
        self.assertEqual(summary["name_city_collision_groups"], 0)
        self.assertEqual(summary["missing_detail_url_records"], 0)
        self.assertEqual(summary["exact_assignment_count"], 1438)
        self.assertEqual(summary["assignment_duplicates"], 0)
        self.assertEqual(summary["omitted_source_records"], 0)
        self.assertEqual(summary["foreign_source_records"], 0)
        self.assertEqual(summary["proposed_distinct_candidate_entities"], 1438)
        self.assertEqual(validate_candidate_entity_partition(partition), ())


if __name__ == "__main__":
    unittest.main()
