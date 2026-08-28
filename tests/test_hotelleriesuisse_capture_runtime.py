from __future__ import annotations

from datetime import datetime, timezone
from email.message import Message
import unittest
from urllib.error import HTTPError

from swiss_os.hotelleriesuisse_capture_runtime import (
    AdaptiveHtmlFetcher,
    HSLCAAccessError,
    RobotsPolicy,
    _approved_url,
)


class _Response:
    def __init__(self, body=b"<html></html>", *, url="https://www.hotelleriesuisse.ch/x", headers=None):
        self._body = body
        self._url = url
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value
        self.status = 200

    def read(self):
        return self._body

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _AllowRobots:
    def __init__(self):
        self.urls = []

    def assert_allowed(self, url):
        self.urls.append(url)


class RuntimePolicyTests(unittest.TestCase):
    def test_host_boundary(self):
        self.assertTrue(_approved_url("https://www.hotelleriesuisse.ch/x"))
        self.assertTrue(_approved_url("https://my.hotelleriesuisse.ch/x"))
        self.assertFalse(_approved_url("https://hotelleriesuisse.ch.evil.test/x"))
        self.assertFalse(_approved_url("https://example.test/x"))

    def test_robots_disallow_fails_before_capture_fetch(self):
        robots_body = b"User-agent: *\nDisallow: /private\n"

        def opener(request, timeout=0):
            return _Response(robots_body, url="https://www.hotelleriesuisse.ch/robots.txt")

        policy = RobotsPolicy(opener=opener)
        with self.assertRaisesRegex(HSLCAAccessError, "robots policy disallows"):
            policy.assert_allowed("https://www.hotelleriesuisse.ch/private/page")

    def test_robots_404_is_treated_as_no_policy(self):
        def opener(request, timeout=0):
            raise HTTPError(request.full_url, 404, "Not Found", Message(), None)

        policy = RobotsPolicy(opener=opener)
        policy.assert_allowed("https://www.hotelleriesuisse.ch/public")

    def test_robots_429_fails_closed(self):
        def opener(request, timeout=0):
            raise HTTPError(request.full_url, 429, "Too Many Requests", Message(), None)

        policy = RobotsPolicy(opener=opener)
        with self.assertRaisesRegex(HSLCAAccessError, "robots preflight failed HTTP 429"):
            policy.assert_allowed("https://www.hotelleriesuisse.ch/public")

    def test_retry_after_and_backoff_then_success(self):
        robots = _AllowRobots()
        sleeps = []
        headers = Message()
        headers["Retry-After"] = "17"
        sequence = [
            HTTPError("https://www.hotelleriesuisse.ch/x", 429, "Too Many Requests", headers, None),
            _Response(b"ok"),
        ]

        def opener(request, timeout=0):
            value = sequence.pop(0)
            if isinstance(value, Exception):
                raise value
            return value

        fetcher = AdaptiveHtmlFetcher(
            opener=opener,
            sleeper=sleeps.append,
            robots=robots,
            attempts=3,
        )
        self.assertEqual(fetcher("https://www.hotelleriesuisse.ch/x"), "ok")
        self.assertEqual(sleeps, [17.0])
        self.assertEqual(robots.urls, ["https://www.hotelleriesuisse.ch/x"])

    def test_persistent_429_aborts_current_page_instead_of_continuing(self):
        robots = _AllowRobots()
        sleeps = []

        def opener(request, timeout=0):
            raise HTTPError(request.full_url, 429, "Too Many Requests", Message(), None)

        fetcher = AdaptiveHtmlFetcher(
            opener=opener,
            sleeper=sleeps.append,
            robots=robots,
            attempts=3,
            base_backoff_seconds=1,
            max_backoff_seconds=4,
        )
        with self.assertRaisesRegex(HSLCAAccessError, "HTTP_429"):
            fetcher("https://www.hotelleriesuisse.ch/x")
        self.assertEqual(sleeps, [1, 2])

    def test_nonretryable_404_does_not_sleep(self):
        robots = _AllowRobots()
        sleeps = []

        def opener(request, timeout=0):
            raise HTTPError(request.full_url, 404, "Not Found", Message(), None)

        fetcher = AdaptiveHtmlFetcher(
            opener=opener,
            sleeper=sleeps.append,
            robots=robots,
            attempts=6,
        )
        with self.assertRaisesRegex(HSLCAAccessError, "HTTP_404"):
            fetcher("https://www.hotelleriesuisse.ch/x")
        self.assertEqual(sleeps, [])

    def test_retry_after_http_date_uses_aware_clock(self):
        fetcher = AdaptiveHtmlFetcher(
            robots=_AllowRobots(),
            clock=lambda: datetime(2026, 8, 28, 16, 0, tzinfo=timezone.utc),
            max_backoff_seconds=120,
        )
        self.assertEqual(
            fetcher._retry_after({"Retry-After": "Fri, 28 Aug 2026 16:01:00 GMT"}),
            60,
        )

    def test_redirect_outside_provider_boundary_is_rejected(self):
        robots = _AllowRobots()

        def opener(request, timeout=0):
            return _Response(b"ok", url="https://evil.test/capture")

        fetcher = AdaptiveHtmlFetcher(opener=opener, robots=robots)
        with self.assertRaisesRegex(HSLCAAccessError, "redirect left approved host boundary"):
            fetcher("https://www.hotelleriesuisse.ch/x")


if __name__ == "__main__":
    unittest.main()
