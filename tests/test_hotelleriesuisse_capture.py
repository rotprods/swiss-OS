from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.hotelleriesuisse_capture import (
    CaptureConfig,
    DirectoryCaptureError,
    capture_directory,
    extract_directory_records,
    extract_expected_pages,
    extract_reported_count,
)


PAGE_1 = """
<html><body>
<div class="result-count">3 Resultate</div>
<nav><a href="/de/x/hotel-page-2">2</a></nav>
<article class="hotel-card">
  <h3>Hotel Alpha</h3>
  <p>Teststrasse 1<br>3000 Bern</p>
  <a href="/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis/hotel-hotel-alpha">Hotel Alpha</a>
</article>
<article class="hotel-card">
  <h3>Hôtel Bêta</h3>
  <p>Rue Test 2<br>1200 Genève</p>
  <a href="/fr/association-et-siege-admin/membres/liste-des-membres/hotel-hotel-beta">Details</a>
</article>
</body></html>
"""

PAGE_2 = """
<html><body>
<div class="result-count">3 Resultate</div>
<nav><a href="/de/x/hotel-page-2">2</a></nav>
<li class="member-result item">
  <strong>Gasthaus Gamma</strong>
  <span>6000 Luzern</span>
  <a href="https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis/hotel-gasthaus-gamma">Mehr</a>
</li>
</body></html>
"""


class PageExtractionTests(unittest.TestCase):
    def test_extracts_name_city_and_unique_detail_url(self) -> None:
        records = extract_directory_records(
            PAGE_1,
            page_url="https://www.hotelleriesuisse.ch/de/directory",
            page_id="CAP:page:0001",
            page_position=1,
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["name"], "Hotel Alpha")
        self.assertEqual(records[0]["city"], "Bern")
        self.assertEqual(records[1]["name"], "Hôtel Bêta")
        self.assertEqual(records[1]["city"], "Genève")
        self.assertNotIn("hotel-page-", records[0]["detail_url"])

    def test_extracts_count_and_last_page(self) -> None:
        self.assertEqual(extract_reported_count(PAGE_1), 3)
        self.assertEqual(extract_expected_pages(PAGE_1), 2)

    def test_missing_city_fails_closed(self) -> None:
        bad = PAGE_2.replace("6000 Luzern", "unknown")
        with self.assertRaisesRegex(DirectoryCaptureError, "missing record city"):
            extract_directory_records(
                bad,
                page_url="https://example.test/page-2",
                page_id="CAP:page:0002",
                page_position=2,
            )


class CaptureTests(unittest.TestCase):
    def config(self, **overrides: object) -> CaptureConfig:
        values: dict[str, object] = {
            "capture_id": "CAPTURE-1",
            "locale": "de",
            "root_url": "https://www.hotelleriesuisse.ch/de/directory",
            "delay_seconds": 0.0,
            "resume": True,
        }
        values.update(overrides)
        return CaptureConfig(**values)  # type: ignore[arg-type]

    def test_complete_two_page_capture_emits_mdma_manifest(self) -> None:
        calls: list[str] = []

        def fetch(url: str) -> str:
            calls.append(url)
            return PAGE_1 if url.endswith("/directory") else PAGE_2

        with tempfile.TemporaryDirectory() as td:
            capture, manifest = capture_directory(
                self.config(),
                output_dir=td,
                fetcher=fetch,
                now=datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc),
            )
            self.assertEqual(len(calls), 2)
            self.assertEqual(capture["capture_mode"], "LIVE_COMPLETE")
            self.assertEqual(capture["capture_violations"], [])
            self.assertTrue(manifest["coverage_complete"])
            self.assertEqual(manifest["records_count"], 3)
            self.assertEqual(manifest["h_id_allocations"], 0)
            self.assertFalse(manifest["authority_advanced"])
            self.assertFalse(manifest["outbound_opened"])
            self.assertEqual(manifest["send_allowed"], 0)
            self.assertTrue((Path(td) / "capture.json").exists())
            self.assertTrue((Path(td) / "member-directory-manifest.json").exists())
            self.assertEqual(len(list((Path(td) / "pages").glob("*.json"))), 2)

    def test_resume_uses_page_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            calls: list[str] = []

            def fetch(url: str) -> str:
                calls.append(url)
                return PAGE_1 if url.endswith("/directory") else PAGE_2

            config = self.config()
            capture_directory(config, output_dir=td, fetcher=fetch)
            first_calls = len(calls)
            capture_directory(config, output_dir=td, fetcher=fetch)
            # Root is reread to reconstruct live count/page context; checkpointed
            # pages are not refetched after that bootstrap read.
            self.assertEqual(len(calls), first_calls + 1)

    def test_reported_count_drift_forces_partial_capture(self) -> None:
        page_2_drift = PAGE_2.replace("3 Resultate", "4 Resultate")

        def fetch(url: str) -> str:
            return PAGE_1 if url.endswith("/directory") else page_2_drift

        with tempfile.TemporaryDirectory() as td:
            capture, manifest = capture_directory(
                self.config(), output_dir=td, fetcher=fetch
            )
            self.assertEqual(capture["capture_mode"], "LIVE_PARTIAL")
            self.assertTrue(
                any(v.startswith("REPORTED_RECORD_DRIFT") for v in capture["capture_violations"])
            )
            self.assertFalse(manifest["coverage_complete"])

    def test_override_conflict_forces_partial_capture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            capture, manifest = capture_directory(
                self.config(expected_pages=3, reported_records=3),
                output_dir=td,
                fetcher=lambda url: PAGE_1 if url.endswith("/directory") else PAGE_2,
            )
            self.assertEqual(capture["capture_mode"], "LIVE_PARTIAL")
            self.assertTrue(
                any(v.startswith("EXPECTED_PAGE_OVERRIDE_CONFLICT") for v in capture["capture_violations"])
            )
            self.assertFalse(manifest["coverage_complete"])

    def test_checkpoint_tampering_is_not_reused(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            calls: list[str] = []

            def fetch(url: str) -> str:
                calls.append(url)
                return PAGE_1 if url.endswith("/directory") else PAGE_2

            config = self.config()
            capture_directory(config, output_dir=td, fetcher=fetch)
            checkpoint = Path(td) / "pages" / "page-0002.json"
            payload = json.loads(checkpoint.read_text())
            payload["records"][0]["city"] = "Tampered"
            checkpoint.write_text(json.dumps(payload), encoding="utf-8")
            before = len(calls)
            capture_directory(config, output_dir=td, fetcher=fetch)
            # root bootstrap + page 2 refetch because its record hash is invalid
            self.assertEqual(len(calls), before + 2)


if __name__ == "__main__":
    unittest.main()
