"""Provider-neutral coherent member-directory manifest builder.

This module converts one explicitly scoped directory capture into the member-
directory evidence manifest required by SSR-1.0. It is intentionally fail-closed:
partial/historical caches remain discovery evidence and can never assert
``coverage_complete=true``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlsplit, urlunsplit
import unicodedata


SCHEMA_VERSION = "MEMBER_DIRECTORY_CAPTURE_V1"
MANIFEST_SCHEMA_VERSION = "MEMBER_DIRECTORY_MANIFEST_V1"


class CaptureMode(str, Enum):
    LIVE_COMPLETE = "LIVE_COMPLETE"
    LIVE_PARTIAL = "LIVE_PARTIAL"
    RECOVERY_COMPLETE = "RECOVERY_COMPLETE"
    HISTORICAL_CACHE = "HISTORICAL_CACHE"


class CoverageClaim(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class ManifestValidation:
    valid: bool
    coverage_complete: bool
    violations: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "coverage_complete": self.coverage_complete,
            "violations": list(self.violations),
            "warnings": list(self.warnings),
        }


def _iso(value: str, field: str) -> datetime:
    if not value:
        raise ValueError(f"{field} is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_identity_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", _text(value))
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_detail_url(value: object) -> str:
    raw = _text(value)
    if not raw:
        return ""
    parsed = urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"invalid detail URL: {raw}")
    hostname = parsed.hostname.casefold()
    port = parsed.port
    netloc = hostname
    if port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        netloc = f"{hostname}:{port}"
    path = re.sub(r"/+", "/", unquote(parsed.path or "/"))
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), netloc, path, "", ""))


def _canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _source_record_key(record: Mapping[str, Any]) -> str:
    hs_id = _text(record.get("hs_id"))
    if hs_id:
        return f"hs:{normalize_identity_text(hs_id)}"
    detail_url = normalize_detail_url(record.get("detail_url"))
    if detail_url:
        return f"url:{detail_url}"
    name = normalize_identity_text(record.get("name"))
    city = normalize_identity_text(record.get("city"))
    if not name or not city:
        raise ValueError("record requires hs_id, detail_url or a complete name+city identity")
    digest = hashlib.sha256(f"{name}\0{city}".encode("utf-8")).hexdigest()
    return f"namecity:{digest}"


def _record_id(source_record_key: str) -> str:
    digest = hashlib.sha256(source_record_key.encode("utf-8")).hexdigest()
    return f"md:{digest[:24]}"


def _record_from_capture(
    record: Mapping[str, Any],
    *,
    page_id: str,
    page_position: int,
    page_source_url: str,
    record_position: int,
) -> dict[str, Any]:
    name = _text(record.get("name"))
    city = _text(record.get("city"))
    evidence_ref = _text(record.get("evidence_ref"))
    if not name:
        raise ValueError("record name is required")
    if not city:
        raise ValueError(f"record city is required for {name}")
    if not evidence_ref:
        raise ValueError(f"record evidence_ref is required for {name} / {city}")
    hs_id = _text(record.get("hs_id"))
    detail_url = normalize_detail_url(record.get("detail_url"))
    key = _source_record_key(record)
    output = {
        "record_id": _record_id(key),
        "source_record_key": key,
        "name": name,
        "city": city,
        "hs_id": hs_id,
        "detail_url": detail_url,
        "evidence_ref": evidence_ref,
        "source_url": normalize_detail_url(record.get("source_url") or page_source_url),
        "page_id": page_id,
        "page_position": page_position,
        "record_position": record_position,
    }
    return output


def build_member_directory_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic SSR-compatible directory manifest.

    Output is always written as non-authoritative evidence. ``coverage_complete``
    is true only when the complete-capture contract passes with zero violations.
    """

    violations: list[str] = []
    warnings: list[str] = []

    schema_version = _text(payload.get("schema_version"))
    if schema_version != SCHEMA_VERSION:
        violations.append(f"SCHEMA_VERSION_MISMATCH:{schema_version or 'EMPTY'}")

    capture_id = _text(payload.get("capture_id"))
    provider = _text(payload.get("provider"))
    surface = _text(payload.get("surface"))
    locale = _text(payload.get("locale")).lower()
    mode_raw = _text(payload.get("capture_mode"))
    claim_raw = _text(payload.get("coverage_claim"))

    for field, value in (
        ("capture_id", capture_id),
        ("provider", provider),
        ("surface", surface),
        ("locale", locale),
    ):
        if not value:
            violations.append(f"MISSING_{field.upper()}")

    try:
        mode = CaptureMode(mode_raw)
    except ValueError:
        mode = CaptureMode.LIVE_PARTIAL
        violations.append(f"INVALID_CAPTURE_MODE:{mode_raw or 'EMPTY'}")

    try:
        claim = CoverageClaim(claim_raw)
    except ValueError:
        claim = CoverageClaim.PARTIAL
        violations.append(f"INVALID_COVERAGE_CLAIM:{claim_raw or 'EMPTY'}")

    try:
        started = _iso(_text(payload.get("started_at")), "started_at")
        completed = _iso(_text(payload.get("completed_at")), "completed_at")
        if completed < started:
            violations.append("CAPTURE_COMPLETED_BEFORE_STARTED")
    except ValueError as exc:
        started = completed = datetime(1970, 1, 1, tzinfo=timezone.utc)
        violations.append(f"INVALID_CAPTURE_TIME:{exc}")

    expected_pages = int(payload.get("expected_pages") or 0)
    reported_records = int(payload.get("reported_records") or 0)
    pages_payload = payload.get("pages", ())
    if not isinstance(pages_payload, Sequence) or isinstance(pages_payload, (str, bytes)):
        pages_payload = ()
        violations.append("PAGES_NOT_ARRAY")

    records: list[dict[str, Any]] = []
    seen_page_ids: set[str] = set()
    seen_page_positions: set[int] = set()
    seen_record_keys: dict[str, dict[str, Any]] = {}

    for page_index, page in enumerate(pages_payload, start=1):
        if not isinstance(page, Mapping):
            violations.append(f"PAGE_NOT_OBJECT:{page_index}")
            continue
        page_id = _text(page.get("page_id"))
        page_position = int(page.get("page_position") or 0)
        page_source_url_raw = page.get("source_url")
        try:
            page_source_url = normalize_detail_url(page_source_url_raw)
        except ValueError as exc:
            page_source_url = ""
            violations.append(f"PAGE_URL_INVALID:{page_index}:{exc}")
        if not page_id:
            violations.append(f"PAGE_ID_MISSING:{page_index}")
        elif page_id in seen_page_ids:
            violations.append(f"DUPLICATE_PAGE_ID:{page_id}")
        seen_page_ids.add(page_id)
        if page_position < 1:
            violations.append(f"PAGE_POSITION_INVALID:{page_id or page_index}")
        elif page_position in seen_page_positions:
            violations.append(f"DUPLICATE_PAGE_POSITION:{page_position}")
        seen_page_positions.add(page_position)

        if _text(page.get("capture_id") or capture_id) != capture_id:
            violations.append(f"PAGE_CAPTURE_ID_MISMATCH:{page_id}")
        if _text(page.get("locale") or locale).lower() != locale:
            violations.append(f"PAGE_LOCALE_MISMATCH:{page_id}")
        if _text(page.get("surface") or surface) != surface:
            violations.append(f"PAGE_SURFACE_MISMATCH:{page_id}")

        page_records = page.get("records", ())
        if not isinstance(page_records, Sequence) or isinstance(page_records, (str, bytes)):
            violations.append(f"PAGE_RECORDS_NOT_ARRAY:{page_id}")
            continue

        for record_position, raw_record in enumerate(page_records, start=1):
            if not isinstance(raw_record, Mapping):
                violations.append(f"RECORD_NOT_OBJECT:{page_id}:{record_position}")
                continue
            try:
                output = _record_from_capture(
                    raw_record,
                    page_id=page_id,
                    page_position=page_position,
                    page_source_url=page_source_url,
                    record_position=record_position,
                )
            except ValueError as exc:
                violations.append(f"INVALID_RECORD:{page_id}:{record_position}:{exc}")
                continue
            key = output["source_record_key"]
            previous = seen_record_keys.get(key)
            if previous is not None:
                violations.append(
                    f"DUPLICATE_SOURCE_RECORD_KEY:{key}:{previous['page_id']}:{page_id}"
                )
                continue
            seen_record_keys[key] = output
            records.append(output)

    observed_pages = len(pages_payload)
    materialized_records = len(records)

    complete_mode = mode in {CaptureMode.LIVE_COMPLETE, CaptureMode.RECOVERY_COMPLETE}
    if claim == CoverageClaim.COMPLETE and not complete_mode:
        violations.append(f"COMPLETE_CLAIM_FORBIDDEN_FOR_MODE:{mode.value}")
    if claim == CoverageClaim.COMPLETE:
        if expected_pages < 1:
            violations.append("COMPLETE_CAPTURE_REQUIRES_EXPECTED_PAGES")
        if observed_pages != expected_pages:
            violations.append(
                f"PAGE_COUNT_MISMATCH:expected={expected_pages}:observed={observed_pages}"
            )
        expected_positions = set(range(1, expected_pages + 1))
        if seen_page_positions != expected_positions:
            violations.append("PAGE_POSITION_COVERAGE_INCOMPLETE")
        if reported_records < 1:
            violations.append("COMPLETE_CAPTURE_REQUIRES_REPORTED_RECORDS")
        if materialized_records != reported_records:
            violations.append(
                f"RECORD_COUNT_MISMATCH:reported={reported_records}:materialized={materialized_records}"
            )
    else:
        warnings.append("PARTIAL_CAPTURE_CANNOT_FREEZE")

    records.sort(key=lambda item: item["source_record_key"])
    records_sha256 = _sha256(records)
    coverage_complete = (
        claim == CoverageClaim.COMPLETE
        and complete_mode
        and not violations
        and observed_pages == expected_pages
        and materialized_records == reported_records
    )

    snapshot_seed = {
        "capture_id": capture_id,
        "provider": provider,
        "surface": surface,
        "locale": locale,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "completed_at": completed.isoformat().replace("+00:00", "Z"),
        "records_sha256": records_sha256,
    }
    snapshot_id = f"mds:{_sha256(snapshot_seed)[:24]}"

    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "capture_id": capture_id,
        "provider": provider,
        "surface": surface,
        "locale": locale,
        "observed_at": completed.isoformat().replace("+00:00", "Z"),
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "capture_mode": mode.value,
        "coverage_claim": claim.value,
        "coverage_complete": coverage_complete,
        "expected_pages": expected_pages,
        "observed_pages": observed_pages,
        "reported_records": reported_records,
        "records_count": materialized_records,
        "records_sha256": records_sha256,
        "records": records,
        "violations": sorted(set(violations)),
        "warnings": sorted(set(warnings)),
        "capture_valid": not violations,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    unsigned = dict(manifest)
    manifest["manifest_sha256"] = _sha256(unsigned)
    return manifest


