from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
from typing import Callable, Mapping, Sequence
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


class ExactCurrentVerifyError(ValueError):
    """Raised when an exact-current verification packet is invalid."""


@dataclass(frozen=True)
class FetchResponse:
    data: bytes
    status: int
    final_url: str
    headers: Mapping[str, str]


@dataclass(frozen=True)
class VerifyConfig:
    user_agent: str = (
        "SWITZERLAND_JOB_OS/1.0 "
        "(+public official entity verification; repository rotprods/swiss-OS)"
    )
    timeout_seconds: float = 30.0
    delay_seconds: float = 0.25
    attempts: int = 3
    allowed_hosts: tuple[str, ...] = ("www.hotelleriesuisse.ch", "hotelleriesuisse.ch")

    def validate(self) -> None:
        if not self.user_agent.strip():
            raise ExactCurrentVerifyError("user_agent must be non-empty")
        if self.timeout_seconds <= 0:
            raise ExactCurrentVerifyError("timeout_seconds must be positive")
        if self.delay_seconds < 0:
            raise ExactCurrentVerifyError("delay_seconds cannot be negative")
        if self.attempts <= 0:
            raise ExactCurrentVerifyError("attempts must be positive")
        if not self.allowed_hosts:
            raise ExactCurrentVerifyError("allowed_hosts must be non-empty")


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._title_depth = 0
        self.visible: list[str] = []
        self.title: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1
        if lowered == "title":
            self._title_depth += 1

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1
        if lowered == "title" and self._title_depth:
            self._title_depth -= 1

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._title_depth:
            self.title.append(text)
        if not self._ignored_depth:
            self.visible.append(text)


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _validate_detail_url(url: str, config: VerifyConfig) -> str:
    if not url.startswith(("https://", "http://")):
        raise ExactCurrentVerifyError("detail_url must be absolute HTTP(S)")
    host = (urlsplit(url).hostname or "").lower()
    if host not in config.allowed_hosts:
        raise ExactCurrentVerifyError(f"detail_url host is not allowed: {host}")
    path = urlsplit(url).path.lower()
    if "/mitgliederverzeichnis/hotel-" not in path:
        raise ExactCurrentVerifyError("detail_url is not a HotellerieSuisse member-detail path")
    if "hotel-page-" in path:
        raise ExactCurrentVerifyError("directory page URL cannot be used as entity detail URL")
    return url


def _fetch_http(config: VerifyConfig, url: str) -> FetchResponse:
    errors: list[str] = []
    for attempt in range(1, config.attempts + 1):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": config.user_agent,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "de-CH,de;q=0.9,fr-CH;q=0.8,it-CH;q=0.7,en;q=0.5",
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
        except Exception as exc:  # pragma: no cover - deterministic tests inject fetcher
            errors.append(f"{type(exc).__name__}: {exc}")
            if attempt < config.attempts:
                time.sleep(float(attempt))
    raise ExactCurrentVerifyError(f"fetch failed: {'; '.join(errors)}")


