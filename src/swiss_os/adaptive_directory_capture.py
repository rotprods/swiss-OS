from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import sys
import time
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    build_member_directory_manifest,
    validate_member_directory_manifest,
)
from .member_directory_capture import (
    CaptureConfig,
    DirectoryCaptureError,
    FetchResponse,
    capture_member_directory,
)


class AdaptiveCaptureError(DirectoryCaptureError):
    """Raised when the polite adaptive fetch path is exhausted."""


class AdaptiveFetcher:
    """HTTP fetcher that honors server throttling instead of hammering through 429s."""

    def __init__(
        self,
        config: CaptureConfig,
        *,
        opener: Callable[..., object] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] | None = None,
        attempts: int = 6,
        base_backoff_seconds: float = 15.0,
        max_backoff_seconds: float = 120.0,
    ) -> None:
        if attempts <= 0:
            raise AdaptiveCaptureError("adaptive attempts must be positive")
        if base_backoff_seconds <= 0 or max_backoff_seconds <= 0:
            raise AdaptiveCaptureError("adaptive backoff values must be positive")
        if max_backoff_seconds < base_backoff_seconds:
            raise AdaptiveCaptureError("max backoff cannot be below base backoff")
        self.config = config
        self.opener = opener
        self.sleeper = sleeper
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.attempts = attempts
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds

    def _request(self, url: str) -> Request:
        return Request(
            url,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": (
                    f"{self.config.locale}-CH,{self.config.locale};q=0.9,en;q=0.5"
                ),
                "Cache-Control": "no-cache",
            },
        )

    def _retry_after_seconds(self, headers: Mapping[str, str] | None) -> float | None:
        if not headers:
            return None
        raw = str(headers.get("Retry-After", "")).strip()
        if not raw:
            return None
        try:
            seconds = float(raw)
            return max(0.0, min(seconds, self.max_backoff_seconds))
        except ValueError:
            try:
                when = parsedate_to_datetime(raw)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                now = self.now()
                if now.tzinfo is None:
                    raise AdaptiveCaptureError("adaptive clock must be timezone-aware")
                return max(
                    0.0,
                    min((when - now).total_seconds(), self.max_backoff_seconds),
                )
            except (TypeError, ValueError, OverflowError):
                return None

    def _fallback_backoff(self, attempt: int) -> float:
        return min(
            self.max_backoff_seconds,
            self.base_backoff_seconds * (2 ** max(0, attempt - 1)),
        )

    def __call__(self, url: str) -> FetchResponse:
        errors: list[str] = []
        for attempt in range(1, self.attempts + 1):
            try:
                with self.opener(
                    self._request(url), timeout=self.config.timeout_seconds
                ) as response:
                    return FetchResponse(
                        data=response.read(),
                        status=int(getattr(response, "status", 200)),
                        final_url=response.geturl(),
                        headers=dict(response.headers.items()),
                    )
            except HTTPError as exc:
                errors.append(f"HTTPError:{exc.code}:{exc.reason}")
                retryable = exc.code == 429 or 500 <= exc.code <= 599
                if not retryable or attempt >= self.attempts:
                    break
                headers = dict(exc.headers.items()) if exc.headers else {}
                wait = self._retry_after_seconds(headers)
                if wait is None:
                    wait = self._fallback_backoff(attempt)
                self.sleeper(wait)
            except (URLError, TimeoutError, OSError) as exc:
                errors.append(f"{type(exc).__name__}:{exc}")
                if attempt >= self.attempts:
                    break
                self.sleeper(self._fallback_backoff(attempt))
        raise AdaptiveCaptureError(
            f"adaptive fetch failed for {url}: {'; '.join(errors)}"
        )


