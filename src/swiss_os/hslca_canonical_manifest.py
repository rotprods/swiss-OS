from __future__ import annotations

"""Promote a qualified HSLCA/PCF evidence bundle into canonical MDM shape.

This adapter is deliberately pre-authority. It converts the low-level live capture
manifest produced by HSLCA/PCF into the stable `MEMBER-DIRECTORY-1.0` contract
consumed by the CMI export layer. It does not perform entity resolution against
HOTELS_MASTER and it never allocates an H-ID.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from .member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    MemberDirectoryError,
    build_member_directory_manifest,
    validate_member_directory_manifest,
)


CANONICAL_PROVIDER = "HOTELLERIESUISSE_MEMBER_DIRECTORY"
CANONICAL_SURFACE = "member-directory"
CURRENT_SCOPE = "CURRENT_DIRECTORY_RECORD"
_LOW_LEVEL_SCHEMA = "swiss-os-member-directory-manifest-v1"
_FINALIZER_SCHEMA = "PARTITION-COUNT-FINALIZER-1.0"


class HSLCADeviceToCanonicalError(ValueError):
    """Raised when a qualified HSLCA bundle cannot enter canonical MDM."""


def _strict_bool(payload: Mapping[str, object], key: str, expected: bool) -> None:
    value = payload.get(key)
    if type(value) is not bool or value is not expected:
        raise HSLCADeviceToCanonicalError(f"{key} must be exactly {str(expected).lower()}")


def _strict_zero(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if type(value) is not int or value != 0:
        raise HSLCADeviceToCanonicalError(f"{key} must be integer 0")


def _positive_int(value: object, *, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise HSLCADeviceToCanonicalError(f"{field} must be a positive integer")
    return value


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HSLCADeviceToCanonicalError(f"{field} must be a non-empty string")
    return value.strip()


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


def build_canonical_manifest(finalizer_payload: object) -> dict[str, object]:
    if not isinstance(finalizer_payload, Mapping):
        raise HSLCADeviceToCanonicalError("finalizer payload must be a JSON object")
    if finalizer_payload.get("schema_version") != _FINALIZER_SCHEMA:
        raise HSLCADeviceToCanonicalError("unsupported finalizer schema")
    _strict_bool(finalizer_payload, "coverage_complete", True)
    _strict_bool(finalizer_payload, "authority_advanced", False)
    _strict_zero(finalizer_payload, "h_id_allocations")
    if finalizer_payload.get("outbound") != "CLOSED":
        raise HSLCADeviceToCanonicalError("outbound must remain CLOSED")
    _strict_zero(finalizer_payload, "send_allowed")
    if finalizer_payload.get("record_count_basis") != "MATERIALIZED_PARTITION_TOTAL":
        raise HSLCADeviceToCanonicalError(
            "record_count_basis must be MATERIALIZED_PARTITION_TOTAL"
        )

    low_level = finalizer_payload.get("member_directory_manifest")
    capture = finalizer_payload.get("finalized_capture")
    if not isinstance(low_level, Mapping):
        raise HSLCADeviceToCanonicalError("member_directory_manifest must be an object")
    if not isinstance(capture, Mapping):
        raise HSLCADeviceToCanonicalError("finalized_capture must be an object")

    if low_level.get("schema_version") != _LOW_LEVEL_SCHEMA:
        raise HSLCADeviceToCanonicalError("unsupported low-level manifest schema")
    _strict_bool(low_level, "coverage_complete", True)
    _strict_bool(low_level, "authority_advanced", False)
    _strict_zero(low_level, "h_id_allocations")
    _strict_bool(low_level, "outbound_opened", False)
    _strict_zero(low_level, "send_allowed")
    if low_level.get("violations") != []:
        raise HSLCADeviceToCanonicalError("low-level manifest must contain no violations")

    _strict_bool(capture, "authority_advanced", False)
    _strict_zero(capture, "h_id_allocations")
    _strict_bool(capture, "outbound_opened", False)
    _strict_zero(capture, "send_allowed")
    if capture.get("capture_violations") != []:
        raise HSLCADeviceToCanonicalError("finalized capture must contain no violations")

    capture_id = _required_text(capture.get("capture_id"), field="capture_id")
    if low_level.get("snapshot_id") != capture_id or low_level.get("capture_id") != capture_id:
        raise HSLCADeviceToCanonicalError("capture/manifest snapshot lineage mismatch")
    locale = _required_text(capture.get("locale"), field="locale").lower()
    if low_level.get("locale") != locale:
        raise HSLCADeviceToCanonicalError("capture/manifest locale mismatch")
    completed_at = _required_text(capture.get("completed_at"), field="completed_at")
    expected_pages = _positive_int(capture.get("expected_pages"), field="expected_pages")
    materialized_records = _positive_int(
        finalizer_payload.get("materialized_records"), field="materialized_records"
    )
    if low_level.get("records_count") != materialized_records:
        raise HSLCADeviceToCanonicalError("low-level record count mismatch")

    raw_manifest_records = low_level.get("records")
    raw_pages = capture.get("pages")
    if not isinstance(raw_manifest_records, list) or not all(
        isinstance(row, Mapping) for row in raw_manifest_records
    ):
        raise HSLCADeviceToCanonicalError("low-level records must be an array of objects")
    if not isinstance(raw_pages, list) or not all(isinstance(page, Mapping) for page in raw_pages):
        raise HSLCADeviceToCanonicalError("capture pages must be an array of objects")
    if len(raw_pages) != expected_pages:
        raise HSLCADeviceToCanonicalError("capture page cardinality mismatch")
    if len(raw_manifest_records) != materialized_records:
        raise HSLCADeviceToCanonicalError("materialized record cardinality mismatch")

    manifest_by_url: dict[str, Mapping[str, object]] = {}
    for index, row in enumerate(raw_manifest_records):
        assert isinstance(row, Mapping)
        detail_url = _required_text(row.get("detail_url"), field=f"manifest record {index} detail_url")
        if detail_url in manifest_by_url:
            raise HSLCADeviceToCanonicalError(f"duplicate low-level detail URL: {detail_url}")
        manifest_by_url[detail_url] = row

    seen_positions: set[int] = set()
    seen_urls: set[str] = set()
    canonical_records: list[DirectoryRecord] = []
    root_url = ""
    for raw_page in raw_pages:
        assert isinstance(raw_page, Mapping)
        position = _positive_int(raw_page.get("page_position"), field="page_position")
        if position in seen_positions:
            raise HSLCADeviceToCanonicalError(f"duplicate page_position: {position}")
        seen_positions.add(position)
        if raw_page.get("capture_id") != capture_id:
            raise HSLCADeviceToCanonicalError(f"page {position} capture_id mismatch")
        if raw_page.get("locale") != locale:
            raise HSLCADeviceToCanonicalError(f"page {position} locale mismatch")
        captured_at = _required_text(raw_page.get("captured_at"), field=f"page {position} captured_at")
        if raw_page.get("captured_at_basis") != "ATOMIC_CHECKPOINT_FILE_MTIME":
            raise HSLCADeviceToCanonicalError(
                f"page {position} lacks HPCB checkpoint timestamp provenance"
            )
        page_source_url = _required_text(raw_page.get("source_url"), field=f"page {position} source_url")
        if position == 1:
            root_url = page_source_url
        page_records = raw_page.get("records")
        if not isinstance(page_records, list) or not all(
            isinstance(record, Mapping) for record in page_records
        ):
            raise HSLCADeviceToCanonicalError(f"page {position} records must be objects")
        for record_index, raw_record in enumerate(page_records, start=1):
            assert isinstance(raw_record, Mapping)
            detail_url = _required_text(
                raw_record.get("detail_url"),
                field=f"page {position} record {record_index} detail_url",
            )
            if detail_url in seen_urls:
                raise HSLCADeviceToCanonicalError(f"duplicate capture detail URL: {detail_url}")
            seen_urls.add(detail_url)
            low = manifest_by_url.get(detail_url)
            if low is None:
                raise HSLCADeviceToCanonicalError(
                    f"capture record missing from low-level manifest: {detail_url}"
                )
            for field in ("name", "city", "evidence_ref", "hs_id"):
                if str(low.get(field, "")) != str(raw_record.get(field, "")):
                    raise HSLCADeviceToCanonicalError(
                        f"capture/manifest {field} mismatch for {detail_url}"
                    )
            record_id = _required_text(low.get("record_id"), field="record_id")
            canonical_records.append(
                DirectoryRecord.from_mapping(
                    {
                        "record_id": record_id,
                        "name": raw_record.get("name"),
                        "city": raw_record.get("city"),
                        "evidence_ref": raw_record.get("evidence_ref"),
                        "hs_id": raw_record.get("hs_id", ""),
                        "detail_url": detail_url,
                        "source_provider": CANONICAL_PROVIDER,
                        "locale": locale,
                        "source_surface": CANONICAL_SURFACE,
                        "source_epoch": capture_id,
                        "partition_key": f"page-{position:04d}",
                        "observed_at": captured_at,
                        "evidence_scope": CURRENT_SCOPE,
                    }
                )
            )

    required_positions = set(range(1, expected_pages + 1))
    if seen_positions != required_positions:
        missing = sorted(required_positions - seen_positions)
        extra = sorted(seen_positions - required_positions)
        raise HSLCADeviceToCanonicalError(
            f"capture partition set mismatch missing={missing} extra={extra}"
        )
    if len(seen_urls) != materialized_records or set(manifest_by_url) != seen_urls:
        raise HSLCADeviceToCanonicalError("capture/manifest record universe mismatch")
    if not root_url:
        raise HSLCADeviceToCanonicalError("root source URL was not established")

    config = DirectoryManifestConfig(
        snapshot_id=capture_id,
        observed_at=completed_at,
        source_provider=CANONICAL_PROVIDER,
        locale=locale,
        source_url=root_url,
        source_epoch=capture_id,
        expected_partitions=expected_pages,
        declared_raw_records=materialized_records,
        coverage_complete_requested=True,
    )
    try:
        result = build_member_directory_manifest(tuple(canonical_records), config)
    except MemberDirectoryError as exc:
        raise HSLCADeviceToCanonicalError(str(exc)) from exc
    if not result.coverage_complete:
        raise HSLCADeviceToCanonicalError(
            "canonical member-directory manifest is incomplete: "
            + ", ".join(result.violations)
        )
    validation = validate_member_directory_manifest(result.manifest)
    if validation:
        raise HSLCADeviceToCanonicalError(
            "canonical manifest failed self-validation: " + ", ".join(validation)
        )
    return result.manifest


def build_file(finalizer_path: str | Path, *, out_path: str | Path) -> dict[str, object]:
    payload = _read_json(finalizer_path)
    manifest = build_canonical_manifest(payload)
    _write_json(out_path, manifest)
    return {
        "valid": True,
        "schema_version": manifest["schema_version"],
        "snapshot_id": manifest["snapshot_id"],
        "records_count": manifest["records_count"],
        "records_sha256": manifest["records_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "coverage_complete": True,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "out": str(out_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.hslca_canonical_manifest")
    parser.add_argument("finalizer")
    parser.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = build_file(args.finalizer, out_path=args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (HSLCADeviceToCanonicalError, MemberDirectoryError, json.JSONDecodeError, OSError, ValueError) as exc:
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
