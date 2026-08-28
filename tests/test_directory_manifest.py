from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.directory_manifest import (
    MANIFEST_SCHEMA_VERSION,
    build_member_directory_manifest,
    normalize_detail_url,
    normalize_source_url,
    validate_member_directory_manifest,
    write_json_atomic,
)
from swiss_os.directory_manifest_cli import main as cli_main


def capture() -> dict[str, object]:
    return {
        "schema_version": "MEMBER_DIRECTORY_CAPTURE_V1",
        "capture_id": "HS-DE-2026-08-28-COMPLETE",
        "provider": "HotellerieSuisse",
        "surface": "member-directory",
        "locale": "de",
        "capture_mode": "LIVE_COMPLETE",
        "coverage_claim": "COMPLETE",
        "started_at": "2026-08-28T10:00:00Z",
        "completed_at": "2026-08-28T10:05:00Z",
        "expected_pages": 2,
        "reported_records": 3,
        "pages": [
            {
                "page_id": "page-001",
                "page_position": 1,
                "source_url": "https://example.test/directory?page=1&filter=active",
                "capture_id": "HS-DE-2026-08-28-COMPLETE",
                "locale": "de",
                "surface": "member-directory",
                "records": [
                    {
                        "name": "Hotel Alpha",
                        "city": "Bern",
                        "hs_id": "HS-100",
                        "detail_url": "https://example.test/hotel/alpha/?utm_source=x",
                        "evidence_ref": "E-ALPHA",
                    },
                    {
                        "name": "Hôtel Bêta",
                        "city": "Genève",
                        "detail_url": "https://example.test/hotel/beta/#top",
                        "evidence_ref": "E-BETA",
                    },
                ],
            },
            {
                "page_id": "page-002",
                "page_position": 2,
                "source_url": "https://example.test/directory?filter=active&page=2",
                "capture_id": "HS-DE-2026-08-28-COMPLETE",
                "locale": "de",
                "surface": "member-directory",
                "records": [
                    {
                        "name": "Gasthaus Gamma",
                        "city": "Luzern",
                        "evidence_ref": "E-GAMMA",
                    }
                ],
            },
        ],
    }


