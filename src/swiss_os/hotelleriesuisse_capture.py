"""Resumable live capture for the public HotellerieSuisse member directory.

The adapter captures one explicit locale/surface/epoch, extracts property records
from detail links, checkpoints every page, and emits an MDMA-1.0 capture plus
manifest. It does not bypass access controls, allocate H-IDs, or advance authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import gzip
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .directory_manifest import build_member_directory_manifest, write_json_atomic


CAPTURE_SCHEMA_VERSION = "MEMBER_DIRECTORY_CAPTURE_V1"
DEFAULT_USER_AGENT = (
    "SWITZERLAND_JOB_OS/1.0 (+public directory evidence capture; "
    "no authentication bypass)"
)


class DirectoryCaptureError(RuntimeError):
    """Raised when a page or capture cannot satisfy the declared contract."""


@dataclass
class HtmlNode:
    tag: str
    attrs: dict[str, str]
    parent: "HtmlNode | None" = None
    children: list["HtmlNode"] = field(default_factory=list)
    text_chunks: list[str] = field(default_factory=list)

    def attr(self, name: str) -> str:
        return self.attrs.get(name, "")

    def classes(self) -> str:
        return self.attrs.get("class", "")

    def text(self) -> str:
        chunks: list[str] = []

        def walk(node: HtmlNode) -> None:
            chunks.extend(node.text_chunks)
            for child in node.children:
                walk(child)

        walk(self)
        return "\n".join(
            line.strip()
            for chunk in chunks
            for line in chunk.splitlines()
            if line.strip()
        )

    def iter(self) -> Iterator["HtmlNode"]:
        yield self
        for child in self.children:
            yield from child.iter()

    def first(self, tags: set[str]) -> "HtmlNode | None":
        for node in self.iter():
            if node.tag in tags:
                return node
        return None


class _DomParser(HTMLParser):
    _VOID = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = HtmlNode("document", {})
        self.stack: list[HtmlNode] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = HtmlNode(
            tag=tag.lower(),
            attrs={key.lower(): value or "" for key, value in attrs},
            parent=self.stack[-1],
        )
        self.stack[-1].children.append(node)
        if node.tag not in self._VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag.lower() and tag.lower() not in self._VOID:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        target = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == target:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].text_chunks.append(data)


def parse_html(html: str) -> HtmlNode:
    parser = _DomParser()
    parser.feed(html)
    parser.close()
    return parser.root


def _canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _absolute_url(base_url: str, href: str) -> str:
    parsed = urlsplit(urljoin(base_url, href))
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise DirectoryCaptureError(f"invalid detail URL: {href}")
    path = re.sub(r"/+", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def _is_detail_href(href: str) -> bool:
    lowered = href.casefold()
    if "/hotel-page-" in lowered:
        return False
    return (
        "/mitgliederverzeichnis/hotel-" in lowered
        or "/liste-des-membres/hotel-" in lowered
    )


def _nearest_card(anchor: HtmlNode) -> HtmlNode:
    fallback = anchor.parent or anchor
    node = anchor.parent
    depth = 0
    while node is not None and depth < 9:
        if node.tag in {"article", "li"}:
            return node
        if re.search(
            r"(?:^|[\s_-])(card|result|teaser|member|hotel|item)(?:$|[\s_-])",
            node.classes(),
            re.IGNORECASE,
        ):
            return node
        fallback = node
        node = node.parent
        depth += 1
    return fallback


def _record_name(anchor: HtmlNode, card: HtmlNode) -> str:
    anchor_text = _text(anchor.text())
    if anchor_text and not re.search(
        r"\b(mehr|details?|weiter|website|webseite|fiche|voir|read more)\b",
        anchor_text,
        re.IGNORECASE,
    ):
        return anchor_text
    heading = card.first({"h1", "h2", "h3", "h4", "h5", "strong"})
    return _text(heading.text()) if heading else ""


def _record_city(card_text: str) -> str:
    # Swiss addresses normally expose a four-digit postal code. The non-greedy
    # line boundary prevents neighbouring card text from being absorbed.
    patterns = (
        r"\b(?:CH[-\s]?)?\d{4}\s+([^\n|,;]+)",
        r"\b(?:Ort|Lieu|Località)\s*[:：]\s*([^\n|,;]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, card_text, re.IGNORECASE)
        if match:
            return _text(match.group(1))
    return ""


def extract_directory_records(
    html: str,
    *,
    page_url: str,
    page_id: str,
    page_position: int,
) -> list[dict[str, Any]]:
    """Extract unique directory property records from one rendered page."""

    root = parse_html(html)
    records: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for node in root.iter():
        if node.tag != "a":
            continue
        href = node.attr("href")
        if not href or not _is_detail_href(href):
            continue
        detail_url = _absolute_url(page_url, href)
        if detail_url in seen_urls:
            continue
        seen_urls.add(detail_url)
        card = _nearest_card(node)
        card_text = card.text()
        name = _record_name(node, card)
        city = _record_city(card_text)
        if not name:
            raise DirectoryCaptureError(
                f"missing record name at page {page_position}: {detail_url}"
            )
        if not city:
            raise DirectoryCaptureError(
                f"missing record city at page {page_position}: {name}"
            )
        record_position = len(records) + 1
        records.append(
            {
                "name": name,
                "city": city,
                "hs_id": "",
                "detail_url": detail_url,
                "source_url": page_url,
                "evidence_ref": f"{page_id}#record-{record_position:03d}",
            }
        )

    if not records:
        raise DirectoryCaptureError(f"no directory records found at {page_url}")
    return records


_COUNT_PATTERNS = (
    r"\b([0-9]{1,4}(?:[.'’\s][0-9]{3})*)\s*(?:Resultate|Resultats|Résultats|Ergebnisse|Treffer)\b",
    r"\b(?:Resultate|Resultats|Résultats|Ergebnisse|Treffer)\s*[:：]?\s*([0-9]{1,4}(?:[.'’\s][0-9]{3})*)\b",
)


def extract_reported_count(html: str) -> int | None:
    text = parse_html(html).text()
    for pattern in _COUNT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            digits = re.sub(r"\D", "", match.group(1))
            return int(digits) if digits else None
    return None


def extract_expected_pages(html: str) -> int | None:
    values = [
        int(value)
        for value in re.findall(r"/hotel-page-([0-9]+)", html, re.IGNORECASE)
    ]
    return max(values, default=0) or None


def _decode_response(body: bytes, content_encoding: str, charset: str | None) -> str:
    if "gzip" in content_encoding.casefold():
        body = gzip.decompress(body)
    return body.decode(charset or "utf-8", errors="replace")


def fetch_html(
    url: str,
    *,
    timeout_seconds: float = 45.0,
    retries: int = 3,
    user_agent: str = DEFAULT_USER_AGENT,
) -> str:
    """Fetch one public page with bounded retries and no access-control bypass."""

    if retries < 1:
        raise ValueError("retries must be positive")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Encoding": "gzip",
                "Accept-Language": "de,fr;q=0.8,en;q=0.6",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                content_type = response.headers.get_content_charset()
                encoding = response.headers.get("Content-Encoding", "")
                return _decode_response(response.read(), encoding, content_type)
        except HTTPError as exc:
            last_error = exc
            if exc.code in {401, 403, 404}:
                break
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = float(retry_after) if retry_after and retry_after.isdigit() else attempt
            time.sleep(min(delay, 10.0))
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(min(float(attempt), 5.0))
    raise DirectoryCaptureError(f"failed to fetch {url}: {last_error}")


@dataclass(frozen=True)
class CaptureConfig:
    capture_id: str
    locale: str = "de"
    provider: str = "HotellerieSuisse"
    surface: str = "member-directory"
    root_url: str = (
        "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/"
        "mitglieder/mitgliederverzeichnis"
    )
    expected_pages: int | None = None
    reported_records: int | None = None
    delay_seconds: float = 0.5
    timeout_seconds: float = 45.0
    retries: int = 3
    resume: bool = True

    def validate(self) -> None:
        if not self.capture_id:
            raise ValueError("capture_id is required")
        if self.locale not in {"de", "fr", "it", "en"}:
            raise ValueError("locale must be de, fr, it or en")
        if self.expected_pages is not None and self.expected_pages < 1:
            raise ValueError("expected_pages must be positive")
        if self.reported_records is not None and self.reported_records < 1:
            raise ValueError("reported_records must be positive")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")

    def page_url(self, position: int) -> str:
        if position == 1:
            return self.root_url
        return f"{self.root_url.rstrip('/')}/hotel-page-{position}"


FetchFunction = Callable[[str], str]


def _page_checkpoint_path(output_dir: Path, position: int) -> Path:
    return output_dir / "pages" / f"page-{position:04d}.json"


def _load_checkpoint(
    path: Path,
    *,
    capture_id: str,
    locale: str,
    source_url: str,
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    if (
        payload.get("capture_id") != capture_id
        or payload.get("locale") != locale
        or payload.get("source_url") != source_url
    ):
        return None
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return None
    if payload.get("records_sha256") != _sha256(records):
        return None
    return payload


def capture_directory(
    config: CaptureConfig,
    *,
    output_dir: str | Path,
    fetcher: FetchFunction | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Capture all pages, checkpoint them, and emit an MDMA manifest."""

    config.validate()
    target = Path(output_dir)
    (target / "pages").mkdir(parents=True, exist_ok=True)
    fetch = fetcher or (
        lambda url: fetch_html(
            url,
            timeout_seconds=config.timeout_seconds,
            retries=config.retries,
        )
    )
    started = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    root_html = fetch(config.page_url(1))
    inferred_pages = extract_expected_pages(root_html)
    inferred_records = extract_reported_count(root_html)
    expected_pages = config.expected_pages or inferred_pages
    reported_records = config.reported_records or inferred_records
    capture_violations: list[str] = []

    if expected_pages is None:
        capture_violations.append("EXPECTED_PAGES_UNRESOLVED")
        expected_pages = 1
    if reported_records is None:
        capture_violations.append("REPORTED_RECORDS_UNRESOLVED")
        reported_records = 0

    pages: list[dict[str, Any]] = []
    count_observations: set[int] = set()
    page_count_observations: set[int] = set()

    for position in range(1, expected_pages + 1):
        source_url = config.page_url(position)
        checkpoint_path = _page_checkpoint_path(target, position)
        checkpoint = (
            _load_checkpoint(
                checkpoint_path,
                capture_id=config.capture_id,
                locale=config.locale,
                source_url=source_url,
            )
            if config.resume
            else None
        )
        if checkpoint is not None:
            pages.append(checkpoint)
            continue

        html = root_html if position == 1 else fetch(source_url)
        observed_count = extract_reported_count(html)
        observed_pages = extract_expected_pages(html)
        if observed_count is not None:
            count_observations.add(observed_count)
        if observed_pages is not None:
            page_count_observations.add(observed_pages)
        page_id = f"{config.capture_id}:page:{position:04d}"
        records = extract_directory_records(
            html,
            page_url=source_url,
            page_id=page_id,
            page_position=position,
        )
        page_payload = {
            "page_id": page_id,
            "page_position": position,
            "source_url": source_url,
            "capture_id": config.capture_id,
            "locale": config.locale,
            "surface": config.surface,
            "observed_reported_records": observed_count,
            "observed_expected_pages": observed_pages,
            "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
            "records_sha256": _sha256(records),
            "records": records,
        }
        write_json_atomic(checkpoint_path, page_payload)
        pages.append(page_payload)
        if position < expected_pages and config.delay_seconds:
            time.sleep(config.delay_seconds)

    # Include resumed observations in coherence checks.
    for page in pages:
        if page.get("observed_reported_records") is not None:
            count_observations.add(int(page["observed_reported_records"]))
        if page.get("observed_expected_pages") is not None:
            page_count_observations.add(int(page["observed_expected_pages"]))

    if len(count_observations) > 1:
        capture_violations.append(
            "REPORTED_RECORD_DRIFT:" + ",".join(str(v) for v in sorted(count_observations))
        )
    if len(page_count_observations) > 1:
        capture_violations.append(
            "PAGE_COUNT_DRIFT:" + ",".join(str(v) for v in sorted(page_count_observations))
        )
    if page_count_observations and expected_pages not in page_count_observations:
        capture_violations.append(
            f"EXPECTED_PAGE_OVERRIDE_CONFLICT:{expected_pages}:"
            + ",".join(str(v) for v in sorted(page_count_observations))
        )
    if count_observations and reported_records not in count_observations:
        capture_violations.append(
            f"REPORTED_RECORD_OVERRIDE_CONFLICT:{reported_records}:"
            + ",".join(str(v) for v in sorted(count_observations))
        )

    completed = datetime.now(timezone.utc)
    complete = not capture_violations
    capture_payload: dict[str, Any] = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "capture_id": config.capture_id,
        "provider": config.provider,
        "surface": config.surface,
        "locale": config.locale,
        "capture_mode": "LIVE_COMPLETE" if complete else "LIVE_PARTIAL",
        "coverage_claim": "COMPLETE" if complete else "PARTIAL",
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "completed_at": completed.isoformat().replace("+00:00", "Z"),
        "expected_pages": expected_pages,
        "reported_records": reported_records,
        "pages": pages,
        "capture_violations": capture_violations,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    manifest = build_member_directory_manifest(capture_payload)
    write_json_atomic(target / "capture.json", capture_payload)
    write_json_atomic(target / "member-directory-manifest.json", manifest)
    return capture_payload, manifest