def _write_json(path: Path, payload: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _promote_materialized_count_proof(output_dir: Path, summary: dict[str, object]) -> dict[str, object]:
    """Allow full page partition proof when the UI omits a displayed total.

    This never weakens page completeness: every other structural capture check must
    already pass, including exact observed pages, page-size geometry, no page errors,
    no duplicates, no card rejects, and unique-record parity.
    """
    checks = summary.get("coverage_checks")
    if not isinstance(checks, Mapping):
        return summary
    displayed = summary.get("displayed_count")
    if displayed is not None:
        return summary
    structural_keys = (
        "robots_allowed",
        "page_errors_zero",
        "observed_pages_equal_expected",
        "empty_pages_zero",
        "non_last_page_size_match",
        "last_page_count_valid",
        "duplicate_detail_urls_zero",
        "sum_page_records_equals_unique",
        "card_rejects_zero",
    )
    if not all(checks.get(key) is True for key in structural_keys):
        return summary

    manifest_path = output_dir / "MEMBER_DIRECTORY_MANIFEST.json"
    records_path = output_dir / "MEMBER_DIRECTORY_RECORDS.json"
    page_path = output_dir / "PAGE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_records = json.loads(records_path.read_text(encoding="utf-8"))
    page_manifest = json.loads(page_path.read_text(encoding="utf-8"))
    if not isinstance(raw_records, list) or not raw_records:
        return summary
    records = tuple(DirectoryRecord.from_mapping(item) for item in raw_records)
    expected_pages = page_manifest.get("expected_pages")
    if isinstance(expected_pages, bool) or not isinstance(expected_pages, int) or expected_pages <= 0:
        raise AdaptiveCaptureError("page manifest expected_pages must be a positive integer")

    rebuilt = build_member_directory_manifest(
        records,
        DirectoryManifestConfig(
            snapshot_id=str(manifest.get("snapshot_id", "")),
            observed_at=str(manifest.get("observed_at", "")),
            source_provider=str(manifest.get("source_provider", "")),
            locale=str(manifest.get("locale", "")),
            source_url=str(manifest.get("source_url", "")),
            source_epoch=str(manifest.get("source_epoch", "")),
            expected_partitions=expected_pages,
            declared_raw_records=len(records),
            coverage_complete_requested=True,
        ),
    )
    rebuilt_manifest = dict(rebuilt.manifest)
    preserved = {
        key: value
        for key, value in manifest.items()
        if key
        in {
            "capture_started_at",
            "capture_finished_at",
            "robots_url",
            "robots_allowed",
            "page_manifest_file",
            "page_manifest_sha256",
            "page_errors",
            "card_rejects",
            "duplicate_detail_urls",
        }
    }
    rebuilt_manifest.update(preserved)
    rebuilt_manifest["count_proof"] = "MATERIALIZED_COMPLETE_PARTITION_SUM"
    rebuilt_manifest["displayed_count_candidates"] = []
    import hashlib

    rebuilt_manifest["manifest_sha256"] = hashlib.sha256(
        json.dumps(
            {k: v for k, v in rebuilt_manifest.items() if k != "manifest_sha256"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    violations = validate_member_directory_manifest(rebuilt_manifest)
    _write_json(manifest_path, rebuilt_manifest)

    updated = dict(summary)
    updated_checks = dict(checks)
    updated_checks["displayed_count_unambiguous"] = False
    updated_checks["displayed_count_equals_unique"] = False
    updated_checks["materialized_complete_partition_count_proof"] = not violations
    updated["coverage_checks"] = updated_checks
    updated["count_proof"] = "MATERIALIZED_COMPLETE_PARTITION_SUM"
    updated["declared_raw_records"] = len(records)
    updated["coverage_complete_requested"] = not violations
    updated["mdm_coverage_complete"] = bool(rebuilt_manifest.get("coverage_complete")) and not violations
    updated["mdm_semantic_violations"] = list(rebuilt.violations)
    updated["transfer_validation"] = list(violations)
    updated["manifest_schema_version"] = rebuilt_manifest.get("schema_version")
    updated["manifest_sha256"] = rebuilt_manifest.get("manifest_sha256")
    _write_json(output_dir / "CAPTURE_SUMMARY.json", updated)
    return updated


def adaptive_capture(
    config: CaptureConfig,
    output_dir: str | Path,
    *,
    attempts: int = 6,
    base_backoff_seconds: float = 15.0,
    max_backoff_seconds: float = 120.0,
) -> dict[str, object]:
    fetcher = AdaptiveFetcher(
        config,
        attempts=attempts,
        base_backoff_seconds=base_backoff_seconds,
        max_backoff_seconds=max_backoff_seconds,
    )
    target = Path(output_dir)
    summary = capture_member_directory(config, target, fetcher=fetcher)
    return _promote_materialized_count_proof(target, summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m swiss_os.adaptive_directory_capture"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--root-url", required=True)
    capture.add_argument("--locale", required=True)
    capture.add_argument("--out-dir", required=True)
    capture.add_argument("--delay", type=float, default=6.0)
    capture.add_argument("--timeout", type=float, default=45.0)
    capture.add_argument("--attempts", type=int, default=6)
    capture.add_argument("--base-backoff", type=float, default=15.0)
    capture.add_argument("--max-backoff", type=float, default=120.0)
    capture.add_argument("--max-pages", type=int, default=250)
    capture.add_argument("--expected-page-size", type=int, default=12)
    capture.add_argument("--retain-html", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capture":
            config = CaptureConfig(
                root_url=args.root_url,
                locale=args.locale,
                delay_seconds=args.delay,
                timeout_seconds=args.timeout,
                attempts=3,
                max_pages=args.max_pages,
                expected_page_size=args.expected_page_size,
                retain_html=args.retain_html,
            )
            summary = adaptive_capture(
                config,
                args.out_dir,
                attempts=args.attempts,
                base_backoff_seconds=args.base_backoff,
                max_backoff_seconds=args.max_backoff,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if summary.get("mdm_coverage_complete") is True else 2
    except (DirectoryCaptureError, AdaptiveCaptureError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
