from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.cwp_lineage_guard import (
    CwpLineageError,
    _load_gzip_json,
    _load_multipart_candidate_export,
    parse_offset_spec,
    validate_candidate_export,
    validate_staged_lineage,
)


def sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def row(offset: int, key: str) -> dict[str, object]:
    return {
        "original_candidate_offset": offset,
        "source_record_key": key,
        "name": "hotel",
        "city": "city",
        "detail_url": "https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/mitgliederverzeichnis/hotel-test",
        "decision": "CANDIDATE_NEW_ENTITY_PREAUTH",
        "work_state": "VERIFY_NEW_ENTITY",
        "priority": 80,
        "reason": "NO_EXACT_CURRENT_CANONICAL_MATCH",
        "matched_hotel_id": "",
    }


def write_multipart(root: Path, payload: dict[str, object], chunk_size: int = 31) -> tuple[Path, bytes]:
    compressed = gzip.compress(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"), mtime=0)
    encoded = base64.b64encode(compressed)
    parts = []
    for index, start in enumerate(range(0, len(encoded), chunk_size)):
        data = encoded[start : start + chunk_size]
        relative = f"parts/part-{index:02d}.b64"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        parts.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {
        "schema_version": "CRM-CANDIDATE-EXPORT-MULTIPART-1.0",
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": "TEST",
        "encoding": "base64(gzip(json))",
        "gzip_mtime": 0,
        "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
        "records_sha256": sha(payload["records"]),
        "records_count": len(payload["records"]),
        "source_records": payload["source_records"],
        "exact_name_city_matches": payload["exact_name_city_matches"],
        "parts": parts,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, compressed


class CwpLineageGuardTests(unittest.TestCase):
    def test_parse_offset_spec(self):
        self.assertEqual(parse_offset_spec("3..5"), [3, 4, 5])
        self.assertEqual(parse_offset_spec([7, 9]), [7, 9])
        self.assertEqual(parse_offset_spec("12"), [12])

    def test_text_safe_base64_gzip_transport_is_transport_neutral(self):
        payload = {"schema_version": "T", "records": [{"id": 1}]}
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        compressed = gzip.compress(raw, mtime=0)
        with tempfile.TemporaryDirectory() as tmp:
            binary_path = Path(tmp) / "binary.json.gz"
            text_path = Path(tmp) / "text.json.gz"
            binary_path.write_bytes(compressed)
            text_path.write_bytes(base64.b64encode(compressed) + b"\n")
            binary_payload, binary_sha = _load_gzip_json(binary_path)
            text_payload, text_sha = _load_gzip_json(text_path)
        self.assertEqual(binary_payload, payload)
        self.assertEqual(text_payload, payload)
        self.assertEqual(binary_sha, hashlib.sha256(compressed).hexdigest())
        self.assertEqual(text_sha, binary_sha)

    def test_invalid_text_transport_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json.gz"
            path.write_text("not-gzip-and-not-base64%%%", encoding="utf-8")
            with self.assertRaises(CwpLineageError):
                _load_gzip_json(path)

    def test_multipart_transport_reconstructs_exact_gzip(self):
        payload = {"records": [{"id": 1}, {"id": 2}], "source_records": 2061, "exact_name_city_matches": 623}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path, compressed = write_multipart(root, payload)
            loaded, digest, manifest = _load_multipart_candidate_export(root, manifest_path)
        self.assertEqual(loaded, payload)
        self.assertEqual(digest, hashlib.sha256(compressed).hexdigest())
        self.assertEqual(manifest["records_sha256"], sha(payload["records"]))

    def test_multipart_part_corruption_fails_closed(self):
        payload = {"records": [{"id": 1}], "source_records": 2061, "exact_name_city_matches": 623}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path, _ = write_multipart(root, payload)
            first = root / "parts/part-00.b64"
            data = bytearray(first.read_bytes())
            data[0] = ord("A") if data[0] != ord("A") else ord("B")
            first.write_bytes(bytes(data))
            with self.assertRaisesRegex(CwpLineageError, "PART_SHA_MISMATCH"):
                _load_multipart_candidate_export(root, manifest_path)

    def test_multipart_reordered_manifest_fails_closed(self):
        payload = {"records": [{"id": 1}, {"id": 2}], "source_records": 2061, "exact_name_city_matches": 623}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path, _ = write_multipart(root, payload, chunk_size=17)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["parts"][0], manifest["parts"][1] = manifest["parts"][1], manifest["parts"][0]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(CwpLineageError):
                _load_multipart_candidate_export(root, manifest_path)

    def test_export_contract_detects_order_drift(self):
        records = [row(i, f"MD-{i:04d}") for i in range(1438)]
        payload = {
            "schema_version": "CRM-CANDIDATE-EXPORT-1.0",
            "records": records,
            "records_count": 1438,
            "candidate_new_entity_preauth": 1438,
            "candidate_order": "source_record_key ascending",
            "records_sha256": sha(records),
            "source_records": 2061,
            "exact_name_city_matches": 623,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
        self.assertEqual(validate_candidate_export(payload), [])
        payload["records"] = list(reversed(records))
        self.assertIn("CANDIDATE_OFFSETS_NOT_CONTIGUOUS", validate_candidate_export(payload))

    def test_skipped_original_offset_fails_closed(self):
        records = [row(i, f"MD-{i:04d}") for i in range(1438)]
        export = {
            "schema_version": "CRM-CANDIDATE-EXPORT-1.0",
            "records": records,
            "records_count": 1438,
            "candidate_new_entity_preauth": 1438,
            "candidate_order": "source_record_key ascending",
            "records_sha256": sha(records),
            "source_records": 2061,
            "exact_name_city_matches": 623,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
        items = [row(453, "MD-0453")]
        packet = {
            "batch_id": "B",
            "items": items,
            "items_count": 1,
            "items_sha256": sha(items),
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
        next_payload = {"ecv_frontier": {"next_staged_batch": "B", "next_staged_items": 1, "next_staged_items_sha256": sha(items), "next_staged_original_candidate_offsets": [454]}}
        errors = validate_staged_lineage(next_payload, export, packet)
        self.assertTrue(any(error.startswith("STAGED_ORIGINAL_CANDIDATE_OFFSETS_MISMATCH") for error in errors))


if __name__ == "__main__":
    unittest.main()
