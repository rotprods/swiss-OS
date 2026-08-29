from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.candidate_entity_partition import (
    build_candidate_entity_partition,
    load_candidate_export,
    validate_candidate_entity_partition,
)


def canonical_json_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def candidate(key: str, name: str = "Hotel A", city: str = "Bern") -> dict[str, str]:
    return {
        "source_record_key": key,
        "name": name,
        "city": city,
        "detail_url": f"https://example.test/{key.lower()}",
        "source_url": "https://example.test/directory",
    }


class CandidateEntityPartitionMultipartTests(unittest.TestCase):
    def build_fixture(self, root: Path) -> tuple[Path, list[dict[str, str]]]:
        records = [candidate("MD-001"), candidate("MD-002", "Hotel B", "Basel")]
        payload = {
            "schema_version": "CRM-CANDIDATE-EXPORT-1.0",
            "snapshot_id": "SNAP-1",
            "records_count": len(records),
            "records": records,
        }
        compressed = gzip.compress(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            mtime=0,
        )
        encoded = base64.b64encode(compressed)
        state = root / "docs" / "state"
        parts_dir = state / "parts"
        parts_dir.mkdir(parents=True)
        cut = len(encoded) // 2
        parts = []
        for index, data in enumerate((encoded[:cut], encoded[cut:])):
            path = parts_dir / f"part-{index:02d}.b64"
            path.write_bytes(data)
            parts.append(
                {
                    "path": str(path.relative_to(root)),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        manifest = {
            "schema_version": "CRM-CANDIDATE-EXPORT-MULTIPART-1.0",
            "project": "SWITZERLAND_JOB_OS",
            "snapshot_id": "SNAP-1",
            "encoding": "base64(gzip(json))",
            "gzip_mtime": 0,
            "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
            "records_sha256": canonical_json_sha(records),
            "records_count": len(records),
            "source_records": 2,
            "exact_name_city_matches": 0,
            "parts": parts,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
        manifest_path = state / "candidate.manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, records

    def test_multipart_manifest_is_the_transport_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path, records = self.build_fixture(root)
            stale_direct = root / "stale.json.gz"
            stale_direct.write_bytes(gzip.compress(b"{}", mtime=0))
            loaded = load_candidate_export(stale_direct, manifest_path)
            self.assertEqual(loaded.snapshot_id, "SNAP-1")
            self.assertEqual(len(loaded.records), len(records))
            self.assertEqual(loaded.records_sha256, canonical_json_sha(records))

    def test_multipart_part_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path, _ = self.build_fixture(root)
            manifest = json.loads(manifest_path.read_text())
            part_path = root / manifest["parts"][0]["path"]
            part_path.write_bytes(part_path.read_bytes() + b"A")
            with self.assertRaisesRegex(
                ValueError, "multipart candidate export invalid"
            ):
                load_candidate_export(root / "unused", manifest_path)

    def test_manifest_pre_authority_locks_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path, _ = self.build_fixture(root)
            manifest = json.loads(manifest_path.read_text())
            manifest["h_id_allocations"] = False
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "allocates H-IDs"):
                load_candidate_export(root / "unused", manifest_path)

    def test_summary_tamper_is_detected_even_with_unchanged_partition_hash(self) -> None:
        partition = build_candidate_entity_partition(
            "SNAP-1", [candidate("MD-001")]
        )
        partition["summary"]["partition_clusters"] = 99
        self.assertIn(
            "summary partition_clusters mismatch",
            validate_candidate_entity_partition(partition),
        )

    def test_conflict_reference_tamper_is_detected(self) -> None:
        left = candidate("MD-001", "Hôtel Bellevue", "Bern")
        right = candidate("MD-002", "Hotel Bellevue", "Bern")
        partition = build_candidate_entity_partition("SNAP-1", [left, right])
        partition["review_conflicts"][0]["candidate_cluster_ids"] = ["CEP-foreign"]
        violations = validate_candidate_entity_partition(partition)
        self.assertTrue(
            any("references foreign cluster" in violation for violation in violations)
        )


if __name__ == "__main__":
    unittest.main()
