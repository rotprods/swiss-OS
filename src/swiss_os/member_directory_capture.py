from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from typing import Callable, Iterable, Mapping, Sequence
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from .member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    build_member_directory_manifest,
    validate_member_directory_manifest,
)


class DirectoryCaptureError(RuntimeError):
    """Raised when a coherent member-directory capture cannot be completed."""


@dataclass(frozen=True)
class FetchResponse:
    data: bytes
    status: int
    final_url: str
    headers: Mapping[str, str]


@dataclass(frozen=True)
class CaptureConfig:
    root_url: str
    locale: str
    source_provider: str = "HOTELLERIESUISSE_MEMBER_DIRECTORY"
    user_agent: str = (
        "SWITZERLAND_JOB_OS/1.0 "
        "(+public directory integrity research; repository rotprods/swiss-OS)"
    )
    timeout_seconds: float = 45.0
    delay_seconds: float = 0.30
    attempts: int = 3
    max_pages: int = 250
    expected_page_size: int = 12
    retain_html: bool = False

    def validate(self) -> None:
        if not self.root_url.startswith(("https://", "http://")):
            raise DirectoryCaptureError("root_url must be absolute HTTP(S)")
        if not self.locale.strip():
            raise DirectoryCaptureError("locale must be non-empty")
        if not self.source_provider.strip():
            raise DirectoryCaptureError("source_provider must be non-empty")
        if not self.user_agent.strip():
            raise DirectoryCaptureError("user_agent must be non-empty")
        if self.timeout_seconds <= 0:
            raise DirectoryCaptureError("timeout_seconds must be positive")
        if self.delay_seconds < 0:
            raise DirectoryCaptureError("delay_seconds cannot be negative")
        if self.attempts <= 0:
            raise DirectoryCaptureError("attempts must be positive")
        if self.max_pages <= 0:
            raise DirectoryCaptureError("max_pages must be positive")
        if self.expected_page_size <= 0:
            raise DirectoryCaptureError("expected_page_size must be positive")


@dataclass(frozen=True)
class ParsedCard:
    name: str
    city: str
    detail_url: str


@dataclass(frozen=True)
class ParsedPage:
    cards: tuple[ParsedCard, ...]
    page_references: tuple[int, ...]
    count_candidates: tuple[int, ...]
    rejects: tuple[dict[str, object], ...]


class _DirectoryParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.page_references: set[int] = set()
        self.cards: list[ParsedCard] = []
        self.rejects: list[dict[str, object]] = []
        self.visible_text: list[str] = []
        self._active_href: str | None = None
        self._active_parts: list[str] = []
        self._seen_detail_urls: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key: value or "" for key, value in attrs}
        href = attributes.get("href", "")
        for match in re.findall(r"hotel-page-(\d+)", href):
            self.page_references.add(int(match))
        if tag.lower() != "a" or not href:
            return
        absolute = urljoin(self.base_url, href)
        path = urlsplit(absolute).path
        if "/mitgliederverzeichnis/hotel-" not in path:
            return
        if "hotel-page-" in path:
            return
        self._active_href = absolute
        self._active_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._active_href:
            return
        detail_url = self._active_href
        parts = [part for part in self._active_parts if part]
        self._active_href = None
        self._active_parts = []
        if detail_url in self._seen_detail_urls:
            return
        self._seen_detail_urls.add(detail_url)
        if len(parts) < 2:
            self.rejects.append(
                {
                    "detail_url": detail_url,
                    "reason_code": "CARD_TEXT_TOO_SHORT",
                    "parts": parts,
                }
            )
            return
        name = parts[0]
        city = parts[-1]
        if not name or not city or name == city:
            self.rejects.append(
                {
                    "detail_url": detail_url,
                    "reason_code": "INVALID_NAME_CITY",
                    "parts": parts,
                }
            )
            return
        self.cards.append(ParsedCard(name, city, detail_url))

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        self.visible_text.append(text)
        if self._active_href:
            self._active_parts.append(text)


