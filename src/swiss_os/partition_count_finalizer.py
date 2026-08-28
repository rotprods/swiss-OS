from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from .directory_manifest import build_member_directory_manifest, write_json_atomic


class PartitionCountFinalizerError(ValueError):
    """Raised when a count-less capture cannot be proven complete by partitions."""


_SCHEMA = "PARTITION-COUNT-FINALIZER-1.0"
_ALLOWED_INPUT_VIOLATION = "REPORTED_RECORDS_UNRESOLVED"


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PartitionCountFinalizerError(f"{field} must be a positive integer")
    return value


def _strict_false(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if not isinstance(value, bool) or value is not False:
        raise PartitionCountFinalizerError(f"{key} must be exactly false")


def _strict_zero(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise PartitionCountFinalizerError(f"{key} must be integer 0")


def finalize_materialized_partition_count(capture_payload: object) -> dict[str, Any]:
    if not isinstance(capture_payload, Mapping):
        raise PartitionCountFinalizerError("capture payload must be a JSON object")
    if capture_payload.get("schema_version") != "MEMBER_DIRECTORY_CAPTURE_V1":
        raise PartitionCountFinalizerError("unsupported capture schema")

    _strict_false(capture_payload, "authority_advanced")
    _strict_zero(capture_payload, "h_id_allocations")
    _strict_false(capture_payload, "outbound_opened")
    _strict_zero(capture_payload, "send_allowed")

    capture_id = capture_payload.get("capture_id")
    locale = capture_payload.get("locale")
    completed_at = capture_payload.get("completed_at")
    if not isinstance(capture_id, str) or not capture_id.strip():
        raise PartitionCountFinalizerError("capture_id must be a non-empty string")
    if not isinstance(locale, str) or not locale.strip():
        raise PartitionCountFinalizerError("locale must be a non-empty string")
    if not isinstance(completed_at, str) or not completed_at.strip():
        raise PartitionCountFinalizerError("completed_at must be a non-empty string")

    reported = capture_payload.get("reported_records")
    if reported not in (None, 0):
        raise PartitionCountFinalizerError(
            "provider-reported count is already present; finalizer is not applicable"
        )
    violations = capture_payload.get("capture_violations")
    if not isinstance(violations, list) or not all(isinstance(item, str) for item in violations):
        raise PartitionCountFinalizerError("capture_violations must be an array of strings")
    non_count_violations = [item for item in violations if item != _ALLOWED_INPUT_VIOLATION]
    if non_count_violations:
        raise PartitionCountFinalizerError(
            "capture has non-count violations: " + ", ".join(non_count_violations)
        )
    if _ALLOWED_INPUT_VIOLATION not in violations:
        raise PartitionCountFinalizerError(
            "capture is not blocked by REPORTED_RECORDS_UNRESOLVED"
        )

    expected_pages = _positive_int(
        capture_payload.get("expected_pages"), field="expected_pages"
    )
    pages = capture_payload.get("pages")
    if not isinstance(pages, list) or not all(isinstance(page, Mapping) for page in pages):
        raise PartitionCountFinalizerError("pages must be an array of objects")
    if len(pages) != expected_pages:
        raise PartitionCountFinalizerError("partition cardinality mismatch")

    seen_positions: set[int] = set()
    seen_detail_urls: set[str] = set()
    records_per_page: dict[int, int] = {}
    materialized_records = 0
    for page in pages:
        assert isinstance(page, Mapping)
        position = _positive_int(page.get("page_position"), field="page_position")
        if position in seen_positions:
            raise PartitionCountFinalizerError(f"duplicate page_position: {position}")
        seen_positions.add(position)
        if page.get("capture_id") != capture_id or page.get("locale") != locale:
            raise PartitionCountFinalizerError(
                f"page {position} capture_id/locale lineage mismatch"
            )
        observed_pages = page.get("observed_expected_pages")
        if observed_pages is not None:
            if _positive_int(observed_pages, field="observed_expected_pages") != expected_pages:
                raise PartitionCountFinalizerError(
                    f"page {position} observed page-count drift"
                )
        observed_count = page.get("observed_reported_records")
        if observed_count not in (None, 0):
            raise PartitionCountFinalizerError(
                f"page {position} has provider count evidence; use provider-reported count"
            )
        source_url = page.get("source_url")
        records = page.get("records")
        if not isinstance(source_url, str) or not source_url.strip():
            raise PartitionCountFinalizerError(f"page {position} source_url missing")
        if not isinstance(records, list) or not records:
            raise PartitionCountFinalizerError(f"page {position} records must be non-empty")
        records_per_page[position] = len(records)
        for record in records:
            if not isinstance(record, Mapping):
                raise PartitionCountFinalizerError(
                    f"page {position} records must contain only objects"
                )
            detail_url = record.get("detail_url")
            if not isinstance(detail_url, str) or not detail_url.strip():
                raise PartitionCountFinalizerError(
                    f"page {position} record detail_url missing"
                )
            if detail_url in seen_detail_urls:
                raise PartitionCountFinalizerError(
                    f"duplicate detail_url across partitions: {detail_url}"
                )
            seen_detail_urls.add(detail_url)
            for field in ("name", "city", "evidence_ref"):
                value = record.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise PartitionCountFinalizerError(
                        f"page {position} record {field} missing"
                    )
            materialized_records += 1

    expected_positions = set(range(1, expected_pages + 1))
    if seen_positions != expected_positions:
        missing = sorted(expected_positions - seen_positions)
        extra = sorted(seen_positions - expected_positions)
        raise PartitionCountFinalizerError(
            f"partition set mismatch missing={missing} extra={extra}"
        )
    if materialized_records <= 0 or materialized_records != len(seen_detail_urls):
        raise PartitionCountFinalizerError("materialized record parity failed")

    # Without an independent provider count, partition cardinality is part of
    # the completeness proof. Every non-last page must expose one stable page
    # size and the final page must contain 1..page_size records. This prevents
    # a missing card on an intermediate page from being silently absorbed into
    # a lower materialized denominator.
    if expected_pages > 1:
        non_last_counts = [records_per_page[pos] for pos in range(1, expected_pages)]
        page_size = non_last_counts[0]
        if page_size <= 0 or any(count != page_size for count in non_last_counts):
            raise PartitionCountFinalizerError(
                "non-last partition cardinality is not stable"
            )
        last_count = records_per_page[expected_pages]
        if not 1 <= last_count <= page_size:
            raise PartitionCountFinalizerError(
                "last partition cardinality exceeds inferred page size"
            )
    else:
        page_size = records_per_page[1]

    finalized_capture = dict(capture_payload)
    finalized_capture.update(
        {
            "declared_raw_records": materialized_records,
            "record_count_basis": "MATERIALIZED_PARTITION_TOTAL",
            "inferred_page_size": page_size,
            "capture_violations": [],
            "capture_mode": "LIVE_COMPLETE_MATERIALIZED_COUNT",
            "coverage_claim": "COMPLETE",
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }
    )
    manifest = build_member_directory_manifest(finalized_capture)
    if manifest.get("coverage_complete") is not True:
        raise PartitionCountFinalizerError(
            "MDM compiler did not accept finalized partition-complete capture: "
            + ", ".join(str(item) for item in manifest.get("violations", []))
        )

    result: dict[str, Any] = {
        "schema_version": _SCHEMA,
        "capture_id": capture_id,
        "expected_pages": expected_pages,
        "inferred_page_size": page_size,
        "materialized_records": materialized_records,
        "record_count_basis": "MATERIALIZED_PARTITION_TOTAL",
        "finalized_capture": finalized_capture,
        "member_directory_manifest": manifest,
        "coverage_complete": True,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "finalizer_sha256": "",
    }
    result["finalizer_sha256"] = _sha256(
        {key: value for key, value in result.items() if key != "finalizer_sha256"}
    )
    return result


def validate_finalizer(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != _SCHEMA:
        violations.append("INVALID_SCHEMA_VERSION")
    if payload.get("coverage_complete") is not True:
        violations.append("COVERAGE_NOT_COMPLETE")
    if payload.get("authority_advanced") is not False:
        violations.append("AUTHORITY_ADVANCED_FORBIDDEN")
    for key in ("h_id_allocations", "send_allowed"):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != 0:
            violations.append(f"INVALID_{key.upper()}")
    if payload.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")
    if payload.get("record_count_basis") != "MATERIALIZED_PARTITION_TOTAL":
        violations.append("INVALID_RECORD_COUNT_BASIS")
    for key in ("expected_pages", "inferred_page_size", "materialized_records"):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            violations.append(f"INVALID_{key.upper()}")
    expected_sha = _sha256(
        {key: value for key, value in payload.items() if key != "finalizer_sha256"}
    )
    if payload.get("finalizer_sha256") != expected_sha:
        violations.append("FINALIZER_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.partition_count_finalizer")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("capture")
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = finalize_materialized_partition_count(_read_json(args.capture))
            write_json_atomic(args.out, result)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "capture_id": result["capture_id"],
                        "expected_pages": result["expected_pages"],
                        "inferred_page_size": result["inferred_page_size"],
                        "materialized_records": result["materialized_records"],
                        "record_count_basis": result["record_count_basis"],
                        "coverage_complete": True,
                        "authority_advanced": False,
                        "h_id_allocations": 0,
                        "outbound": "CLOSED",
                        "send_allowed": 0,
                        "finalizer_sha256": result["finalizer_sha256"],
                        "out": args.out,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        payload = _read_json(args.path)
        if not isinstance(payload, Mapping):
            raise PartitionCountFinalizerError("finalizer payload must be a JSON object")
        violations = validate_finalizer(payload)
        print(
            json.dumps(
                {"valid": not violations, "violations": list(violations)},
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if not violations else 2
    except (PartitionCountFinalizerError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
