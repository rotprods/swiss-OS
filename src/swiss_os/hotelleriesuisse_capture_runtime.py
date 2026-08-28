from __future__ import annotations

"""Polite runtime actuator for the resumable HSLCA capture engine.

The core HSLCA module owns parsing/checkpoints/coherence. This runtime owns network
policy: approved host boundary, robots preflight, adaptive throttling and a hard
stop on persistent rate limiting. A failed page aborts the activation so prior
checkpoints can be resumed later instead of hammering subsequent pages.
"""

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import gzip
import json
import re
import sys
import time
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
import urllib.robotparser

from .hotelleriesuisse_capture import (
    CaptureConfig,
    DEFAULT_USER_AGENT,
    DirectoryCaptureError,
    capture_directory,
)


class HSLCAAccessError(DirectoryCaptureError):
    """Typed source-access or rate-limit failure."""


APPROVED_HOST_SUFFIX = "hotelleriesuisse.ch"


def _approved_url(url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    return (
        parsed.scheme.lower() in {"http", "https"}
        and bool(host)
        and (host == APPROVED_HOST_SUFFIX or host.endswith("." + APPROVED_HOST_SUFFIX))
    )


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    if not _approved_url(url):
        raise HSLCAAccessError(f"unapproved HotellerieSuisse URL: {url}")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), "", "", ""))


def _decode_response(body: bytes, content_encoding: str, charset: str | None) -> str:
    if "gzip" in content_encoding.casefold():
        body = gzip.decompress(body)
    return body.decode(charset or "utf-8", errors="replace")