def _count_candidates(text: str) -> tuple[int, ...]:
    result: list[int] = []
    patterns = (
        r"([0-9][0-9\s'’.,]{2,})\s+(?:Ergebnisse|Resultate|Treffer|résultats|results)",
        r"(?:Ergebnisse|Resultate|Treffer|résultats|results)\s*:?\s*([0-9][0-9\s'’.,]{2,})",
    )
    for pattern in patterns:
        for raw in re.findall(pattern, text, re.IGNORECASE):
            digits = re.sub(r"\D", "", raw)
            if not digits:
                continue
            value = int(digits)
            if 1000 <= value <= 5000 and value not in result:
                result.append(value)
    return tuple(result)


def parse_directory_page(html: bytes, base_url: str) -> ParsedPage:
    parser = _DirectoryParser(base_url)
    parser.feed(html.decode("utf-8", "replace"))
    return ParsedPage(
        cards=tuple(parser.cards),
        page_references=tuple(sorted(parser.page_references)),
        count_candidates=_count_candidates(" ".join(parser.visible_text)),
        rejects=tuple(parser.rejects),
    )


def _fetch_http(config: CaptureConfig, url: str) -> FetchResponse:
    errors: list[str] = []
    for attempt in range(1, config.attempts + 1):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": config.user_agent,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": f"{config.locale}-CH,{config.locale};q=0.9,en;q=0.5",
                    "Cache-Control": "no-cache",
                },
            )
            with urlopen(request, timeout=config.timeout_seconds) as response:
                return FetchResponse(
                    data=response.read(),
                    status=int(getattr(response, "status", 200)),
                    final_url=response.geturl(),
                    headers=dict(response.headers.items()),
                )
        except Exception as exc:  # pragma: no cover - exercised through fake fetchers
            errors.append(f"{type(exc).__name__}: {exc}")
            if attempt < config.attempts:
                time.sleep(float(attempt))
    raise DirectoryCaptureError(f"fetch failed for {url}: {'; '.join(errors)}")


