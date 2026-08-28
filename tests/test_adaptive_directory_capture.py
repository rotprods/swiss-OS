from __future__ import annotations

from datetime import datetime, timezone
from email.message import Message
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from urllib.error import HTTPError

from swiss_os.adaptive_directory_capture import (
    AdaptiveCaptureError,
    AdaptiveFetcher,
    _promote_materialized_count_proof,
)
from swiss_os.member_directory_capture import CaptureConfig


class _Response:
    def __init__(self, data=b"ok", status=200, url="https://example.test/x", headers=None):
        self._data = data
        self.status = status
        self._url = url
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value

    def read(self):
        return self._data

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class AdaptiveFetcherTests(unittest.TestCase):
    def _config(self):
        return CaptureConfig(
            root_url="https://example.test/directory",
            locale="de",
            timeout_seconds=2,
        )

    def test_429_retry_after_is_honored(self):
        calls = []
        sleeps = []
        headers = Message()
        headers["Retry-After"] = "17"
        sequence = [
            HTTPError("https://example.test/x", 429, "Too Many Requests", headers, None),
            _Response(),
        ]

        def opener(*args, **kwargs):
            calls.append((args, kwargs))
            value = sequence.pop(0)
            if isinstance(value, Exception):
                raise value
            return value

        fetcher = AdaptiveFetcher(
            self._config(), opener=opener, sleeper=sleeps.append, attempts=3
        )
        response = fetcher("https://example.test/x")
        self.assertEqual(response.status, 200)
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [17.0])

    def test_429_without_header_uses_exponential_backoff(self):
        sleeps = []
        sequence = [
            HTTPError("https://example.test/x", 429, "Too Many Requests", Message(), None),
            HTTPError("https://example.test/x", 429, "Too Many Requests", Message(), None),
            _Response(),
        ]

        def opener(*args, **kwargs):
            value = sequence.pop(0)
            if isinstance(value, Exception):
                raise value
            return value

        fetcher = AdaptiveFetcher(
            self._config(),
            opener=opener,
            sleeper=sleeps.append,
            attempts=4,
            base_backoff_seconds=10,
            max_backoff_seconds=25,
        )
        fetcher("https://example.test/x")
        self.assertEqual(sleeps, [10, 20])

    def test_nonretryable_404_fails_immediately(self):
        sleeps = []

        def opener(*args, **kwargs):
            raise HTTPError(
                "https://example.test/x", 404, "Not Found", Message(), None
            )

        fetcher = AdaptiveFetcher(
            self._config(), opener=opener, sleeper=sleeps.append, attempts=6
        )
        with self.assertRaisesRegex(AdaptiveCaptureError, "HTTPError:404"):
            fetcher("https://example.test/x")
        self.assertEqual(sleeps, [])

    def test_retry_after_is_capped(self):
        headers = Message()
        headers["Retry-After"] = "9999"
        fetcher = AdaptiveFetcher(
            self._config(),
            max_backoff_seconds=120,
        )
        self.assertEqual(fetcher._retry_after_seconds(dict(headers.items())), 120)

    def test_http_date_retry_after_uses_timezone_aware_clock(self):
        fetcher = AdaptiveFetcher(
            self._config(),
            now=lambda: datetime(2026, 8, 28, 16, 0, 0, tzinfo=timezone.utc),
            max_backoff_seconds=120,
        )
        seconds = fetcher._retry_after_seconds(
            {"Retry-After": "Fri, 28 Aug 2026 16:01:00 GMT"}
        )
        self.assertEqual(seconds, 60)


class MaterializedCountProofTests(unittest.TestCase):
    def test_partial_capture_cannot_be_promoted(self):
        summary = {
            "displayed_count": None,
            "coverage_checks": {
                "robots_allowed": True,
                "page_errors_zero": False,
                "observed_pages_equal_expected": False,
                "empty_pages_zero": True,
                "non_last_page_size_match": True,
                "last_page_count_valid": False,
                "duplicate_detail_urls_zero": True,
                "sum_page_records_equals_unique": True,
                "card_rejects_zero": True,
            },
            "mdm_coverage_complete": False,
        }
        with TemporaryDirectory() as tmp:
            result = _promote_materialized_count_proof(Path(tmp), summary)
        self.assertIs(result, summary)
        self.assertFalse(result["mdm_coverage_complete"])

    def test_displayed_count_path_is_not_rewritten(self):
        summary = {
            "displayed_count": 24,
            "coverage_checks": {},
            "mdm_coverage_complete": True,
        }
        with TemporaryDirectory() as tmp:
            result = _promote_materialized_count_proof(Path(tmp), summary)
        self.assertIs(result, summary)


if __name__ == "__main__":
    unittest.main()
