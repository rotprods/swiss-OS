from __future__ import annotations

"""Compatibility bridge from HSLCA capture payloads to the current MDM compiler.

HSLCA was developed against an intermediate MDMA module name. This adapter keeps
its capture/checkpoint implementation isolated while routing the final manifest
through the canonical `member_directory_manifest` compiler already on main.
It is deliberately pre-authority and fail-closed on any capture violation.
"""

import json
from pathlib import Path
from typing import Any, Mapping

from .member_directory_manifest import compile_member_directory_manifest


def write_json_atomic(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def build_member_directory_manifest(capture_payload: Mapping[str, Any]) -> dict[str, Any]:
    if capture_payload.get("schema_version") != "MEMBER_DIRECTORY_CAPTURE_V1":
        raise ValueError("unsupported HSLCA capture schema")

    capture_id = str(capture_payload.get("capture_id", "") or "").strip()
    locale = str(capture_payload.get("locale", "") or "").strip().lower()
    observed_at = str(capture_payload.get("completed_at", "") or "").strip()
    pages = capture_payload.get("pages")
    if not capture_id or not locale or not observed_at:
        raise ValueError("capture_id, locale and completed_at are required")
    if not isinstance(pages, list) or not pages:
        raise ValueError("capture pages must be a non-empty array")

    expected_pages = _positive_int(capture_payload.get("expected_pages"))
    if expected_pages is None:
        raise ValueError("capture expected_pages must be a positive integer")

    observations: list[dict[str, Any]] = []
    source_urls: dict[str, str] = {}
    for page in pages:
        if not isinstance(page, Mapping):
            raise ValueError("capture pages must contain only objects")
        position = _positive_int(page.get("page_position"))
        if position is None:
            raise ValueError("capture page_position must be a positive integer")
        page_url = str(page.get("source_url", "") or "").strip()
        records = page.get("records")
        if not page_url or not isinstance(records, list) or not records:
            raise ValueError("capture page requires source_url and non-empty records")
        for record in records:
            if not isinstance(record, Mapping):
                raise ValueError("capture records must contain only objects")
            detail_url = str(record.get("detail_url", "") or "").strip()
            row = {
                "name": record.get("name", ""),
                "city": record.get("city", ""),
                "hs_id": record.get("hs_id", ""),
                "detail_url": detail_url,
                "evidence_ref": record.get("evidence_ref", ""),
                "locale": locale,
                "epoch": capture_id,
                "page": position,
            }
            observations.append(row)
            if detail_url:
                source_urls[detail_url] = page_url

    if not observations:
        raise ValueError("capture contains zero materialized observations")

    reported_records = _positive_int(capture_payload.get("reported_records"))
    declared_raw_records = reported_records or len(observations)
    manifest = compile_member_directory_manifest(
        observations,
        snapshot_id=capture_id,
        observed_at=observed_at,
        expected_pages=expected_pages,
        declared_raw_records=declared_raw_records,
    )

    capture_violations = capture_payload.get("capture_violations", [])
    if not isinstance(capture_violations, list) or not all(
        isinstance(item, str) for item in capture_violations
    ):
        raise ValueError("capture_violations must be an array of strings")

    out = dict(manifest)
    merged_violations = list(out.get("violations", []))
    merged_violations.extend(
        f"capture:{item}" for item in capture_violations if item
    )
    out.update(
        {
            "source_provider": str(capture_payload.get("provider", "") or "").strip(),
            "source_surface": str(capture_payload.get("surface", "") or "").strip(),
            "capture_id": capture_id,
            "capture_mode": capture_payload.get("capture_mode"),
            "coverage_claim": capture_payload.get("coverage_claim"),
            "records_count": len(out.get("records", [])),
            "materialized_source_urls": source_urls,
            "violations": merged_violations,
            "coverage_complete": bool(out.get("coverage_complete")) and not merged_violations,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }
    )
    return out
