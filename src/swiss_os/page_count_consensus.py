from __future__ import annotations

"""Normalize narrowly bounded HSLCA pagination metadata drift before PCF-1.0.

This module never claims that a drifting source is generally coherent. It handles
one specific cache-skew pattern only: the finalized capture contains the complete
partition set selected by HSLCA, at least 99% of page responses independently
report that same partition count, and the remaining responses report exactly one
fewer page. The terminal page itself must report the selected partition count.

The raw capture is never mutated. A derived capture preserves every divergent
observation in ``observed_expected_pages_original`` and records a consensus proof
before routing the derived payload into the existing strict PCF-1.0 finalizer.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from .directory_manifest import write_json_atomic


SCHEMA_VERSION = "PAGE-COUNT-CONSENSUS-NORMALIZER-1.0"
_DRIFT_PREFIX = "PAGE_COUNT_DRIFT:"
_ALLOWED_BASE_VIOLATION = "REPORTED_RECORDS_UNRESOLVED"


class PageCountConsensusError(ValueError):
    """Raised when pagination drift is not narrow enough to normalize safely."""


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PageCountConsensusError(f"{field} must be a positive integer")
    return value


def _strict_false(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if not isinstance(value, bool) or value is not False:
        raise PageCountConsensusError(f"{key} must be exactly false")


def _strict_zero(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise PageCountConsensusError(f"{key} must be integer 0")


def normalize_page_count_consensus(capture_payload: object) -> dict[str, Any]:
    if not isinstance(capture_payload, Mapping):
        raise PageCountConsensusError("capture payload must be a JSON object")
    if capture_payload.get("schema_version") != "MEMBER_DIRECTORY_CAPTURE_V1":
        raise PageCountConsensusError("unsupported capture schema")

    _strict_false(capture_payload, "authority_advanced")
    _strict_zero(capture_payload, "h_id_allocations")
    _strict_false(capture_payload, "outbound_opened")
    _strict_zero(capture_payload, "send_allowed")

    violations = capture_payload.get("capture_violations")
    if not isinstance(violations, list) or not all(isinstance(item, str) for item in violations):
        raise PageCountConsensusError("capture_violations must be an array of strings")
    unexpected = [
        item
        for item in violations
        if item != _ALLOWED_BASE_VIOLATION and not item.startswith(_DRIFT_PREFIX)
    ]
    if unexpected:
        raise PageCountConsensusError(
            "capture has unsupported violations: " + ", ".join(unexpected)
        )
    drift_violations = [item for item in violations if item.startswith(_DRIFT_PREFIX)]
    if len(drift_violations) > 1:
        raise PageCountConsensusError("capture contains multiple page-count drift violations")
    if _ALLOWED_BASE_VIOLATION not in violations:
        raise PageCountConsensusError("capture is not a count-less PCF candidate")

    expected_pages = _positive_int(capture_payload.get("expected_pages"), field="expected_pages")
    pages = capture_payload.get("pages")
    if not isinstance(pages, list) or not all(isinstance(page, Mapping) for page in pages):
        raise PageCountConsensusError("pages must be an array of objects")
    if len(pages) != expected_pages:
        raise PageCountConsensusError("partition cardinality does not equal expected_pages")

    seen_positions: set[int] = set()
    observations: list[int] = []
    page_by_position: dict[int, Mapping[str, object]] = {}
    for raw_page in pages:
        assert isinstance(raw_page, Mapping)
        position = _positive_int(raw_page.get("page_position"), field="page_position")
        if position in seen_positions:
            raise PageCountConsensusError(f"duplicate page_position: {position}")
        seen_positions.add(position)
        observed = _positive_int(
            raw_page.get("observed_expected_pages"), field="observed_expected_pages"
        )
        observations.append(observed)
        page_by_position[position] = raw_page

    required_positions = set(range(1, expected_pages + 1))
    if seen_positions != required_positions:
        missing = sorted(required_positions - seen_positions)
        extra = sorted(seen_positions - required_positions)
        raise PageCountConsensusError(
            f"partition set mismatch missing={missing} extra={extra}"
        )

    histogram = Counter(observations)
    observed_values = sorted(histogram)
    consensus_count = histogram.get(expected_pages, 0)
    outlier_positions = sorted(
        position
        for position, page in page_by_position.items()
        if page.get("observed_expected_pages") != expected_pages
    )
    outlier_count = len(outlier_positions)

    if outlier_count:
        expected_drift_violation = _DRIFT_PREFIX + ",".join(str(value) for value in observed_values)
        if drift_violations != [expected_drift_violation]:
            raise PageCountConsensusError(
                "PAGE_COUNT_DRIFT declaration does not match observed histogram"
            )
        # At least 99% of independently fetched pages must agree with the selected
        # complete partition count. Integer arithmetic avoids float boundary drift.
        if consensus_count * 100 < expected_pages * 99:
            raise PageCountConsensusError("page-count consensus is below 99 percent")
        if any(value != expected_pages - 1 for value in observations if value != expected_pages):
            raise PageCountConsensusError(
                "page-count outliers must be exactly expected_pages-1"
            )
        if expected_pages in outlier_positions:
            raise PageCountConsensusError("terminal page must report expected_pages")
    elif drift_violations:
        raise PageCountConsensusError("capture declares drift but page observations are unanimous")

    normalized = json.loads(json.dumps(capture_payload))
    normalized_pages = normalized["pages"]
    for page in normalized_pages:
        observed = page["observed_expected_pages"]
        if observed != expected_pages:
            page["observed_expected_pages_original"] = observed
            page["observed_expected_pages"] = expected_pages
            page["page_count_consensus_normalized"] = True

    normalized["capture_violations"] = [_ALLOWED_BASE_VIOLATION]
    normalized["page_count_consensus"] = {
        "schema_version": SCHEMA_VERSION,
        "expected_pages": expected_pages,
        "observations": {str(key): histogram[key] for key in observed_values},
        "consensus_pages": consensus_count,
        "total_pages": expected_pages,
        "outlier_positions": outlier_positions,
        "outlier_count": outlier_count,
        "minimum_consensus_percent": 99,
        "rule": "OUTLIERS_ONLY_EXPECTED_MINUS_ONE_AND_TERMINAL_PAGE_AGREES",
        "raw_capture_preserved": True,
    }
    normalized["authority_advanced"] = False
    normalized["h_id_allocations"] = 0
    normalized["outbound_opened"] = False
    normalized["send_allowed"] = 0
    return normalized


def normalize_file(path: str | Path, *, out_path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    normalized = normalize_page_count_consensus(payload)
    write_json_atomic(out_path, normalized)
    proof = normalized["page_count_consensus"]
    return {
        "valid": True,
        "expected_pages": proof["expected_pages"],
        "consensus_pages": proof["consensus_pages"],
        "outlier_positions": proof["outlier_positions"],
        "raw_capture_preserved": True,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "out": str(out_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.page_count_consensus")
    parser.add_argument("capture")
    parser.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = normalize_file(args.capture, out_path=args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (PageCountConsensusError, json.JSONDecodeError, OSError, ValueError) as exc:
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