def validate_member_directory_manifest(payload: Mapping[str, Any]) -> ManifestValidation:
    violations: list[str] = []
    warnings: list[str] = []

    if _text(payload.get("schema_version")) != MANIFEST_SCHEMA_VERSION:
        violations.append("MANIFEST_SCHEMA_VERSION_MISMATCH")
    records = payload.get("records", ())
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        records = ()
        violations.append("MANIFEST_RECORDS_NOT_ARRAY")

    record_ids: set[str] = set()
    source_keys: set[str] = set()
    normalized_records: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            violations.append(f"MANIFEST_RECORD_NOT_OBJECT:{index}")
            continue
        record_id = _text(record.get("record_id"))
        source_key = _text(record.get("source_record_key"))
        if not record_id:
            violations.append(f"MANIFEST_RECORD_ID_MISSING:{index}")
        elif record_id in record_ids:
            violations.append(f"MANIFEST_RECORD_ID_DUPLICATE:{record_id}")
        record_ids.add(record_id)
        if not source_key:
            violations.append(f"MANIFEST_SOURCE_KEY_MISSING:{index}")
        elif source_key in source_keys:
            violations.append(f"MANIFEST_SOURCE_KEY_DUPLICATE:{source_key}")
        source_keys.add(source_key)
        normalized_records.append(dict(record))

    normalized_records.sort(key=lambda item: _text(item.get("source_record_key")))
    computed_records_sha = _sha256(normalized_records)
    if _text(payload.get("records_sha256")) != computed_records_sha:
        violations.append("MANIFEST_RECORDS_SHA_MISMATCH")
    if int(payload.get("records_count") or 0) != len(normalized_records):
        violations.append("MANIFEST_RECORD_COUNT_MISMATCH")
    if bool(payload.get("authority_advanced")):
        violations.append("MANIFEST_AUTHORITY_ADVANCE_FORBIDDEN")
    if int(payload.get("h_id_allocations") or 0) != 0:
        violations.append("MANIFEST_H_ID_ALLOCATION_FORBIDDEN")
    if bool(payload.get("outbound_opened")):
        violations.append("MANIFEST_OUTBOUND_OPEN_FORBIDDEN")
    if int(payload.get("send_allowed") or 0) != 0:
        violations.append("MANIFEST_SEND_ALLOWED_FORBIDDEN")

    unsigned = dict(payload)
    supplied_manifest_sha = _text(unsigned.pop("manifest_sha256", ""))
    if supplied_manifest_sha != _sha256(unsigned):
        violations.append("MANIFEST_SHA_MISMATCH")

    coverage_complete = bool(payload.get("coverage_complete")) and not violations
    if not bool(payload.get("coverage_complete")):
        warnings.append("MANIFEST_NOT_COVERAGE_COMPLETE")

    return ManifestValidation(
        valid=not violations,
        coverage_complete=coverage_complete,
        violations=tuple(sorted(set(violations))),
        warnings=tuple(sorted(set(warnings))),
    )


def read_json_object(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object")
    return payload


def write_json_atomic(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp.replace(target)
