from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from swiss_os.hslca_pcf_bridge import (
    HSLCAProofBridgeError,
    bridge_file,
    enrich_capture_with_checkpoint_times,
)


def _sha(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _record(name: str, city: str, slug: str, page: int) -> dict[str, str]:
    return {
        "name": name,
        "city": city,
        "hs_id": "",
        "detail_url": f"https://www.hotelleriesuisse.ch/de/directory/hotel-{slug}",
        "source_url": f"https://www.hotelleriesuisse.ch/de/directory/hotel-page-{page}",
        "evidence_ref": f"CAPTURE-1:page:{page:04d}#record-001",
    }


def _page(position: int, record: dict[str, str]) -> dict[str, object]:
    records = [record]
    return {
        "page_id": f"CAPTURE-1:page:{position:04d}",
        "page_position": position,
        "source_url": "https://www.hotelleriesuisse.ch/de/directory" + ("" if position == 1 else f"/hotel-page-{position}"),
        "capture_id": "CAPTURE-1",
        "locale": "de",
        "surface": "member-directory",
        "observed_reported_records": None,
        "observed_expected_pages": 2,
        "html_sha256": "a" * 64,
        "records_sha256": _sha(records),
        "records": records,
    }


def _capture() -> dict[str, object]:
    return {
        "schema_version": "MEMBER_DIRECTORY_CAPTURE_V1",
        "capture_id": "CAPTURE-1",
        "provider": "HotellerieSuisse",
        "surface": "member-directory",
        "locale": "de",
        "capture_mode": "LIVE_PARTIAL",
        "coverage_claim": "PARTIAL",
        "started_at": "2026-08-28T10:00:00Z",
        "completed_at": "2026-08-28T10:10:00Z",
        "expected_pages": 2,
        "reported_records": 0,
        "pages": [
            _page(1, _record("Hotel Alpha", "Bern", "alpha", 1)),
            _page(2, _record("Hotel Beta", "Genève", "beta", 2)),
        ],
        "capture_violations": ["REPORTED_RECORDS_UNRESOLVED"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }


def _write_checkpoints(root: Path, payload: dict[str, object], timestamp: float) -> Path:
    pages_dir = root / "pages"
    pages_dir.mkdir()
    for page in payload["pages"]:  # type: ignore[index]
        position = page["page_position"]  # type: ignore[index]
        path = pages_dir / f"page-{position:04d}.json"
        path.write_text(json.dumps(page), encoding="utf-8")
        os.utime(path, (timestamp, timestamp))
    return pages_dir


class HSLCAProofBridgeTests(unittest.TestCase):
    def test_enriches_exact_checkpoint_mtimes_inside_capture_window(self) -> None:
        payload = _capture()
        with tempfile.TemporaryDirectory() as td:
            stamp = datetime(2026, 8, 28, 10, 5, tzinfo=timezone.utc).timestamp()
            pages_dir = _write_checkpoints(Path(td), payload, stamp)
            out = enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)
            self.assertEqual(len(out["pages"]), 2)
            self.assertTrue(out["pages"][0]["captured_at"].startswith("2026-08-28T10:05:00"))
            self.assertEqual(out["pages"][0]["captured_at_basis"], "ATOMIC_CHECKPOINT_FILE_MTIME")
            self.assertEqual(out["checkpoint_timestamp_provenance"]["pages_verified"], 2)
            self.assertFalse(out["authority_advanced"])
            self.assertEqual(out["h_id_allocations"], 0)
            self.assertFalse(out["outbound_opened"])
            self.assertEqual(out["send_allowed"], 0)

    def test_bridge_file_writes_enriched_capture(self) -> None:
        payload = _capture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stamp = datetime(2026, 8, 28, 10, 5, tzinfo=timezone.utc).timestamp()
            pages_dir = _write_checkpoints(root, payload, stamp)
            capture_path = root / "capture.json"
            capture_path.write_text(json.dumps(payload), encoding="utf-8")
            out_path = root / "capture-with-times.json"
            summary = bridge_file(capture_path, pages_dir=pages_dir, out_path=out_path)
            self.assertTrue(summary["valid"])
            self.assertEqual(summary["pages_verified"], 2)
            self.assertTrue(out_path.exists())

    def test_rejects_tampered_checkpoint(self) -> None:
        payload = _capture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stamp = datetime(2026, 8, 28, 10, 5, tzinfo=timezone.utc).timestamp()
            pages_dir = _write_checkpoints(root, payload, stamp)
            path = pages_dir / "page-0002.json"
            checkpoint = json.loads(path.read_text())
            checkpoint["records"][0]["city"] = "Tampered"
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            os.utime(path, (stamp, stamp))
            with self.assertRaisesRegex(HSLCAProofBridgeError, "does not equal"):
                enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)

    def test_rejects_stale_checkpoint_before_current_capture(self) -> None:
        payload = _capture()
        with tempfile.TemporaryDirectory() as td:
            stamp = datetime(2026, 8, 28, 9, 59, tzinfo=timezone.utc).timestamp()
            pages_dir = _write_checkpoints(Path(td), payload, stamp)
            with self.assertRaisesRegex(HSLCAProofBridgeError, "predates"):
                enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)

    def test_rejects_checkpoint_after_capture_window(self) -> None:
        payload = _capture()
        with tempfile.TemporaryDirectory() as td:
            stamp = datetime(2026, 8, 28, 10, 11, tzinfo=timezone.utc).timestamp()
            pages_dir = _write_checkpoints(Path(td), payload, stamp)
            with self.assertRaisesRegex(HSLCAProofBridgeError, "postdates"):
                enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)

    def test_rejects_missing_checkpoint(self) -> None:
        payload = _capture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stamp = datetime(2026, 8, 28, 10, 5, tzinfo=timezone.utc).timestamp()
            pages_dir = _write_checkpoints(root, payload, stamp)
            (pages_dir / "page-0002.json").unlink()
            with self.assertRaisesRegex(HSLCAProofBridgeError, "missing"):
                enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)

    def test_rejects_pre_authorized_capture(self) -> None:
        payload = _capture()
        payload["authority_advanced"] = True
        with tempfile.TemporaryDirectory() as td:
            stamp = datetime(2026, 8, 28, 10, 5, tzinfo=timezone.utc).timestamp()
            pages_dir = _write_checkpoints(Path(td), payload, stamp)
            with self.assertRaisesRegex(HSLCAProofBridgeError, "authority_advanced"):
                enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)

    def test_rejects_page_position_type_coercion(self) -> None:
        payload = _capture()
        payload["pages"][0]["page_position"] = "1"  # type: ignore[index]
        with tempfile.TemporaryDirectory() as td:
            pages_dir = Path(td) / "pages"
            pages_dir.mkdir()
            with self.assertRaisesRegex(HSLCAProofBridgeError, "positive integer"):
                enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)


if __name__ == "__main__":
    unittest.main()
