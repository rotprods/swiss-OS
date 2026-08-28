from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from .snapshot_freeze import normalize_text, normalize_url


SCHEMA_VERSION = "swiss-os-member-directory-manifest-v1"


@dataclass(frozen=True)
class MemberDirectoryRecord:
    record_id: str
    name: str
    city: str
    hs_id: str
    detail_url: str
    evidence_ref: str

    def as_dict(self) -> dict[str, str]:
        return {
            "record_id": self.record_id,
            "name": self.name,
            "city": self.city,
            "hs_id": self.hs_id,
            "detail_url": self.detail_url,
            "evidence_ref": self.evidence_ref,
        }


def _stable_record_id(hs_id: str, detail_url: str, name: str, city: str) -> str:
    if hs_id:
        return f"hs:{hs_id}"
    if detail_url:
        digest = hashlib.sha256(detail_url.encode("utf-8")).hexdigest()[:20]
        return f"md:url:{digest}"
    nc = f"{normalize_text(name)}|{normalize_text(city)}"
    if not normalize_text(name) or not normalize_text(city):
        raise ValueError("member-directory record without hs_id/detail_url requires non-empty name and city")
    return "md:nc:" + hashlib.sha256(nc.encode("utf-8")).hexdigest()[:20]


def normalize_member_directory_record(value: Mapping[str, Any]) -> MemberDirectoryRecord:
    name = str(value.get("name", "") or "").strip()
    city = str(value.get("city", "") or "").strip()
    hs_id = str(value.get("hs_id", "") or "").strip()
    detail_url = normalize_url(str(value.get("detail_url", "") or ""))
    evidence_ref = str(value.get("evidence_ref", "") or "").strip()
    explicit_id = str(value.get("record_id", "") or "").strip()

    if not name:
        raise ValueError("member-directory record requires name")
    if not evidence_ref:
        raise ValueError(f"member-directory record {name!r} requires evidence_ref")

    record_id = explicit_id or _stable_record_id(hs_id, detail_url, name, city)
    return MemberDirectoryRecord(record_id, name, city, hs_id, detail_url, evidence_ref)


