from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.candidate_entity_partition import (
    build_candidate_entity_partition,
    build_public_summary,
    load_candidate_export,
    validate_candidate_entity_partition,
)


def record(key: str, name: str, city: str, detail_url: str) -> dict[str, str]:
    return {
        "provider_record_key": key,
        "raw_name": name,
        "raw_city": city,
        "detail_url": detail_url,
        "source_url": "https://example.test/directory",
    }


class CandidateEntityPartitionTests(unittest.TestCase):
    def test_unique_records_become_singletons(self) -> None:
        payload = build_candidate_entity_partition(
            "SNAP-1",
            [
                record("MD-001", "Hotel A", "Bern", "https://x.test/a"),
                record("MD-002", "Hotel B", "Basel", "https://x.test/b"),
            ],
        )
        self.assertEqual(payload["partition_state"], "EXACT_PARTITION")
        self.assertEqual(payload["summary"]["candidate_records"], 2)
        self.assertEqual(payload["summary"]["partition_clusters"], 2)
        self.assertEqual(payload["summary"]["singleton_clusters"], 2)
        self.assertEqual(payload["summary"]["review_conflict_groups"], 0)
        self.assertEqual(validate_candidate_entity_partition(payload), ())

    def test_exact_detail_url_creates_stable_cluster(self) -> None:
        payload = build_candidate_entity_partition(
            "SNAP-1",
            [
                record("MD-001", "Hotel A", "Bern", "https://x.test/a/"),
                record("MD-002", "Hotel A AG", "Bern", "HTTPS://X.TEST/a"),
            ],
        )
        self.assertEqual(payload["summary"]["partition_clusters"], 1)
        self.assertEqual(payload["summary"]["stable_detail_url_clusters"], 1)
        cluster = payload["clusters"][0]
        self.assertEqual(cluster["stable_identity_basis"], "EXACT_DETAIL_URL")
        self.assertEqual(cluster["member_source_record_keys"], ["MD-001", "MD-002"])
        self.assertEqual(cluster["leader_source_record_key"], "MD-001")
        self.assertEqual(validate_candidate_entity_partition(payload), ())

    def test_same_name_city_with_different_urls_requires_review(self) -> None:
        payload = build_candidate_entity_partition(
            "SNAP-1",
            [
                record("MD-001", "Hôtel Bellevue", "Bern", "https://x.test/a"),
                record("MD-002", "Hotel Bellevue", "Bern", "https://x.test/b"),
            ],
        )
        self.assertEqual(payload["partition_state"], "PARTITION_COMPLETE_REVIEW_REQUIRED")
        self.assertEqual(payload["summary"]["partition_clusters"], 2)
        self.assertEqual(payload["summary"]["name_city_collision_groups"], 1)
        self.assertEqual(payload["summary"]["review_required_records"], 2)
        self.assertEqual(
            payload["review_conflicts"][0]["required_action"],
            "EXPLICIT_ENTITY_REVIEW_NO_AUTOMERGE",
        )

    def test_missing_detail_url_is_review_not_auto_merge(self) -> None:
        payload = build_candidate_entity_partition(
            "SNAP-1", [record("MD-001", "Hotel A", "Bern", "")]
        )
        self.assertEqual(payload["partition_state"], "PARTITION_COMPLETE_REVIEW_REQUIRED")
        self.assertEqual(payload["summary"]["missing_detail_url_records"], 1)
        self.assertEqual(payload["review_conflicts"][0]["conflict_type"], "MISSING_DETAIL_URL")

    def test_duplicate_provider_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate source_record_key"):
            build_candidate_entity_partition(
                "SNAP-1",
                [
                    record("MD-001", "Hotel A", "Bern", "https://x.test/a"),
                    record("MD-001", "Hotel B", "Basel", "https://x.test/b"),
                ],
            )

    def test_disagreeing_source_key_fields_are_rejected(self) -> None:
        row = record("MD-001", "Hotel A", "Bern", "https://x.test/a")
        row["source_record_key"] = "MD-002"
        with self.assertRaisesRegex(
            ValueError, "provider_record_key and source_record_key disagree"
        ):
            build_candidate_entity_partition("SNAP-1", [row])

    def test_partition_is_deterministic_across_input_order(self) -> None:
        records = [
            record("MD-002", "Hotel A AG", "Bern", "https://x.test/a"),
            record("MD-001", "Hotel A", "Bern", "https://x.test/a"),
            record("MD-003", "Hotel B", "Basel", "https://x.test/b"),
        ]
        left = build_candidate_entity_partition("SNAP-1", records)
        right = build_candidate_entity_partition("SNAP-1", list(reversed(records)))
        self.assertEqual(left["partition_sha256"], right["partition_sha256"])
        self.assertEqual(left["clusters"], right["clusters"])
        self.assertEqual(left["review_conflicts"], right["review_conflicts"])

    def test_loader_validates_gzip_and_record_hashes(self) -> None:
        rows = [
            record("MD-001", "Hotel A", "Bern", "https://x.test/a"),
            record("MD-002", "Hotel B", "Basel", "https://x.test/b"),
        ]
        records_sha = hashlib.sha256(
            json.dumps(
                rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        raw = json.dumps(
            {
                "schema_version": "CRM-CANDIDATE-EXPORT-1.0",
                "snapshot_id": "SNAP-1",
                "records_count": 2,
                "records": rows,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        compressed = gzip.compress(raw, mtime=0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "records.json.gz"
            manifest = root / "manifest.json"
            archive.write_bytes(compressed)
            manifest.write_text(
                json.dumps({
                    "snapshot_id": "SNAP-1",
                    "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
                    "records_sha256": records_sha,
                    "records_count": 2,
                }),
                encoding="utf-8",
            )
            loaded = load_candidate_export(archive, manifest)
            self.assertEqual(len(loaded.records), 2)
            self.assertEqual(loaded.snapshot_id, "SNAP-1")
            manifest_payload = json.loads(manifest.read_text())
            manifest_payload["records_sha256"] = "0" * 64
            manifest.write_text(json.dumps(manifest_payload))
            with self.assertRaisesRegex(ValueError, "candidate records SHA mismatch"):
                load_candidate_export(archive, manifest)

    def test_loader_accepts_strict_base64_gzip_transport(self) -> None:
        rows = [record("MD-001", "Hotel A", "Bern", "https://x.test/a")]
        records_sha = hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        compressed = gzip.compress(
            json.dumps({"snapshot_id": "SNAP-1", "records_count": 1, "records": rows}, sort_keys=True, separators=(",", ":")).encode(),
            mtime=0,
        )
        import base64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "records.b64"
            manifest = root / "manifest.json"
            archive.write_bytes(base64.b64encode(compressed))
            manifest.write_text(json.dumps({
                "snapshot_id": "SNAP-1",
                "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
                "records_sha256": records_sha,
                "records_count": 1,
            }))
            self.assertEqual(len(load_candidate_export(archive, manifest).records), 1)

    def test_public_summary_preserves_hard_locks(self) -> None:
        partition = build_candidate_entity_partition(
            "SNAP-1", [record("MD-001", "Hotel A", "Bern", "https://x.test/a")]
        )
        summary = build_public_summary(partition)
        self.assertTrue(summary["validation_pass"])
        self.assertIs(summary["authority_advanced"], False)
        self.assertEqual(summary["h_id_allocations"], 0)
        self.assertEqual(summary["canonical_id_reservations"], 0)
        self.assertEqual(summary["outbound"], "CLOSED")
        self.assertEqual(summary["send_allowed"], 0)

    def test_validator_detects_assignment_tamper(self) -> None:
        partition = build_candidate_entity_partition(
            "SNAP-1", [record("MD-001", "Hotel A", "Bern", "https://x.test/a")]
        )
        partition["clusters"][0]["member_source_record_keys"].append("MD-001")
        violations = validate_candidate_entity_partition(partition)
        self.assertIn(
            "cluster " + partition["clusters"][0]["cluster_id"] + " repeats a member",
            violations,
        )
        self.assertIn("source record assigned to multiple clusters", violations)


if __name__ == "__main__":
    unittest.main()
