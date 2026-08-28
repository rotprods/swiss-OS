from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

from .directory_manifest import write_json_atomic
from .partition_count_finalizer import (
    PartitionCountFinalizerError,
    finalize_materialized_partition_count,
)

_SCHEMA = "PARTITION-COUNT-FINALIZER-1.1"
_COUNT_BLOCKER = "REPORTED_RECORDS_UNRESOLVED"
_DRIFT_RE = re.compile(r"^PAGE_COUNT_DRIFT:([0-9]+(?:,[0-9]+)*)$")


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PartitionCountFinalizerError(f"{field} must be a positive integer")
    return value


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _capture_sha(payload: Mapping[str, object]) -> str:
    return _sha256(payload)


def _validate_bounded_pagination_ceiling(
    capture_payload: Mapping[str, object],
) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
    """Validate the live pagination widget as a bounded link ceiling, not a count oracle.

    HSLCA's per-page observation is produced by taking the highest `/hotel-page-N`
    link rendered on that page. A pagination widget may window those links, so an
    interior page can legitimately expose a lower ceiling than the root/terminal
    page. PCF-1.1 tolerates only that downward-only condition.

    Safety conditions are deliberately asymmetric:
    * any observation above the root capture target fails closed;
    * page 1 and the materialized terminal page must both expose the target;
    * every partition 1..target must still exist (enforced again by PCF-1.0);
    * the declared PAGE_COUNT_DRIFT values must exactly match materialized
      checkpoint observations.
    """

    expected_pages = _positive_int(capture_payload.get("expected_pages"), field="expected_pages")
    pages = capture_payload.get("pages")
    if not isinstance(pages, list) or len(pages) != expected_pages:
        raise PartitionCountFinalizerError("partition cardinality mismatch")

    violations = capture_payload.get("capture_violations")
    if not isinstance(violations, list) or not all(isinstance(item, str) for item in violations):
        raise PartitionCountFinalizerError("capture_violations must be an array of strings")
    if _COUNT_BLOCKER not in violations:
        raise PartitionCountFinalizerError("capture is not blocked by REPORTED_RECORDS_UNRESOLVED")

    drift_claims: list[set[int]] = []
    unsupported: list[str] = []
    for violation in violations:
        if violation == _COUNT_BLOCKER:
            continue
        match = _DRIFT_RE.fullmatch(violation)
        if not match:
            unsupported.append(violation)
            continue
        drift_claims.append({int(value) for value in match.group(1).split(",")})
    if unsupported:
        raise PartitionCountFinalizerError(
            "non-count violations: " + ", ".join(unsupported)
        )
    if len(drift_claims) > 1:
        raise PartitionCountFinalizerError("multiple PAGE_COUNT_DRIFT declarations")

    observations: dict[int, int] = {}
    for page in pages:
        if not isinstance(page, Mapping):
            raise PartitionCountFinalizerError("pages must be an array of objects")
        position = _positive_int(page.get("page_position"), field="page_position")
        observed = page.get("observed_expected_pages")
        if observed is None:
            raise PartitionCountFinalizerError(
                f"page {position} lacks pagination-link ceiling evidence"
            )
        ceiling = _positive_int(observed, field=f"page {position} observed_expected_pages")
        if ceiling > expected_pages:
            raise PartitionCountFinalizerError(
                f"page {position} pagination expansion {ceiling}>{expected_pages}"
            )
        observations[position] = ceiling

    required_positions = set(range(1, expected_pages + 1))
    if set(observations) != required_positions:
        raise PartitionCountFinalizerError("partition set mismatch before pagination reconciliation")
    if observations[1] != expected_pages:
        raise PartitionCountFinalizerError("root page does not anchor expected_pages")
    if observations[expected_pages] != expected_pages:
        raise PartitionCountFinalizerError("terminal page does not anchor expected_pages")

    observed_set = tuple(sorted(set(observations.values())))
    lower = tuple(value for value in observed_set if value < expected_pages)
    if drift_claims:
        if set(observed_set) != drift_claims[0]:
            raise PartitionCountFinalizerError(
                "PAGE_COUNT_DRIFT declaration does not match checkpoint observations"
            )
        if not lower:
            raise PartitionCountFinalizerError("PAGE_COUNT_DRIFT declared without lower ceiling")
    elif len(observed_set) > 1:
        raise PartitionCountFinalizerError("pagination ceiling drift is undeclared")

    return expected_pages, observed_set, lower


