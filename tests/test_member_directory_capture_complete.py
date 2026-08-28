from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from swiss_os.member_directory_capture import (
    CaptureConfig,
    FetchResponse,
    capture_member_directory,
)


ROOT = "https://example.test/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis"


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(seconds=1)
        return value


def card(index: int) -> str:
    return (
        f'<a href="{ROOT}/hotel-hotel-{index}">'
        f'<span>Hotel {index}</span><span>City {index}</span></a>'
    )


class CompleteCaptureGateTests(unittest.TestCase):
    def test_complete_capture_passes_all_gates(self) -> None:
        root_cards = "".join(card(index) for index in range(1, 1001))
        root_html = (
            f'<html><body><div>1001 Ergebnisse</div>'
            f'<a href="{ROOT}/hotel-page-2">2</a>{root_cards}</body></html>'
        ).encode()
        last_html = f"<html><body>{card(1001)}</body></html>".encode()

        def fetcher(url: str) -> FetchResponse:
            data = root_html if url == ROOT else last_html
            return FetchResponse(data, 200, url, {})

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = capture_member_directory(
                CaptureConfig(
                    root_url=ROOT,
                    locale="de",
                    delay_seconds=0,
                    expected_page_size=1000,
                ),
                tmpdir,
                fetcher=fetcher,
                robots_checker=lambda _: (
                    True,
                    "https://example.test/robots.txt",
                    "User-agent: *\nAllow: /",
                ),
                now=Clock(),
                sleeper=lambda _: None,
            )
            self.assertTrue(all(summary["coverage_checks"].values()))
            self.assertTrue(summary["coverage_complete_requested"])
            self.assertTrue(summary["mdm_coverage_complete"])
            self.assertEqual(summary["transfer_validation"], [])
            self.assertEqual(summary["unique_records"], 1001)
            self.assertFalse(summary["authority_advanced"])
            self.assertEqual(summary["h_id_allocations"], 0)
            self.assertEqual(summary["outbound"], "CLOSED")
            self.assertEqual(summary["send_allowed"], 0)
            self.assertTrue((Path(tmpdir) / "MEMBER_DIRECTORY_MANIFEST.json").is_file())


if __name__ == "__main__":
    unittest.main()
