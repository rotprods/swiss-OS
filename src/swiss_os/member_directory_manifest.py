from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping

from .snapshot_freeze import normalize_text, normalize_url


@dataclass(frozen=True)
class MemberDirectoryObservation:
    name: str
    city: str
    evidence_ref: str
    locale: str
    epoch: str
    page: int | None = None
    hs_id: str = ""
    detail_url: str = ""
    record_id: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], index: int) -> "MemberDirectoryObservation":
        name = str(value.get("name", "") or "").strip()
        city = str(value.get("city", "") or "").strip()
        evidence_ref = str(value.get("evidence_ref", "") or "").strip()
        locale = str(value.get("locale", "") or "").strip().lower()
        epoch = str(value.get("epoch", "") or "").strip()
        hs_id = str(value.get("hs_id", "") or "").strip()
        detail_url = normalize_url(str(value.get("detail_url", "") or ""))
        raw_page = value.get("page")
        if isinstance(raw_page, bool):
            raise ValueError(f"observation {index} page must be a positive integer")
        page = int(raw_page) if raw_page not in (None, "") else None
        if not name:
            raise ValueError(f"observation {index} is missing name")
        if not evidence_ref:
            raise ValueError(f"observation {index} is missing evidence_ref")
        if not locale:
            raise ValueError(f"observation {index} is missing locale")
        if not epoch:
            raise ValueError(f"observation {index} is missing epoch")
        if page is not None and page <= 0:
            raise ValueError(f"observation {index} page must be positive")
        record_id = str(value.get("record_id", "") or "").strip()
        if not record_id:
            identity = hs_id or detail_url or f"{normalize_text(name)}|{normalize_text(city)}"
            seed = f"{epoch}|{locale}|{identity}"
            record_id = "MD-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
        return cls(name, city, evidence_ref, locale, epoch, page, hs_id, detail_url, record_id)

    def identity_key(self) -> str:
        if self.hs_id:
            return f"hs:{self.hs_id}"
        if self.detail_url:
            return f"url:{self.detail_url}"
        return f"nc:{normalize_text(self.name)}|{normalize_text(self.city)}"

    def as_record(self) -> dict[str, str]:
        return {
            "record_id": self.record_id,
            "name": self.name,
            "city": self.city,
            "hs_id": self.hs_id,
            "detail_url": self.detail_url,
            "evidence_ref": self.evidence_ref,
        }


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    dup: set[str] = set()
    for value in values:
        if value in seen:
            dup.add(value)
        seen.add(value)
    return sorted(dup)


def _require_positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def compile_member_directory_manifest(
    observations: Iterable[Mapping[str, Any]],
    *,
    snapshot_id: str,
    observed_at: str,
    expected_pages: int,
    declared_raw_records: int,
) -> dict[str, Any]:
    snapshot_id = snapshot_id.strip()
    observed_at = observed_at.strip()
    if not snapshot_id or not observed_at:
        raise ValueError("snapshot_id and observed_at are required")
    expected_pages = _require_positive_int("expected_pages", expected_pages)
    declared_raw_records = _require_positive_int("declared_raw_records", declared_raw_records)

    raw_rows = list(observations)
    if not all(isinstance(value, Mapping) for value in raw_rows):
        raise ValueError("all member-directory observations must be objects")
    rows = [MemberDirectoryObservation.from_mapping(value, idx) for idx, value in enumerate(raw_rows)]
    if not rows:
        raise ValueError("at least one member-directory observation is required")

    locales = sorted({row.locale for row in rows})
    epochs = sorted({row.epoch for row in rows})
    observed_page_set = {row.page for row in rows if row.page is not None}
    expected_page_set = set(range(1, expected_pages + 1))
    missing_pages = sorted(expected_page_set.difference(observed_page_set))
    out_of_range_pages = sorted(page for page in observed_page_set if page not in expected_page_set)
    observed_valid_pages = sorted(observed_page_set.intersection(expected_page_set))
    duplicate_record_ids = _duplicates(row.record_id for row in rows)
    duplicate_identity_keys = _duplicates(row.identity_key() for row in rows)

    violations: list[str] = []
    if len(locales) != 1:
        violations.append(f"mixed locales: {locales}")
    if len(epochs) != 1:
        violations.append(f"mixed epochs: {epochs}")
    if missing_pages:
        violations.append(f"missing pages: {missing_pages}")
    if out_of_range_pages:
        violations.append(f"out-of-range pages: {out_of_range_pages}")
    if len(rows) != declared_raw_records:
        violations.append(f"materialized_records={len(rows)} != declared_raw_records={declared_raw_records}")
    if duplicate_record_ids:
        violations.append("duplicate record_id values detected")
    if duplicate_identity_keys:
        violations.append("duplicate stable identity keys detected")

    ordered = sorted(rows, key=lambda row: (row.identity_key(), row.record_id))
    records = [row.as_record() for row in ordered]
    records_sha256 = hashlib.sha256(
        json.dumps(records, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "schema_version": "swiss-os-member-directory-manifest-v1",
        "snapshot_id": snapshot_id,
        "observed_at": observed_at,
        "locale": locales[0] if len(locales) == 1 else "MIXED",
        "epoch": epochs[0] if len(epochs) == 1 else "MIXED",
        "expected_pages": expected_pages,
        "observed_pages": len(observed_valid_pages),
        "observed_page_numbers": observed_valid_pages,
        "missing_pages": missing_pages,
        "out_of_range_pages": out_of_range_pages,
        "declared_raw_records": declared_raw_records,
        "materialized_records": len(records),
        "duplicate_record_ids": duplicate_record_ids,
        "duplicate_identity_keys": duplicate_identity_keys,
        "coverage_complete": not violations,
        "violations": violations,
        "records_sha256": records_sha256,
        "records": records,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
    }
