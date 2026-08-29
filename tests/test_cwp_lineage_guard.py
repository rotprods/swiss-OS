from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.cwp_lineage_guard import CwpLineageError, _load_gzip_json, parse_offset_spec, validate_candidate_export, validate_staged_lineage


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