class RobotsPolicy:
    def __init__(
        self,
        *,
        opener: Callable[..., object] = urlopen,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.opener = opener
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    def _load(self, origin: str) -> urllib.robotparser.RobotFileParser:
        cached = self._cache.get(origin)
        if cached is not None:
            return cached
        robots_url = origin.rstrip("/") + "/robots.txt"
        request = Request(
            robots_url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/plain,*/*;q=0.1",
            },
        )
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                final_url = response.geturl()
                if not _approved_url(final_url):
                    raise HSLCAAccessError(
                        f"robots redirect left approved host boundary: {final_url}"
                    )
                text = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            # RFC-style conservative policy: a definite 404 means no robots file;
            # throttling/server failures are not permission to continue.
            if exc.code == 404:
                text = "User-agent: *\nAllow: /\n"
            else:
                raise HSLCAAccessError(
                    f"robots preflight failed HTTP {exc.code}: {robots_url}"
                ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise HSLCAAccessError(
                f"robots preflight unavailable: {robots_url}: {exc}"
            ) from exc
        parser.parse(text.splitlines())
        self._cache[origin] = parser
        return parser

    def assert_allowed(self, url: str) -> None:
        origin = _origin(url)
        parser = self._load(origin)
        if not parser.can_fetch(self.user_agent, url):
            raise HSLCAAccessError(f"robots policy disallows capture URL: {url}")


class AdaptiveHtmlFetcher:
    def __init__(
        self,
        *,
        opener: Callable[..., object] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] | None = None,
        robots: RobotsPolicy | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: float = 45.0,
        attempts: int = 6,
        base_backoff_seconds: float = 15.0,
        max_backoff_seconds: float = 120.0,
    ) -> None:
        if attempts <= 0:
            raise ValueError("attempts must be positive")
        if base_backoff_seconds <= 0 or max_backoff_seconds <= 0:
            raise ValueError("backoff values must be positive")
        if max_backoff_seconds < base_backoff_seconds:
            raise ValueError("max_backoff_seconds cannot be below base_backoff_seconds")
        self.opener = opener
        self.sleeper = sleeper
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.attempts = attempts
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.robots = robots or RobotsPolicy(
            opener=opener,
            user_agent=user_agent,
            timeout_seconds=min(timeout_seconds, 30.0),
        )

    def _request(self, url: str) -> Request:
        if not _approved_url(url):
            raise HSLCAAccessError(f"unapproved HotellerieSuisse URL: {url}")
        return Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Encoding": "gzip",
                "Accept-Language": "de,fr;q=0.8,it;q=0.6,en;q=0.5",
                "Cache-Control": "no-cache",
            },
        )

    def _retry_after(self, headers: Mapping[str, str] | None) -> float | None:
        if not headers:
            return None
        raw = str(headers.get("Retry-After", "") or "").strip()
        if not raw:
            return None
        try:
            return min(self.max_backoff_seconds, max(0.0, float(raw)))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(raw)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                now = self.clock()
                if now.tzinfo is None:
                    raise HSLCAAccessError("adaptive runtime clock must be timezone-aware")
                return min(
                    self.max_backoff_seconds,
                    max(0.0, (retry_at - now).total_seconds()),
                )
            except (TypeError, ValueError, OverflowError):
                return None

    def _backoff(self, attempt: int) -> float:
        return min(
            self.max_backoff_seconds,
            self.base_backoff_seconds * (2 ** max(0, attempt - 1)),
        )

    def __call__(self, url: str) -> str:
        self.robots.assert_allowed(url)
        errors: list[str] = []
        for attempt in range(1, self.attempts + 1):
            try:
                with self.opener(
                    self._request(url), timeout=self.timeout_seconds
                ) as response:
                    final_url = response.geturl()
                    if not _approved_url(final_url):
                        raise HSLCAAccessError(
                            f"capture redirect left approved host boundary: {final_url}"
                        )
                    # If a redirect changed host, enforce the destination robots
                    # policy before accepting the body. The first redirect request
                    # has already occurred, but no additional directory traversal
                    # is permitted until destination policy is checked.
                    if _origin(final_url) != _origin(url):
                        self.robots.assert_allowed(final_url)
                    charset = response.headers.get_content_charset()
                    encoding = response.headers.get("Content-Encoding", "")
                    return _decode_response(response.read(), encoding, charset)
            except HTTPError as exc:
                errors.append(f"HTTP_{exc.code}")
                retryable = exc.code == 429 or 500 <= exc.code <= 599
                if not retryable or attempt >= self.attempts:
                    break
                headers = dict(exc.headers.items()) if exc.headers else {}
                wait = self._retry_after(headers)
                self.sleeper(wait if wait is not None else self._backoff(attempt))
            except (URLError, TimeoutError, OSError) as exc:
                errors.append(type(exc).__name__)
                if attempt >= self.attempts:
                    break
                self.sleeper(self._backoff(attempt))
        raise HSLCAAccessError(
            f"adaptive capture fetch exhausted for {url}: {','.join(errors)}"
        )


def run_capture(
    *,
    capture_id: str,
    root_url: str,
    locale: str,
    output_dir: str,
    delay_seconds: float = 6.0,
    timeout_seconds: float = 45.0,
    attempts: int = 6,
    base_backoff_seconds: float = 15.0,
    max_backoff_seconds: float = 120.0,
) -> tuple[dict[str, object], dict[str, object]]:
    config = CaptureConfig(
        capture_id=capture_id,
        locale=locale,
        root_url=root_url,
        delay_seconds=delay_seconds,
        timeout_seconds=timeout_seconds,
        retries=1,
        resume=True,
    )
    fetcher = AdaptiveHtmlFetcher(
        timeout_seconds=timeout_seconds,
        attempts=attempts,
        base_backoff_seconds=base_backoff_seconds,
        max_backoff_seconds=max_backoff_seconds,
    )
    return capture_directory(config, output_dir=output_dir, fetcher=fetcher)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m swiss_os.hotelleriesuisse_capture_runtime"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--capture-id", required=True)
    capture.add_argument("--root-url", required=True)
    capture.add_argument("--locale", default="de")
    capture.add_argument("--out-dir", required=True)
    capture.add_argument("--delay", type=float, default=6.0)
    capture.add_argument("--timeout", type=float, default=45.0)
    capture.add_argument("--attempts", type=int, default=6)
    capture.add_argument("--base-backoff", type=float, default=15.0)
    capture.add_argument("--max-backoff", type=float, default=120.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        capture, manifest = run_capture(
            capture_id=args.capture_id,
            root_url=args.root_url,
            locale=args.locale,
            output_dir=args.out_dir,
            delay_seconds=args.delay,
            timeout_seconds=args.timeout,
            attempts=args.attempts,
            base_backoff_seconds=args.base_backoff,
            max_backoff_seconds=args.max_backoff,
        )
        summary = {
            "capture_id": capture.get("capture_id"),
            "capture_mode": capture.get("capture_mode"),
            "coverage_claim": capture.get("coverage_claim"),
            "capture_violations": capture.get("capture_violations"),
            "records_count": manifest.get("records_count"),
            "coverage_complete": manifest.get("coverage_complete"),
            "manifest_violations": manifest.get("violations"),
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if manifest.get("coverage_complete") is True else 2
    except (HSLCAAccessError, DirectoryCaptureError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": str(exc),
                    "authority_advanced": False,
                    "h_id_allocations": 0,
                    "outbound_opened": False,
                    "send_allowed": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