def _robots_allowed(config: VerifyConfig, detail_url: str) -> tuple[bool, str]:
    parts = urlsplit(detail_url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        response = _fetch_http(config, robots_url)
        parser = RobotFileParser()
        parser.parse(response.data.decode("utf-8", "replace").splitlines())
        return parser.can_fetch(config.user_agent, detail_url), robots_url
    except ExactCurrentVerifyError:
        return False, robots_url


def parse_visible_identity(html: bytes) -> tuple[str, str]:
    parser = _VisibleTextParser()
    parser.feed(html.decode("utf-8", "replace"))
    return " ".join(parser.title), " ".join(parser.visible)


def classify_verification(
    *,
    name_match: bool,
    city_match: bool,
    http_ok: bool,
) -> str:
    if not http_ok:
        return "FETCH_FAILED"
    if name_match and city_match:
        return "CURRENT_DETAIL_VERIFIED"
    if name_match:
        return "CURRENT_DETAIL_NAME_ONLY"
    if city_match:
        return "CURRENT_DETAIL_CITY_ONLY"
    return "CURRENT_DETAIL_MISMATCH"


def _followup(work_state: str, verification_state: str) -> str:
    if verification_state != "CURRENT_DETAIL_VERIFIED":
        return "REQUEUE_EXACT_CURRENT"
    if work_state == "RECONCILE_REQUIRED":
        return "RESOLVE_CANONICAL_CONFLICT"
    if work_state == "VERIFY_NEW_ENTITY":
        return "DEDUPE_GROUP_ALIAS_REVIEW"
    return "REVIEW_DECISION_SEMANTICS"


def verify_batch(
    batch: Mapping[str, object],
    *,
    config: VerifyConfig | None = None,
    fetcher: Callable[[str], FetchResponse] | None = None,
    robots_checker: Callable[[VerifyConfig, str], tuple[bool, str]] | None = None,
    now: Callable[[], datetime] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    active_config = config or VerifyConfig()
    active_config.validate()
    items = batch.get("items")
    if not isinstance(items, list) or not all(isinstance(item, Mapping) for item in items):
        raise ExactCurrentVerifyError("batch items must be an array of objects")
    if int(batch.get("items_count", -1)) != len(items):
        raise ExactCurrentVerifyError("batch items_count mismatch")
    batch_id = str(batch.get("batch_id", "")).strip()
    if not batch_id:
        raise ExactCurrentVerifyError("batch_id must be non-empty")

    get = fetcher or (lambda url: _fetch_http(active_config, url))
    check_robots = robots_checker or _robots_allowed
    clock = now or (lambda: datetime.now(timezone.utc))
    robots_cache: dict[str, tuple[bool, str]] = {}
    results: list[dict[str, object]] = []

    for index, item in enumerate(items, start=1):
        key = str(item.get("source_record_key", "")).strip()
        name = str(item.get("name", "")).strip()
        city = str(item.get("city", "")).strip()
        detail_url = str(item.get("detail_url", "")).strip()
        work_state = str(item.get("work_state", "")).strip()
        observed_at = clock().isoformat()
        base: dict[str, object] = {
            "batch_id": batch_id,
            "item_index": index,
            "source_record_key": key,
            "expected_name": name,
            "expected_city": city,
            "detail_url": detail_url,
            "work_state": work_state,
            "observed_at": observed_at,
        }
        if not all((key, name, city, detail_url, work_state)):
            results.append(
                {
                    **base,
                    "verification_state": "INVALID_WORK_ITEM",
                    "followup": "REVIEW_PACKET_CONTRACT",
                    "error": "required work-item field missing",
                }
            )
            continue
        try:
            _validate_detail_url(detail_url, active_config)
            host = (urlsplit(detail_url).hostname or "").lower()
            if host not in robots_cache:
                robots_cache[host] = check_robots(active_config, detail_url)
            robots_allowed, robots_url = robots_cache[host]
            if not robots_allowed:
                results.append(
                    {
                        **base,
                        "robots_url": robots_url,
                        "robots_allowed": False,
                        "verification_state": "ROBOTS_BLOCKED",
                        "followup": "PROVIDER_POLICY_REVIEW",
                    }
                )
                continue
            response = get(detail_url)
            title, visible = parse_visible_identity(response.data)
            normalized_visible = _normalize(f"{title} {visible}")
            normalized_name = _normalize(name)
            normalized_city = _normalize(city)
            name_match = bool(normalized_name and normalized_name in normalized_visible)
            city_match = bool(normalized_city and normalized_city in normalized_visible)
            http_ok = 200 <= response.status < 400
            state = classify_verification(
                name_match=name_match,
                city_match=city_match,
                http_ok=http_ok,
            )
            results.append(
                {
                    **base,
                    "robots_url": robots_url,
                    "robots_allowed": True,
                    "http_status": response.status,
                    "final_url": response.final_url,
                    "response_sha256": _sha256_bytes(response.data),
                    "response_bytes": len(response.data),
                    "title": title,
                    "name_match": name_match,
                    "city_match": city_match,
                    "verification_state": state,
                    "followup": _followup(work_state, state),
                    "etag": response.headers.get("ETag") or response.headers.get("Etag"),
                    "last_modified": response.headers.get("Last-Modified"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    **base,
                    "verification_state": "FETCH_FAILED",
                    "followup": "REQUEUE_EXACT_CURRENT",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        if active_config.delay_seconds:
            sleeper(active_config.delay_seconds)

    counts: dict[str, int] = {}
    for result in results:
        state = str(result["verification_state"])
        counts[state] = counts.get(state, 0) + 1
    payload: dict[str, object] = {
        "schema_version": "EXACT-CURRENT-VERIFY-1.0",
        "batch_id": batch_id,
        "items_count": len(items),
        "results_count": len(results),
        "counts_by_state": counts,
        "all_verified": counts.get("CURRENT_DETAIL_VERIFIED", 0) == len(items),
        "results": results,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "packet_sha256": "",
    }
    payload["packet_sha256"] = _sha256_json(
        {key: value for key, value in payload.items() if key != "packet_sha256"}
    )
    return payload


def validate_verification_packet(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != "EXACT-CURRENT-VERIFY-1.0":
        violations.append("INVALID_SCHEMA_VERSION")
    if bool(payload.get("authority_advanced")):
        violations.append("AUTHORITY_ADVANCED_FORBIDDEN")
    if int(payload.get("h_id_allocations", 0)) != 0:
        violations.append("H_ID_ALLOCATIONS_FORBIDDEN")
    if payload.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")
    if int(payload.get("send_allowed", 0)) != 0:
        violations.append("SEND_ALLOWED_NOT_ZERO")
    results = payload.get("results")
    if not isinstance(results, list):
        violations.append("RESULTS_NOT_ARRAY")
        results = []
    if int(payload.get("results_count", -1)) != len(results):
        violations.append("RESULT_COUNT_MISMATCH")
    if int(payload.get("items_count", -1)) != len(results):
        violations.append("ITEM_RESULT_PARITY_MISMATCH")
    keys: set[str] = set()
    for result in results:
        if not isinstance(result, Mapping):
            violations.append("RESULT_NOT_OBJECT")
            continue
        key = str(result.get("source_record_key", "")).strip()
        if not key:
            violations.append("EMPTY_SOURCE_RECORD_KEY")
        elif key in keys:
            violations.append("DUPLICATE_SOURCE_RECORD_KEY")
        keys.add(key)
    expected = _sha256_json(
        {key: value for key, value in payload.items() if key != "packet_sha256"}
    )
    if payload.get("packet_sha256") != expected:
        violations.append("PACKET_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.exact_current_verify")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("batch")
    verify.add_argument("--out", required=True)
    verify.add_argument("--delay", type=float, default=0.25)
    verify.add_argument("--timeout", type=float, default=30.0)
    verify.add_argument("--attempts", type=int, default=3)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "verify":
            raw = _read_json(args.batch)
            if not isinstance(raw, Mapping):
                raise ExactCurrentVerifyError("batch must be a JSON object")
            packet = verify_batch(
                raw,
                config=VerifyConfig(
                    delay_seconds=args.delay,
                    timeout_seconds=args.timeout,
                    attempts=args.attempts,
                ),
            )
            _write_json(args.out, packet)
            print(json.dumps({
                "valid": True,
                "batch_id": packet["batch_id"],
                "items_count": packet["items_count"],
                "counts_by_state": packet["counts_by_state"],
                "all_verified": packet["all_verified"],
                "packet_sha256": packet["packet_sha256"],
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound": "CLOSED",
                "send_allowed": 0,
                "out": args.out,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        raw = _read_json(args.path)
        if not isinstance(raw, Mapping):
            raise ExactCurrentVerifyError("verification packet must be a JSON object")
        violations = validate_verification_packet(raw)
        print(json.dumps({
            "valid": not violations,
            "violations": list(violations),
            "packet_sha256": raw.get("packet_sha256"),
        }, indent=2, sort_keys=True))
        return 0 if not violations else 2
    except (ExactCurrentVerifyError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