class DirectoryManifestTests(unittest.TestCase):
    def test_complete_coherent_capture_is_freeze_eligible(self) -> None:
        manifest = build_member_directory_manifest(capture())
        self.assertEqual(manifest["schema_version"], MANIFEST_SCHEMA_VERSION)
        self.assertTrue(manifest["capture_valid"])
        self.assertTrue(manifest["coverage_complete"])
        self.assertEqual(manifest["records_count"], 3)
        self.assertEqual(manifest["violations"], [])
        self.assertFalse(manifest["authority_advanced"])
        self.assertEqual(manifest["h_id_allocations"], 0)
        self.assertFalse(manifest["outbound_opened"])
        self.assertEqual(manifest["send_allowed"], 0)
        self.assertTrue(validate_member_directory_manifest(manifest).valid)

    def test_historical_cache_cannot_claim_complete(self) -> None:
        payload = capture()
        payload["capture_mode"] = "HISTORICAL_CACHE"
        manifest = build_member_directory_manifest(payload)
        self.assertFalse(manifest["coverage_complete"])
        self.assertIn("COMPLETE_CLAIM_FORBIDDEN_FOR_MODE:HISTORICAL_CACHE", manifest["violations"])

    def test_partial_capture_never_freezes(self) -> None:
        payload = capture()
        payload["capture_mode"] = "LIVE_PARTIAL"
        payload["coverage_claim"] = "PARTIAL"
        payload["pages"] = payload["pages"][:1]  # type: ignore[index]
        manifest = build_member_directory_manifest(payload)
        self.assertTrue(manifest["capture_valid"])
        self.assertFalse(manifest["coverage_complete"])
        self.assertIn("PARTIAL_CAPTURE_CANNOT_FREEZE", manifest["warnings"])

    def test_mixed_locale_is_rejected(self) -> None:
        payload = capture()
        payload["pages"][1]["locale"] = "fr"  # type: ignore[index]
        manifest = build_member_directory_manifest(payload)
        self.assertFalse(manifest["capture_valid"])
        self.assertIn("PAGE_LOCALE_MISMATCH:page-002", manifest["violations"])

    def test_missing_page_position_blocks_complete_capture(self) -> None:
        payload = capture()
        payload["pages"] = payload["pages"][:1]  # type: ignore[index]
        manifest = build_member_directory_manifest(payload)
        self.assertFalse(manifest["coverage_complete"])
        self.assertTrue(any(v.startswith("PAGE_COUNT_MISMATCH") for v in manifest["violations"]))
        self.assertIn("PAGE_POSITION_COVERAGE_INCOMPLETE", manifest["violations"])

    def test_reported_record_mismatch_blocks_complete_capture(self) -> None:
        payload = capture()
        payload["reported_records"] = 4
        manifest = build_member_directory_manifest(payload)
        self.assertFalse(manifest["coverage_complete"])
        self.assertIn("RECORD_COUNT_MISMATCH:reported=4:materialized=3", manifest["violations"])

    def test_duplicate_source_identity_is_conflict(self) -> None:
        payload = capture()
        duplicate = copy.deepcopy(payload["pages"][0]["records"][0])  # type: ignore[index]
        payload["pages"][1]["records"].append(duplicate)  # type: ignore[index]
        payload["reported_records"] = 4
        manifest = build_member_directory_manifest(payload)
        self.assertFalse(manifest["capture_valid"])
        self.assertTrue(any(v.startswith("DUPLICATE_SOURCE_RECORD_KEY:hs:hs 100") for v in manifest["violations"]))

    def test_record_order_and_hash_are_deterministic(self) -> None:
        first = build_member_directory_manifest(capture())
        payload = capture()
        payload["pages"] = list(reversed(payload["pages"]))  # type: ignore[arg-type]
        second = build_member_directory_manifest(payload)
        self.assertEqual(first["records"], second["records"])
        self.assertEqual(first["records_sha256"], second["records_sha256"])
        self.assertEqual(first["snapshot_id"], second["snapshot_id"])

    def test_detail_url_normalization_drops_query_and_fragment(self) -> None:
        self.assertEqual(
            normalize_detail_url("HTTPS://Example.Test:443/a//b/?utm=x#frag"),
            "https://example.test/a/b",
        )

    def test_source_url_preserves_and_sorts_scope_query(self) -> None:
        self.assertEqual(
            normalize_source_url("HTTPS://Example.Test:443/d/?page=2&filter=active#frag"),
            "https://example.test/d?filter=active&page=2",
        )
        self.assertNotEqual(
            normalize_source_url("https://example.test/d?filter=active"),
            normalize_source_url("https://example.test/d?filter=inactive"),
        )

    def test_duplicate_page_source_url_is_rejected(self) -> None:
        payload = capture()
        payload["pages"][1]["source_url"] = payload["pages"][0]["source_url"]  # type: ignore[index]
        manifest = build_member_directory_manifest(payload)
        self.assertFalse(manifest["capture_valid"])
        self.assertTrue(any(v.startswith("DUPLICATE_PAGE_SOURCE_URL") for v in manifest["violations"]))

    def test_manifest_tampering_is_detected(self) -> None:
        manifest = build_member_directory_manifest(capture())
        manifest["records"][0]["city"] = "Basel"
        result = validate_member_directory_manifest(manifest)
        self.assertFalse(result.valid)
        self.assertIn("MANIFEST_RECORDS_SHA_MISMATCH", result.violations)
        self.assertIn("MANIFEST_SHA_MISMATCH", result.violations)

    def test_recovery_import_preserves_valid_manifest(self) -> None:
        manifest = build_member_directory_manifest(capture())
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "manifest.json"
            output = Path(td) / "recovered.json"
            write_json_atomic(source, manifest)
            self.assertEqual(cli_main(["recovery-import", str(source), "--out", str(output)]), 0)
            self.assertEqual(json.loads(source.read_text()), json.loads(output.read_text()))

    def test_cli_partial_build_writes_output_but_returns_blocked(self) -> None:
        payload = capture()
        payload["capture_mode"] = "HISTORICAL_CACHE"
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "capture.json"
            output = Path(td) / "manifest.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(cli_main(["build", str(source), "--out", str(output)]), 2)
            self.assertTrue(output.exists())
            self.assertFalse(json.loads(output.read_text())["coverage_complete"])


if __name__ == "__main__":
    unittest.main()