def finalize_bounded_pagination_ceiling(capture_payload: object) -> dict[str, Any]:
    if not isinstance(capture_payload, Mapping):
        raise PartitionCountFinalizerError("capture payload must be a JSON object")

    expected_pages, observed_set, lower = _validate_bounded_pagination_ceiling(capture_payload)

    # PCF-1.0 owns all partition, lineage, timestamp, record, uniqueness and
    # cardinality checks. Feed it a semantic-normalized copy only after proving
    # that the sole extra anomaly is a downward-only pagination-widget ceiling.
    normalized = copy.deepcopy(dict(capture_payload))
    normalized["capture_violations"] = [_COUNT_BLOCKER]
    for page in normalized["pages"]:
        page["observed_expected_pages"] = expected_pages

    legacy = finalize_materialized_partition_count(normalized)
    result = copy.deepcopy(legacy)
    result["schema_version"] = _SCHEMA
    result["pagination_observation_semantics"] = "VISIBLE_PAGINATION_LINK_CEILING"
    result["observed_pagination_ceilings"] = list(observed_set)
    result["lower_pagination_ceilings_tolerated"] = list(lower)
    result["pagination_anchor_pages"] = [1, expected_pages]
    result["input_capture_sha256"] = _capture_sha(capture_payload)

    # Preserve original checkpoint observations in the finalized provenance;
    # only the semantic violation is resolved by PCF-1.1.
    finalized_capture = result.get("finalized_capture")
    if isinstance(finalized_capture, dict):
        original_pages = capture_payload.get("pages")
        finalized_capture["pages"] = copy.deepcopy(original_pages)
        finalized_capture["pagination_observation_semantics"] = "VISIBLE_PAGINATION_LINK_CEILING"
        finalized_capture["pagination_link_ceiling_observations"] = list(observed_set)
        finalized_capture["pagination_link_ceiling_anomalies"] = list(lower)

    result["finalizer_sha256"] = ""
    result["finalizer_sha256"] = _sha256(
        {key: value for key, value in result.items() if key != "finalizer_sha256"}
    )
    return result


def validate_finalizer_v11(payload: Mapping[str, object]) -> tuple[str, ...]:
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
    if payload.get("pagination_observation_semantics") != "VISIBLE_PAGINATION_LINK_CEILING":
        violations.append("INVALID_PAGINATION_OBSERVATION_SEMANTICS")

    expected = payload.get("expected_pages")
    observed = payload.get("observed_pagination_ceilings")
    lower = payload.get("lower_pagination_ceilings_tolerated")
    anchors = payload.get("pagination_anchor_pages")
    if isinstance(expected, bool) or not isinstance(expected, int) or expected <= 0:
        violations.append("INVALID_EXPECTED_PAGES")
    elif not isinstance(observed, list) or not observed or any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in observed
    ):
        violations.append("INVALID_PAGINATION_CEILINGS")
    else:
        if max(observed) != expected or any(value > expected for value in observed):
            violations.append("PAGINATION_EXPANSION_OR_MISSING_ANCHOR")
        if not isinstance(lower, list) or sorted(lower) != sorted(value for value in observed if value < expected):
            violations.append("LOWER_PAGINATION_CEILING_MISMATCH")
        if anchors != [1, expected]:
            violations.append("INVALID_PAGINATION_ANCHORS")

    input_sha = payload.get("input_capture_sha256")
    if not isinstance(input_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", input_sha):
        violations.append("INVALID_INPUT_CAPTURE_SHA256")
    expected_sha = _sha256(
        {key: value for key, value in payload.items() if key != "finalizer_sha256"}
    )
    if payload.get("finalizer_sha256") != expected_sha:
        violations.append("FINALIZER_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.partition_count_finalizer_v11")
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
            result = finalize_bounded_pagination_ceiling(_read_json(args.capture))
            write_json_atomic(args.out, result)
            print(json.dumps({
                "valid": True,
                "capture_id": result["capture_id"],
                "expected_pages": result["expected_pages"],
                "materialized_records": result["materialized_records"],
                "observed_pagination_ceilings": result["observed_pagination_ceilings"],
                "lower_pagination_ceilings_tolerated": result["lower_pagination_ceilings_tolerated"],
                "record_count_basis": result["record_count_basis"],
                "coverage_complete": True,
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound": "CLOSED",
                "send_allowed": 0,
                "finalizer_sha256": result["finalizer_sha256"],
                "out": args.out,
            }, indent=2, sort_keys=True))
            return 0
        payload = _read_json(args.path)
        if not isinstance(payload, Mapping):
            raise PartitionCountFinalizerError("finalizer payload must be a JSON object")
        violations = validate_finalizer_v11(payload)
        print(json.dumps({"valid": not violations, "violations": list(violations)}, indent=2, sort_keys=True))
        return 0 if not violations else 2
    except (PartitionCountFinalizerError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