def _duplicates(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return tuple(sorted(dupes))


def _records_sha(records: Sequence[MemberDirectoryRecord]) -> str:
    payload = [record.as_dict() for record in records]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build_member_directory_manifest(
    raw_records: Sequence[Mapping[str, Any]],
    *,
    snapshot_id: str,
    observed_at: str,
    locale: str,
    source_url: str,
    declared_raw_records: int,
    expected_pages: int,
    observed_pages: int,
    coverage_complete_requested: bool,
) -> dict[str, Any]:
    snapshot_id = str(snapshot_id or "").strip()
    observed_at = str(observed_at or "").strip()
    locale = str(locale or "").strip()
    source_url = normalize_url(str(source_url or ""))
    if not snapshot_id:
        raise ValueError("member-directory manifest requires snapshot_id")
    if not observed_at:
        raise ValueError("member-directory manifest requires observed_at")
    if not locale:
        raise ValueError("member-directory manifest requires locale")
    if not source_url:
        raise ValueError("member-directory manifest requires source_url")
    for name, value in (
        ("declared_raw_records", declared_raw_records),
        ("expected_pages", expected_pages),
        ("observed_pages", observed_pages),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if not isinstance(coverage_complete_requested, bool):
        raise ValueError("coverage_complete_requested must be a boolean")

    normalized = [normalize_member_directory_record(item) for item in raw_records]
    records = sorted(normalized, key=lambda item: item.record_id)

    duplicate_record_ids = _duplicates([item.record_id for item in records])
    duplicate_hs_ids = _duplicates([item.hs_id for item in records])
    duplicate_detail_urls = _duplicates([item.detail_url for item in records])
    if duplicate_record_ids:
        raise ValueError(f"duplicate member-directory record_id values: {', '.join(duplicate_record_ids)}")
    if duplicate_hs_ids:
        raise ValueError(f"duplicate member-directory hs_id values: {', '.join(duplicate_hs_ids)}")
    if duplicate_detail_urls:
        raise ValueError(f"duplicate member-directory detail_url values: {', '.join(duplicate_detail_urls)}")

    normalized_name_city = [f"{normalize_text(item.name)}|{normalize_text(item.city)}" for item in records]
    ambiguous_name_city = _duplicates(normalized_name_city)

    violations: list[str] = []
    if declared_raw_records != len(records):
        violations.append("DECLARED_RECORD_COUNT_MISMATCH")
    if expected_pages <= 0:
        violations.append("EXPECTED_PAGES_NOT_POSITIVE")
    if observed_pages != expected_pages:
        violations.append("PAGE_COVERAGE_INCOMPLETE")
    if declared_raw_records <= 0:
        violations.append("DECLARED_RECORD_COUNT_NOT_POSITIVE")

    coverage_complete = bool(coverage_complete_requested and not violations)
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "observed_at": observed_at,
        "locale": locale,
        "source_url": source_url,
        "declared_raw_records": declared_raw_records,
        "materialized_records": len(records),
        "expected_pages": expected_pages,
        "observed_pages": observed_pages,
        "coverage_complete_requested": coverage_complete_requested,
        "coverage_complete": coverage_complete,
        "coverage_violations": violations,
        "duplicate_record_ids": 0,
        "duplicate_hs_ids": 0,
        "duplicate_detail_urls": 0,
        "ambiguous_name_city_keys": len(ambiguous_name_city),
        "records_sha256": _records_sha(records),
        "records": [item.as_dict() for item in records],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
    }


def validate_member_directory_manifest(payload: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if str(payload.get("schema_version", "")) != SCHEMA_VERSION:
        errors.append("INVALID_SCHEMA_VERSION")
    for field in ("snapshot_id", "observed_at", "locale", "source_url"):
        if not str(payload.get(field, "") or "").strip():
            errors.append(f"MISSING_{field.upper()}")

    raw_records = payload.get("records", [])
    if not isinstance(raw_records, list):
        return tuple(errors + ["RECORDS_NOT_ARRAY"])
    try:
        records = [normalize_member_directory_record(item) for item in raw_records if isinstance(item, Mapping)]
    except ValueError as exc:
        return tuple(errors + [f"INVALID_RECORD:{exc}"])
    if len(records) != len(raw_records):
        errors.append("RECORDS_CONTAIN_NON_OBJECT")

    if len({item.record_id for item in records}) != len(records):
        errors.append("DUPLICATE_RECORD_ID")
    hs_ids = [item.hs_id for item in records if item.hs_id]
    if len(set(hs_ids)) != len(hs_ids):
        errors.append("DUPLICATE_HSID")
    urls = [item.detail_url for item in records if item.detail_url]
    if len(set(urls)) != len(urls):
        errors.append("DUPLICATE_DETAIL_URL")

    declared = payload.get("declared_raw_records")
    materialized = payload.get("materialized_records")
    expected_pages = payload.get("expected_pages")
    observed_pages = payload.get("observed_pages")
    for field, value in (
        ("declared_raw_records", declared),
        ("materialized_records", materialized),
        ("expected_pages", expected_pages),
        ("observed_pages", observed_pages),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"INVALID_{field.upper()}")

    if isinstance(declared, int) and declared != len(records):
        errors.append("DECLARED_RECORD_COUNT_MISMATCH")
    if isinstance(materialized, int) and materialized != len(records):
        errors.append("MATERIALIZED_RECORD_COUNT_MISMATCH")
    if isinstance(expected_pages, int) and isinstance(observed_pages, int) and observed_pages != expected_pages:
        errors.append("PAGE_COVERAGE_INCOMPLETE")

    sorted_records = sorted(records, key=lambda item: item.record_id)
    if str(payload.get("records_sha256", "")) != _records_sha(sorted_records):
        errors.append("RECORDS_SHA256_MISMATCH")

    complete = payload.get("coverage_complete")
    if not isinstance(complete, bool):
        errors.append("COVERAGE_COMPLETE_NOT_BOOLEAN")
    elif complete:
        if errors:
            errors.append("COVERAGE_COMPLETE_TRUE_WITH_VALIDATION_ERRORS")
        if not bool(payload.get("coverage_complete_requested", False)):
            errors.append("COVERAGE_COMPLETE_TRUE_WITHOUT_REQUEST")

    if payload.get("authority_advanced") is not False:
        errors.append("AUTHORITY_ADVANCED_MUST_BE_FALSE")
    if payload.get("h_id_allocations") != 0:
        errors.append("H_ID_ALLOCATIONS_MUST_BE_ZERO")
    if payload.get("outbound_opened") is not False:
        errors.append("OUTBOUND_OPENED_MUST_BE_FALSE")
    return tuple(errors)