def _robots_allowed(config: CaptureConfig) -> tuple[bool, str, str]:
    parts = urlsplit(config.root_url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        response = _fetch_http(config, robots_url)
        text = response.data.decode("utf-8", "replace")
        parser = RobotFileParser()
        parser.parse(text.splitlines())
        return parser.can_fetch(config.user_agent, config.root_url), robots_url, text
    except DirectoryCaptureError as exc:
        return False, robots_url, str(exc)


def _page_url(root_url: str, page: int) -> str:
    return root_url if page == 1 else f"{root_url.rstrip('/')}/hotel-page-{page}"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def capture_member_directory(
    config: CaptureConfig,
    output_dir: str | Path,
    *,
    fetcher: Callable[[str], FetchResponse] | None = None,
    robots_checker: Callable[[CaptureConfig], tuple[bool, str, str]] | None = None,
    now: Callable[[], datetime] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    config.validate()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    page_dir = target / "pages"
    if config.retain_html:
        page_dir.mkdir(parents=True, exist_ok=True)

    clock = now or (lambda: datetime.now(timezone.utc))
    started = clock()
    if started.tzinfo is None:
        raise DirectoryCaptureError("capture clock must return timezone-aware datetime")
    source_epoch = (
        f"HS-DIRECTORY-{config.locale.upper()}-"
        f"{started.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )

    check_robots = robots_checker or _robots_allowed
    robots_allowed, robots_url, robots_evidence = check_robots(config)
    (target / "robots.txt").write_text(robots_evidence, encoding="utf-8")
    if not robots_allowed:
        raise DirectoryCaptureError("robots policy does not allow directory capture")

    get = fetcher or (lambda url: _fetch_http(config, url))
    root_response = get(config.root_url)
    root_parsed = parse_directory_page(root_response.data, config.root_url)
    max_page = max(root_parsed.page_references) if root_parsed.page_references else 1
    if not 1 <= max_page <= config.max_pages:
        raise DirectoryCaptureError(f"implausible pagination max: {max_page}")

    page_results: list[dict[str, object]] = []
    all_records: list[DirectoryRecord] = []
    all_rejects: list[dict[str, object]] = []
    page_errors: list[dict[str, object]] = []

    def register(
        page: int,
        response: FetchResponse,
        parsed: ParsedPage,
        observed_at: str,
    ) -> None:
        page_sha = _sha256_bytes(response.data)
        if config.retain_html:
            (page_dir / f"page-{page:03d}.html.gz").write_bytes(
                gzip.compress(response.data)
            )
        page_results.append(
            {
                "page": page,
                "requested_url": _page_url(config.root_url, page),
                "final_url": response.final_url,
                "status": response.status,
                "observed_at": observed_at,
                "sha256": page_sha,
                "bytes": len(response.data),
                "records_count": len(parsed.cards),
                "rejects_count": len(parsed.rejects),
                "etag": response.headers.get("ETag")
                or response.headers.get("Etag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
        )
        for card in parsed.cards:
            record_id = (
                "directory:"
                + hashlib.sha256(card.detail_url.encode("utf-8")).hexdigest()[:24]
            )
            all_records.append(
                DirectoryRecord.from_mapping(
                    {
                        "record_id": record_id,
                        "name": card.name,
                        "city": card.city,
                        "evidence_ref": (
                            f"{source_epoch}:page:{page:03d}:sha256:{page_sha}"
                        ),
                        "hs_id": "",
                        "detail_url": card.detail_url,
                        "source_provider": config.source_provider,
                        "locale": config.locale.lower(),
                        "source_surface": config.root_url,
                        "source_epoch": source_epoch,
                        "partition_key": f"page:{page:03d}",
                        "observed_at": observed_at,
                        "evidence_scope": "CURRENT_DIRECTORY_RECORD",
                    }
                )
            )
        for reject in parsed.rejects:
            all_rejects.append({"page": page, **reject})

    register(1, root_response, root_parsed, clock().isoformat())
    for page in range(2, max_page + 1):
        url = _page_url(config.root_url, page)
        try:
            response = get(url)
            parsed = parse_directory_page(response.data, config.root_url)
            register(page, response, parsed, clock().isoformat())
        except Exception as exc:
            page_errors.append(
                {"page": page, "url": url, "error": f"{type(exc).__name__}: {exc}"}
            )
        if config.delay_seconds:
            sleeper(config.delay_seconds)

    finished = clock()
    by_detail: dict[str, DirectoryRecord] = {}
    duplicate_detail_urls: list[dict[str, object]] = []
    for record in all_records:
        previous = by_detail.get(record.detail_url)
        if previous:
            duplicate_detail_urls.append(
                {
                    "detail_url": record.detail_url,
                    "first_partition": previous.partition_key,
                    "duplicate_partition": record.partition_key,
                }
            )
        else:
            by_detail[record.detail_url] = record
    unique_records = tuple(by_detail.values())

    count_candidates = root_parsed.count_candidates
    displayed_count = count_candidates[0] if len(count_candidates) == 1 else None
    sum_page_records = sum(int(page["records_count"]) for page in page_results)
    empty_pages = [page["page"] for page in page_results if page["records_count"] == 0]
    non_last_page_size_mismatches = [
        page["page"]
        for page in page_results
        if page["page"] < max_page
        and page["records_count"] != config.expected_page_size
    ]
    last_page_count = next(
        (
            int(page["records_count"])
            for page in page_results
            if page["page"] == max_page
        ),
        None,
    )

    coverage_checks = {
        "robots_allowed": robots_allowed,
        "page_errors_zero": not page_errors,
        "observed_pages_equal_expected": len(page_results) == max_page,
        "empty_pages_zero": not empty_pages,
        "non_last_page_size_match": not non_last_page_size_mismatches,
        "last_page_count_valid": last_page_count is not None
        and 1 <= last_page_count <= config.expected_page_size,
        "duplicate_detail_urls_zero": not duplicate_detail_urls,
        "sum_page_records_equals_unique": sum_page_records == len(unique_records),
        "displayed_count_unambiguous": displayed_count is not None,
        "displayed_count_equals_unique": displayed_count == len(unique_records)
        if displayed_count is not None
        else False,
        "card_rejects_zero": not all_rejects,
    }
    coverage_complete_requested = all(coverage_checks.values())
    declared_raw_records = (
        displayed_count if displayed_count is not None else len(unique_records)
    )
    manifest_result = build_member_directory_manifest(
        unique_records,
        DirectoryManifestConfig(
            snapshot_id=source_epoch,
            observed_at=finished.isoformat(),
            source_provider=config.source_provider,
            locale=config.locale.lower(),
            source_url=config.root_url,
            source_epoch=source_epoch,
            expected_partitions=max_page,
            declared_raw_records=declared_raw_records,
            coverage_complete_requested=coverage_complete_requested,
        ),
    )

    page_manifest: dict[str, object] = {
        "schema_version": "HS-DIRECTORY-PAGES-1.0",
        "snapshot_id": source_epoch,
        "source_url": config.root_url,
        "locale": config.locale.lower(),
        "capture_started_at": started.isoformat(),
        "capture_finished_at": finished.isoformat(),
        "expected_pages": max_page,
        "observed_pages": len(page_results),
        "pages": page_results,
        "page_errors": page_errors,
        "empty_pages": empty_pages,
        "non_last_page_size_mismatches": non_last_page_size_mismatches,
        "last_page_count": last_page_count,
        "sum_page_records": sum_page_records,
        "unique_records": len(unique_records),
        "duplicate_detail_urls": duplicate_detail_urls,
        "card_rejects": all_rejects,
        "displayed_count_candidates": list(count_candidates),
        "coverage_checks": coverage_checks,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    page_manifest_path = target / "PAGE_MANIFEST.json"
    _write_json(page_manifest_path, page_manifest)

    manifest = dict(manifest_result.manifest)
    manifest.update(
        {
            "capture_started_at": started.isoformat(),
            "capture_finished_at": finished.isoformat(),
            "robots_url": robots_url,
            "robots_allowed": robots_allowed,
            "page_manifest_file": page_manifest_path.name,
            "page_manifest_sha256": hashlib.sha256(
                page_manifest_path.read_bytes()
            ).hexdigest(),
            "capture_checks": coverage_checks,
            "displayed_count_candidates": list(count_candidates),
            "page_errors": page_errors,
            "card_rejects": all_rejects,
            "duplicate_detail_urls": duplicate_detail_urls,
        }
    )
    manifest["manifest_sha256"] = _sha256_json(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )

    manifest_path = target / "MEMBER_DIRECTORY_MANIFEST.json"
    records_path = target / "MEMBER_DIRECTORY_RECORDS.json"
    _write_json(manifest_path, manifest)
    _write_json(records_path, [record.as_dict() for record in unique_records])
    transfer_violations = validate_member_directory_manifest(manifest)

    summary: dict[str, object] = {
        "schema_version": "HS-DIRECTORY-CAPTURE-SUMMARY-1.0",
        "snapshot_id": source_epoch,
        "max_page": max_page,
        "observed_pages": len(page_results),
        "displayed_count_candidates": list(count_candidates),
        "displayed_count": displayed_count,
        "sum_page_records": sum_page_records,
        "unique_records": len(unique_records),
        "page_errors": len(page_errors),
        "empty_pages": empty_pages,
        "non_last_page_size_mismatches": non_last_page_size_mismatches,
        "last_page_count": last_page_count,
        "duplicate_detail_urls": len(duplicate_detail_urls),
        "card_rejects": len(all_rejects),
        "coverage_checks": coverage_checks,
        "coverage_complete_requested": coverage_complete_requested,
        "mdm_coverage_complete": manifest_result.coverage_complete,
        "mdm_semantic_violations": list(manifest_result.violations),
        "transfer_validation": list(transfer_violations),
        "manifest_sha256": manifest["manifest_sha256"],
        "records_sha256": manifest["records_sha256"],
        "page_manifest_sha256": manifest["page_manifest_sha256"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    _write_json(target / "CAPTURE_SUMMARY.json", summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m swiss_os.member_directory_capture"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--root-url", required=True)
    capture.add_argument("--locale", required=True)
    capture.add_argument("--out-dir", required=True)
    capture.add_argument("--delay", type=float, default=0.30)
    capture.add_argument("--timeout", type=float, default=45.0)
    capture.add_argument("--attempts", type=int, default=3)
    capture.add_argument("--max-pages", type=int, default=250)
    capture.add_argument("--expected-page-size", type=int, default=12)
    capture.add_argument("--retain-html", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capture":
            summary = capture_member_directory(
                CaptureConfig(
                    root_url=args.root_url,
                    locale=args.locale,
                    delay_seconds=args.delay,
                    timeout_seconds=args.timeout,
                    attempts=args.attempts,
                    max_pages=args.max_pages,
                    expected_page_size=args.expected_page_size,
                    retain_html=args.retain_html,
                ),
                args.out_dir,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if summary["mdm_coverage_complete"] else 2
    except (DirectoryCaptureError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
