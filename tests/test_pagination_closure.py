from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.pagination_closure import (
    PaginationClosureError,
    prove_file,
    prove_pagination_closure,
)


def _sha(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _record(name: str, city: str, slug: str, page: int, index: int) -> dict[str, str]:
    return {
        "name": name,
        "city": city,
        "hs_id": "",
        "detail_url": (
            "https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/"
            f"mitgliederverzeichnis/hotel-{slug}"
        ),
        "source_url": (
            "https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/"
            "mitgliederverzeichnis"
        ),
        "evidence_ref": f"CAPTURE-1:page:{page:04d}#record-{index:03d}",
    }


def _page(position: int, records: list[dict[str, str]], observed_pages: int | None = 2) -> dict[str, object]:
    return {
        "page_id": f"CAPTURE-1:page:{position:04d}",
        "page_position": position,
        "source_url": (
            "https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/"
            "mitgliederverzeichnis"
            + ("" if position == 1 else f"/hotel-page-{position}")
        ),
        "capture_id": "CAPTURE-1",
        "locale": "de",
        "surface": "member-directory",
        "observed_reported_records": None,
        "observed_expected_pages": observed_pages,
        "html_sha256": "a" * 64,
        "records_sha256": _sha(records),
        "records": records,
    }


def _capture() -> dict[str, object]:
    page1_records = [
        _record("Hotel Alpha", "Bern", "hotel-alpha", 1, 1),
        _record("Hotel Beta", "Genève", "hotel-beta", 1, 2),
    ]
    page2_records = [_record("Hotel Gamma", "Luzern", "hotel-gamma", 2, 1)]
    return {
        "schema_version": "MEMBER_DIRECTORY_CAPTURE_V1",
        "capture_id": "CAPTURE-1",
        "provider": "HotellerieSuisse",
        "surface": "member-directory",
        "locale": "de",
        "capture_mode": "LIVE_PARTIAL",
        "coverage_claim": "PARTIAL",
        "started_at": "2026-08-28T10:00:00Z",
        "completed_at": "2026-08-28T10:05:00Z",
        "expected_pages": 2,
        "reported_records": 0,
        "pages": [_page(1, page1_records), _page(2, page2_records)],
        "capture_violations": ["REPORTED_RECORDS_UNRESOLVED"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }


class PaginationClosureTests(unittest.TestCase):
    def test_proves_complete_enumeration_without_displayed_count(self) -> None:
        capture, manifest, proof = prove_pagination_closure(
            _capture(), expected_page_size=2
        )
        self.assertEqual(capture["capture_mode"], "LIVE_COMPLETE_PAGINATION_CLOSURE")
        self.assertEqual(capture["reported_records"], 3)
        self.assertEqual(capture["capture_violations"], [])
        self.assertEqual(proof["method"], "ROOT_PAGINATION_CLOSURE")
        self.assertEqual(proof["terminal_page_count"], 1)
        self.assertEqual(proof["derived_raw_records"], 3)
        self.assertEqual(manifest["records_count"], 3)
        self.assertTrue(manifest["coverage_complete"])
        self.assertFalse(manifest["authority_advanced"])
        self.assertEqual(manifest["h_id_allocations"], 0)
        self.assertFalse(manifest["outbound_opened"])
        self.assertEqual(manifest["send_allowed"], 0)

    def test_file_roundtrip_writes_pre_authority_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            capture_path = Path(td) / "capture.json"
            capture_path.write_text(json.dumps(_capture()), encoding="utf-8")
            out = Path(td) / "proved"
            summary = prove_file(
                capture_path, out_dir=out, expected_page_size=2
            )
            self.assertTrue(summary["coverage_complete"])
            self.assertTrue((out / "capture-pagination-closed.json").exists())
            self.assertTrue((out / "member-directory-manifest.json").exists())
            self.assertTrue((out / "pagination-closure-proof.json").exists())
            self.assertTrue((out / "pagination-closure-summary.json").exists())

    def test_rejects_any_non_count_capture_violation(self) -> None:
        payload = _capture()
        payload["capture_violations"] = [
            "REPORTED_RECORDS_UNRESOLVED",
            "PAGE_COUNT_DRIFT:2,3",
        ]
        with self.assertRaisesRegex(PaginationClosureError, "non-count violations"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_missing_root_terminal_boundary_observation(self) -> None:
        payload = _capture()
        payload["pages"][0]["observed_expected_pages"] = None  # type: ignore[index]
        with self.assertRaisesRegex(PaginationClosureError, "root page"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_conflicting_pagination_observation(self) -> None:
        payload = _capture()
        payload["pages"][1]["observed_expected_pages"] = 3  # type: ignore[index]
        with self.assertRaisesRegex(PaginationClosureError, "disagree"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_sparse_non_terminal_page(self) -> None:
        payload = _capture()
        page = payload["pages"][0]  # type: ignore[index]
        page["records"] = page["records"][:1]  # type: ignore[index]
        page["records_sha256"] = _sha(page["records"])  # type: ignore[index]
        with self.assertRaisesRegex(PaginationClosureError, "non-terminal page 1"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_duplicate_detail_url_across_pages(self) -> None:
        payload = _capture()
        page1 = payload["pages"][0]  # type: ignore[index]
        page2 = payload["pages"][1]  # type: ignore[index]
        page2["records"][0]["detail_url"] = page1["records"][0]["detail_url"]  # type: ignore[index]
        page2["records_sha256"] = _sha(page2["records"])  # type: ignore[index]
        with self.assertRaisesRegex(PaginationClosureError, "duplicate detail_url"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_checkpoint_record_hash_tampering(self) -> None:
        payload = _capture()
        payload["pages"][1]["records"][0]["city"] = "Tampered"  # type: ignore[index]
        with self.assertRaisesRegex(PaginationClosureError, "records hash mismatch"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_pre_authorized_input(self) -> None:
        payload = _capture()
        payload["authority_advanced"] = True
        with self.assertRaisesRegex(PaginationClosureError, "authority_advanced"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_existing_reported_count_path(self) -> None:
        payload = _capture()
        payload["reported_records"] = 3
        payload["capture_violations"] = []
        with self.assertRaisesRegex(PaginationClosureError, "only for captures without"):
            prove_pagination_closure(payload, expected_page_size=2)

    def test_rejects_type_coercion_for_page_size(self) -> None:
        with self.assertRaisesRegex(PaginationClosureError, "positive integer"):
            prove_pagination_closure(_capture(), expected_page_size=True)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
