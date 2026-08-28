from __future__ import annotations

"""Offline enumeration proof for a fully materialized HSLCA capture.

This module exists for the case where the public member directory exposes a
stable terminal pagination boundary but no independently parseable displayed
record count. It does not turn a partial crawl into a complete one. Instead it
requires a hash-valid, exact 1..N page set whose root page itself observed N,
full non-terminal page density, a valid terminal page, unique detail URLs and
no capture violation other than REPORTED_RECORDS_UNRESOLVED.

The result is still pre-authority source evidence. It never allocates H-IDs,
advances canonical state, or opens outbound.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from .directory_manifest import build_member_directory_manifest, write_json_atomic


SCHEMA_VERSION = "HSLCA-PAGINATION-CLOSURE-1.0"
_ALLOWED_INPUT_VIOLATIONS = {"REPORTED_RECORDS_UNRESOLVED"}


class PaginationClosureError(ValueError):
    """Raised when pagination closure cannot prove exhaustive enumeration."""


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _strict_positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PaginationClosureError(f"{name} must be a positive integer")
    return value


def _strict_zero(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise PaginationClosureError(f"{name} must be integer zero")


def _require_false(name: str, value: object) -> None:
    if value is not False:
        raise PaginationClosureError(f"{name} must be false")


def _require_nonempty_string(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PaginationClosureError(f"{name} must be a non-empty string")
    return value.strip()


def prove_pagination_closure(
    capture_payload: Mapping[str, Any],
    *,
    expected_page_size: int = 12,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Prove exhaustive enumeration from HSLCA's captured pagination boundary.

    The proof is intentionally narrower than a generic "count records" fallback.
    A caller cannot supply an arbitrary expected page count: page 1 must have
    observed the same terminal page N from the live source during this capture.
    """

    expected_page_size = _strict_positive_int(
        "expected_page_size", expected_page_size
    )
    if capture_payload.get("schema_version") != "MEMBER_DIRECTORY_CAPTURE_V1":
        raise PaginationClosureError("unsupported capture schema")

    _require_false("authority_advanced", capture_payload.get("authority_advanced"))
    _strict_zero("h_id_allocations", capture_payload.get("h_id_allocations"))
    _require_false("outbound_opened", capture_payload.get("outbound_opened"))
    _strict_zero("send_allowed", capture_payload.get("send_allowed"))

    capture_id = _require_nonempty_string(
        "capture_id", capture_payload.get("capture_id")
    )
    locale = _require_nonempty_string("locale", capture_payload.get("locale"))
    expected_pages = _strict_positive_int(
        "expected_pages", capture_payload.get("expected_pages")
    )

    raw_reported = capture_payload.get("reported_records")
    if raw_reported not in (None, 0):
        raise PaginationClosureError(
            "pagination closure is only for captures without a reported record count"
        )
    if isinstance(raw_reported, bool):
        raise PaginationClosureError("reported_records cannot be boolean")

    raw_violations = capture_payload.get("capture_violations")
    if not isinstance(raw_violations, list) or not all(
        isinstance(value, str) for value in raw_violations
    ):
        raise PaginationClosureError("capture_violations must be an array of strings")
    unexpected = sorted(set(raw_violations).difference(_ALLOWED_INPUT_VIOLATIONS))
    if unexpected:
        raise PaginationClosureError(
            "capture has non-count violations: " + ",".join(unexpected)
        )
    if "REPORTED_RECORDS_UNRESOLVED" not in raw_violations:
        raise PaginationClosureError(
            "capture does not carry the unresolved reported-count condition"
        )

    raw_pages = capture_payload.get("pages")
    if not isinstance(raw_pages, list) or not raw_pages:
        raise PaginationClosureError("capture pages must be a non-empty array")
    if len(raw_pages) != expected_pages:
        raise PaginationClosureError(
            f"observed page objects {len(raw_pages)} != expected_pages {expected_pages}"
        )

    pages_by_position: dict[int, Mapping[str, Any]] = {}
    all_detail_urls: set[str] = set()
    total_records = 0
    page_sizes: dict[int, int] = {}
    page_count_observations: set[int] = set()

    for index, raw_page in enumerate(raw_pages):
        if not isinstance(raw_page, Mapping):
            raise PaginationClosureError(f"page {index} must be an object")
        position = _strict_positive_int(
            f"page {index} page_position", raw_page.get("page_position")
        )
        if position in pages_by_position:
            raise PaginationClosureError(f"duplicate page_position {position}")
        if position > expected_pages:
            raise PaginationClosureError(f"out-of-range page_position {position}")
        pages_by_position[position] = raw_page

        if raw_page.get("capture_id") != capture_id:
            raise PaginationClosureError(f"page {position} capture_id mismatch")
        if str(raw_page.get("locale", "")).strip().lower() != locale.lower():
            raise PaginationClosureError(f"page {position} locale mismatch")
        _require_nonempty_string(f"page {position} source_url", raw_page.get("source_url"))

        observed_pages = raw_page.get("observed_expected_pages")
        if observed_pages is not None:
            observed_pages = _strict_positive_int(
                f"page {position} observed_expected_pages", observed_pages
            )
            page_count_observations.add(observed_pages)

        if raw_page.get("observed_reported_records") is not None:
            raise PaginationClosureError(
                f"page {position} has a reported-record observation; use the count path"
            )

        records = raw_page.get("records")
        if not isinstance(records, list) or not records:
            raise PaginationClosureError(f"page {position} records must be non-empty")
        expected_records_sha = _require_nonempty_string(
            f"page {position} records_sha256", raw_page.get("records_sha256")
        )
        if _canonical_sha256(records) != expected_records_sha:
            raise PaginationClosureError(f"page {position} records hash mismatch")

        page_sizes[position] = len(records)
        total_records += len(records)
        for record_index, record in enumerate(records):
            if not isinstance(record, Mapping):
                raise PaginationClosureError(
                    f"page {position} record {record_index} must be an object"
                )
            _require_nonempty_string(
                f"page {position} record {record_index} name", record.get("name")
            )
            _require_nonempty_string(
                f"page {position} record {record_index} city", record.get("city")
            )
            _require_nonempty_string(
                f"page {position} record {record_index} evidence_ref",
                record.get("evidence_ref"),
            )
            detail_url = _require_nonempty_string(
                f"page {position} record {record_index} detail_url",
                record.get("detail_url"),
            )
            if detail_url in all_detail_urls:
                raise PaginationClosureError(
                    f"duplicate detail_url across capture: {detail_url}"
                )
            all_detail_urls.add(detail_url)

    expected_positions = set(range(1, expected_pages + 1))
    if set(pages_by_position) != expected_positions:
        missing = sorted(expected_positions.difference(pages_by_position))
        raise PaginationClosureError(f"missing page positions: {missing}")

    root_observed_pages = pages_by_position[1].get("observed_expected_pages")
    if root_observed_pages != expected_pages or isinstance(root_observed_pages, bool):
        raise PaginationClosureError(
            "root page did not observe the declared terminal pagination boundary"
        )
    if page_count_observations != {expected_pages}:
        raise PaginationClosureError(
            "pagination observations are absent or disagree with expected_pages"
        )

    for position in range(1, expected_pages):
        if page_sizes[position] != expected_page_size:
            raise PaginationClosureError(
                f"non-terminal page {position} has {page_sizes[position]} records; "
                f"expected {expected_page_size}"
            )
    last_page_count = page_sizes[expected_pages]
    if not 1 <= last_page_count <= expected_page_size:
        raise PaginationClosureError("terminal page record count is invalid")

    proof_core = {
        "schema_version": SCHEMA_VERSION,
        "method": "ROOT_PAGINATION_CLOSURE",
        "capture_id": capture_id,
        "locale": locale.lower(),
        "expected_pages": expected_pages,
        "observed_page_positions": list(range(1, expected_pages + 1)),
        "expected_page_size": expected_page_size,
        "non_terminal_pages_full": True,
        "terminal_page_count": last_page_count,
        "root_observed_expected_pages": expected_pages,
        "page_count_observations": sorted(page_count_observations),
        "unique_detail_urls": len(all_detail_urls),
        "derived_raw_records": total_records,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    proof = dict(proof_core)
    proof["proof_sha256"] = _canonical_sha256(proof_core)

    promoted_capture = json.loads(json.dumps(capture_payload))
    promoted_capture.update(
        {
            "reported_records": total_records,
            "capture_violations": [],
            "capture_mode": "LIVE_COMPLETE_PAGINATION_CLOSURE",
            "coverage_claim": "COMPLETE",
            "enumeration_proof": proof,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }
    )
    manifest = build_member_directory_manifest(promoted_capture)
    if manifest.get("coverage_complete") is not True:
        raise PaginationClosureError(
            "canonical member-directory compiler rejected the pagination-closure capture: "
            + ";".join(str(v) for v in manifest.get("violations", []))
        )
    manifest = dict(manifest)
    manifest["enumeration_proof"] = proof
    manifest["authority_advanced"] = False
    manifest["h_id_allocations"] = 0
    manifest["outbound_opened"] = False
    manifest["send_allowed"] = 0
    return promoted_capture, manifest, proof


def prove_file(
    capture_path: str | Path,
    *,
    out_dir: str | Path,
    expected_page_size: int = 12,
) -> dict[str, Any]:
    capture_file = Path(capture_path)
    payload = json.loads(capture_file.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise PaginationClosureError("capture JSON must be an object")
    capture, manifest, proof = prove_pagination_closure(
        payload, expected_page_size=expected_page_size
    )
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    write_json_atomic(target / "capture-pagination-closed.json", capture)
    write_json_atomic(target / "member-directory-manifest.json", manifest)
    write_json_atomic(target / "pagination-closure-proof.json", proof)
    summary = {
        "capture_id": capture["capture_id"],
        "enumeration_method": proof["method"],
        "expected_pages": proof["expected_pages"],
        "records_count": manifest.get("records_count"),
        "coverage_complete": manifest.get("coverage_complete") is True,
        "proof_sha256": proof["proof_sha256"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    write_json_atomic(target / "pagination-closure-summary.json", summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.pagination_closure")
    sub = parser.add_subparsers(dest="command", required=True)
    prove = sub.add_parser("prove")
    prove.add_argument("capture_json")
    prove.add_argument("--out-dir", required=True)
    prove.add_argument("--expected-page-size", type=int, default=12)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prove":
            result = prove_file(
                args.capture_json,
                out_dir=args.out_dir,
                expected_page_size=args.expected_page_size,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if result["coverage_complete"] else 2
    except (PaginationClosureError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": str(exc),
                    "authority_advanced": False,
                    "h_id_allocations": 0,
                    "outbound_opened": False,
                    "send_allowed": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
