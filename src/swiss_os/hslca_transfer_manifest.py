from __future__ import annotations

"""Compile a PCF-finalized HSLCA capture into canonical MEMBER-DIRECTORY-1.0.

The HSLCA/PCF stack historically emitted an intermediate compatibility manifest.
D2C/CMI consumes the stricter transfer-valid manifest implemented by
``swiss_os.member_directory``. This adapter closes that representation gap while
remaining strictly pre-authority: it never allocates H-IDs, mutates canonical
state, opens outbound, or infers source completeness beyond the finalized capture.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from .member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    build_member_directory_manifest,
    validate_member_directory_manifest,
)


class HSLCA transfer_manifestError(ValueError):
    """Raised when a finalized HSLCA capture is not transfer-manifest eligible."""


def _strict_false(payload: Mapping[str, object], field: str) -> None:
    value = payload.get(field)
    if type(value) is not bool or value is not False:
        raise HSLCA transfer_manifestError(f"{field} must be exactly false")


def _strict_zero(payload: Mapping[str, object], field: str) -> None:
    value = payload.get(field)
    if type(value) is not int or value != 0:
        raise HSLCA transfer_manifestError(f"{field} must be integer 0")


def _positive_int(value: object, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise HSLCA transfer_manifestError(f"{field} must be a positive integer")
    return value


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HSLCA transfer_manifestError(f"{field} must be a non-empty string")
    return value.strip()


def _record_id(capture_id: str, detail_url: str) -> str:
    digest = hashlib.sha256(f"{capture_id}|{detail_url}".encode("utf-8")).hexdigest()[:20]
    return f"hslca:{digest}"


def compile_transfer_manifest(finalized_capture: Mapping[str, Any]) -> dict[str, object]:
    if finalized_capture.get("schema_version") != "MEMBER_DIRECTORY_CAPTURE_V1":
        raise HSLCA transfer_manifestError("unsupported capture schema")

    _strict_false(finalized_capture, "authority_advanced")
    _strict_zero(finalized_capture, "h_id_allocations")
    _strict_false(finalized_capture, "outbound_opened")
    _strict_zero(finalized_capture, "send_allowed")

    if finalized_capture.get("capture_mode") != "LIVE_COMPLETE_MATERIALIZED_COUNT":
        raise HSLCA transfer_manifestError("capture_mode must be LIVE_COMPLETE_MATERIALIZED_COUNT")
    if finalized_capture.get("coverage_claim") != "COMPLETE":
        raise HSLCA transfer_manifestError("coverage_claim must be COMPLETE")
    if finalized_capture.get("record_count_basis") != "MATERIALIZED_PARTITION_TOTAL":
        raise HSLCA transfer_manifestError(
            "record_count_basis must be MATERIALIZED_PARTITION_TOTAL"
        )
    violations = finalized_capture.get("capture_violations")
    if violations != []:
        raise HSLCA transfer_manifestError("finalized capture must have zero capture violations")

    capture_id = _required_text(finalized_capture.get("capture_id"), "capture_id")
    locale = _required_text(finalized_capture.get("locale"), "locale").lower()
    completed_at = _required_text(finalized_capture.get("completed_at"), "completed_at")
    expected_pages = _positive_int(finalized_capture.get("expected_pages"), "expected_pages")
    declared_raw_records = _positive_int(
        finalized_capture.get("declared_raw_records"), "declared_raw_records"
    )
    pages = finalized_capture.get("pages")
    if not isinstance(pages, list) or len(pages) != expected_pages:
        raise HSLCA transfer_manifestError("pages must exactly match expected_pages")

    source_url = ""
    records: list[DirectoryRecord] = []
    seen_positions: set[int] = set()
    seen_detail_urls: set[str] = set()
    for page in pages:
        if not isinstance(page, Mapping):
            raise HSLCA transfer_manifestError("pages must contain only objects")
        position = _positive_int(page.get("page_position"), "page_position")
        if position in seen_positions:
            raise HSLCA transfer_manifestError(f"duplicate page_position: {position}")
        seen_positions.add(position)
        if page.get("capture_id") != capture_id or page.get("locale") != locale:
            raise HSLCA transfer_manifestError(
                f"page {position} capture_id/locale lineage mismatch"
            )
        page_source_url = _required_text(page.get("source_url"), f"page {position} source_url")
        if position == 1:
            source_url = page_source_url
        captured_at = _required_text(page.get("captured_at"), f"page {position} captured_at")
        raw_records = page.get("records")
        if not isinstance(raw_records, list) or not raw_records:
            raise HSLCA transfer_manifestError(f"page {position} records must be non-empty")
        for index, raw in enumerate(raw_records, start=1):
            if not isinstance(raw, Mapping):
                raise HSLCA transfer_manifestError(
                    f"page {position} record {index} must be an object"
                )
            name = _required_text(raw.get("name"), f"page {position} record {index} name")
            city = _required_text(raw.get("city"), f"page {position} record {index} city")
            detail_url = _required_text(
                raw.get("detail_url"), f"page {position} record {index} detail_url"
            )
            evidence_ref = _required_text(
                raw.get("evidence_ref"), f"page {position} record {index} evidence_ref"
            )
            if detail_url in seen_detail_urls:
                raise HSLCA transfer_manifestError(f"duplicate detail_url: {detail_url}")
            seen_detail_urls.add(detail_url)
            records.append(
                DirectoryRecord.from_mapping(
                    {
                        "record_id": _record_id(capture_id, detail_url),
                        "name": name,
                        "city": city,
                        "evidence_ref": evidence_ref,
                        "hs_id": str(raw.get("hs_id", "") or "").strip(),
                        "detail_url": detail_url,
                        "source_provider": "HOTELLERIESUISSE_MEMBER_DIRECTORY",
                        "locale": locale,
                        "source_surface": "member-directory",
                        "source_epoch": capture_id,
                        "partition_key": f"page:{position:04d}",
                        "observed_at": captured_at,
                        "evidence_scope": "CURRENT_DIRECTORY_RECORD",
                    }
                )
            )

    if seen_positions != set(range(1, expected_pages + 1)):
        raise HSLCA transfer_manifestError("page positions are not exactly 1..expected_pages")
    if len(records) != declared_raw_records:
        raise HSLCA transfer_manifestError(
            f"materialized records {len(records)} != declared_raw_records {declared_raw_records}"
        )

    result = build_member_directory_manifest(
        records,
        DirectoryManifestConfig(
            snapshot_id=capture_id,
            observed_at=completed_at,
            source_provider="HOTELLERIESUISSE_MEMBER_DIRECTORY",
            locale=locale,
            source_url=source_url,
            source_epoch=capture_id,
            expected_partitions=expected_pages,
            declared_raw_records=declared_raw_records,
            coverage_complete_requested=True,
        ),
    )
    if not result.coverage_complete:
        raise HSLCA transfer_manifestError(
            "canonical MDM rejected finalized capture: " + ", ".join(result.violations)
        )
    transfer_violations = validate_member_directory_manifest(result.manifest)
    if transfer_violations:
        raise HSLCA transfer_manifestError(
            "canonical MDM failed transfer validation: " + ", ".join(transfer_violations)
        )
    return result.manifest


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.hslca_transfer_manifest")
    parser.add_argument("finalized_capture")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        payload = _read_json(args.finalized_capture)
        if not isinstance(payload, Mapping):
            raise HSLCA transfer_manifestError("finalized capture must be a JSON object")
        manifest = compile_transfer_manifest(payload)
        _write_json(args.out, manifest)
        print(
            json.dumps(
                {
                    "valid": True,
                    "snapshot_id": manifest["snapshot_id"],
                    "records_count": manifest["records_count"],
                    "coverage_complete": True,
                    "manifest_sha256": manifest["manifest_sha256"],
                    "authority_advanced": False,
                    "h_id_allocations": 0,
                    "outbound": "CLOSED",
                    "send_allowed": 0,
                    "out": args.out,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except (HSLCA transfer_manifestError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": str(exc),
                    "authority_advanced": False,
                    "h_id_allocations": 0,
                    "outbound": "CLOSED",
                    "send_allowed": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
