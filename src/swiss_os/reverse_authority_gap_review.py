from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "RAGR-1.0"
TOP_SAME_CITY_SUGGESTIONS = 3


class ReverseAuthorityGapReviewError(ValueError):
    """Raised when a reverse authority/source review queue cannot be built safely."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalize(value: object) -> str:
    value = unicodedata.normalize("NFKD", _text(value))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _tokens(value: object) -> frozenset[str]:
    return frozenset(token for token in _normalize(value).split() if len(token) > 1)


def _jaccard(left: Sequence[str] | frozenset[str], right: Sequence[str] | frozenset[str]) -> float:
    a, b = set(left), set(right)
    return 0.0 if not (a or b) else len(a & b) / len(a | b)


def _score(left: str, right: str) -> tuple[float, float, float]:
    name_similarity = SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()
    token_jaccard = _jaccard(_tokens(left), _tokens(right))
    combined = (name_similarity * 0.7) + (token_jaccard * 0.3)
    return round(combined, 6), round(name_similarity, 6), round(token_jaccard, 6)


def _source_rows(payload: object) -> list[Mapping[str, object]]:
    raw = payload.get("records") if isinstance(payload, Mapping) else payload
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise ReverseAuthorityGapReviewError("source universe must contain records array")
    return list(raw)


def _catalog_rows(payload: object) -> list[Mapping[str, object]]:
    raw = payload.get("hotels") if isinstance(payload, Mapping) else payload
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise ReverseAuthorityGapReviewError("canonical catalog must be an array or object with hotels array")
    return list(raw)


def _require_sha(label: str, digest: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ReverseAuthorityGapReviewError(f"{label} must be lowercase SHA-256")


def build_reverse_authority_gap_review(
    *,
    snapshot_id: str,
    authority_epoch: str,
    source_universe: object,
    canonical_catalog: object,
    terminal_coverage: object,
    source_records_sha256: str,
    canonical_catalog_sha256: str,
    terminal_coverage_sha256: str,
) -> dict[str, Any]:
    if not snapshot_id.strip() or not authority_epoch.strip():
        raise ReverseAuthorityGapReviewError("snapshot_id and authority_epoch are required")
    for label, digest in (
        ("source_records_sha256", source_records_sha256),
        ("canonical_catalog_sha256", canonical_catalog_sha256),
        ("terminal_coverage_sha256", terminal_coverage_sha256),
    ):
        _require_sha(label, digest)

    source_rows = _source_rows(source_universe)
    catalog_rows = _catalog_rows(canonical_catalog)
    if _sha256(source_rows) != source_records_sha256:
        raise ReverseAuthorityGapReviewError("source_records_sha256 mismatch")
    if _sha256(canonical_catalog) != canonical_catalog_sha256:
        raise ReverseAuthorityGapReviewError("canonical_catalog_sha256 mismatch")
    if _sha256(terminal_coverage) != terminal_coverage_sha256:
        raise ReverseAuthorityGapReviewError("terminal_coverage_sha256 mismatch")
    if not isinstance(terminal_coverage, list) or not all(
        isinstance(item, Mapping) for item in terminal_coverage
    ):
        raise ReverseAuthorityGapReviewError("terminal_coverage must be an array of objects")

    sources: list[dict[str, str]] = []
    seen_source_keys: set[str] = set()
    for row in source_rows:
        key = _text(row.get("record_id") or row.get("source_record_key"))
        name = _text(row.get("name"))
        city = _text(row.get("city"))
        detail_url = _text(row.get("detail_url"))
        if not key or not name or not city or not detail_url:
            raise ReverseAuthorityGapReviewError("source key/name/city/detail_url are required")
        if key in seen_source_keys:
            raise ReverseAuthorityGapReviewError(f"duplicate source key: {key}")
        seen_source_keys.add(key)
        sources.append({"source_record_key": key, "name": name, "city": city, "detail_url": detail_url})

    canonicals: dict[str, dict[str, Any]] = {}
    for row in catalog_rows:
        hotel_id = _text(row.get("hotel_id"))
        if not re.fullmatch(r"H-\d{4,}", hotel_id):
            raise ReverseAuthorityGapReviewError(f"invalid canonical hotel_id: {hotel_id or '<empty>'}")
        if hotel_id in canonicals:
            raise ReverseAuthorityGapReviewError(f"duplicate canonical hotel_id: {hotel_id}")
        if "is_active" not in row or not isinstance(row.get("is_active"), bool):
            raise ReverseAuthorityGapReviewError(f"canonical is_active must be explicit boolean: {hotel_id}")
        name = _text(row.get("name") or row.get("canonical_name"))
        city = _text(row.get("city"))
        if row.get("is_active") is True and (not name or not city):
            raise ReverseAuthorityGapReviewError(f"active canonical name/city required: {hotel_id}")
        canonicals[hotel_id] = {
            "hotel_id": hotel_id,
            "name": name,
            "city": city,
            "is_active": row.get("is_active"),
            "official_website": _text(row.get("official_website")),
            "hotelleriesuisse_url": _text(row.get("hotelleriesuisse_url") or row.get("detail_url")),
            "source_snapshot_id": _text(row.get("source_snapshot_id")),
            "membership_state": _text(row.get("membership_state")),
            "authority_state": _text(row.get("state")),
            "first_seen": _text(row.get("first_seen")),
            "last_seen": _text(row.get("last_seen")),
        }

    active_ids = {hotel_id for hotel_id, row in canonicals.items() if row["is_active"] is True}
    covered_ids: set[str] = set()
    covered_source_keys: set[str] = set()
    for row in terminal_coverage:
        source_key = _text(row.get("source_record_key"))
        hotel_id = _text(row.get("canonical_hotel_id"))
        if not source_key or source_key not in seen_source_keys:
            raise ReverseAuthorityGapReviewError(f"coverage source key not in source universe: {source_key or '<empty>'}")
        if source_key in covered_source_keys:
            raise ReverseAuthorityGapReviewError(f"duplicate coverage source key: {source_key}")
        covered_source_keys.add(source_key)
        if hotel_id not in active_ids:
            raise ReverseAuthorityGapReviewError(f"coverage target must be active canonical: {hotel_id or '<empty>'}")
        covered_ids.add(hotel_id)

    by_city: dict[str, list[dict[str, str]]] = {}
    for source in sources:
        by_city.setdefault(_normalize(source["city"]), []).append(source)
    for values in by_city.values():
        values.sort(key=lambda item: item["source_record_key"])

    queue: list[dict[str, Any]] = []
    for hotel_id in sorted(active_ids - covered_ids):
        canonical = canonicals[hotel_id]
        same_city = by_city.get(_normalize(canonical["city"]), ())
        suggestions: list[dict[str, Any]] = []
        for source in same_city:
            combined, name_similarity, token_jaccard = _score(canonical["name"], source["name"])
            suggestions.append(
                {
                    "source_record_key": source["source_record_key"],
                    "source_name": source["name"],
                    "source_city": source["city"],
                    "source_detail_url": source["detail_url"],
                    "combined_similarity": combined,
                    "name_similarity": name_similarity,
                    "token_jaccard": token_jaccard,
                }
            )
        suggestions.sort(
            key=lambda item: (
                -float(item["combined_similarity"]),
                -float(item["name_similarity"]),
                -float(item["token_jaccard"]),
                str(item["source_record_key"]),
            )
        )
        suggestions = suggestions[:TOP_SAME_CITY_SUGGESTIONS]
        queue.append(
            {
                "canonical_hotel_id": hotel_id,
                "canonical_name": canonical["name"],
                "canonical_city": canonical["city"],
                "authority_metadata": {
                    "official_website": canonical["official_website"],
                    "hotelleriesuisse_url": canonical["hotelleriesuisse_url"],
                    "source_snapshot_id": canonical["source_snapshot_id"],
                    "membership_state": canonical["membership_state"],
                    "authority_state": canonical["authority_state"],
                    "first_seen": canonical["first_seen"],
                    "last_seen": canonical["last_seen"],
                },
                "same_city_source_candidates": len(same_city),
                "suggestions": suggestions,
                "queue_reason": (
                    "NO_TERMINAL_SOURCE_MAPPING_SAME_CITY_CANDIDATES_PRESENT"
                    if same_city
                    else "NO_TERMINAL_SOURCE_MAPPING_NO_SAME_CITY_SOURCE_CANDIDATE"
                ),
                "required_action": "EVIDENCE_BACKED_REVERSE_GAP_REVIEW",
                "terminal_decision_allowed_from_queue": False,
                "authority_mutation_allowed_from_queue": False,
            }
        )

    queue.sort(key=lambda item: str(item["canonical_hotel_id"]))
    city_counts = Counter(str(item["canonical_city"]) for item in queue)
    no_same_city = sum(1 for item in queue if item["same_city_source_candidates"] == 0)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": snapshot_id,
        "authority_epoch": authority_epoch,
        "source_records_sha256": source_records_sha256,
        "canonical_catalog_sha256": canonical_catalog_sha256,
        "terminal_coverage_sha256": terminal_coverage_sha256,
        "summary": {
            "source_records": len(sources),
            "active_canonical_records": len(active_ids),
            "terminal_coverage_source_records": len(terminal_coverage),
            "unique_covered_canonical_records": len(covered_ids),
            "reverse_authority_source_gaps": len(queue),
            "gaps_without_same_city_source_candidate": no_same_city,
            "gaps_with_same_city_source_candidate": len(queue) - no_same_city,
            "gap_city_counts": dict(sorted(city_counts.items())),
        },
        "review_queue": queue,
        "queue_sha256": _sha256(queue),
        "review_only": True,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "outbound_opened": False,
        "send_allowed": 0,
    }
    violations = validate_reverse_authority_gap_review(result)
    if violations:
        raise ReverseAuthorityGapReviewError("queue validation failed: " + ", ".join(violations))
    return result


def validate_reverse_authority_gap_review(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        violations.append("INVALID_SCHEMA_VERSION")
    if payload.get("review_only") is not True:
        violations.append("REVIEW_ONLY_MUST_BE_TRUE")
    if payload.get("authority_advanced") is not False:
        violations.append("AUTHORITY_ADVANCED_MUST_BE_FALSE")
    if payload.get("outbound") != "CLOSED" or payload.get("outbound_opened") is not False:
        violations.append("OUTBOUND_MUST_REMAIN_CLOSED")
    for key in ("h_id_allocations", "canonical_id_reservations", "send_allowed"):
        value = payload.get(key)
        if isinstance(value, bool) or value != 0:
            violations.append(f"{key.upper()}_MUST_BE_INTEGER_ZERO")
    queue = payload.get("review_queue")
    if not isinstance(queue, list) or not all(isinstance(item, Mapping) for item in queue):
        violations.append("REVIEW_QUEUE_NOT_ARRAY_OF_OBJECTS")
        return tuple(dict.fromkeys(violations))
    if payload.get("queue_sha256") != _sha256(queue):
        violations.append("QUEUE_SHA_MISMATCH")
    ids: list[str] = []
    for item in queue:
        hotel_id = item.get("canonical_hotel_id")
        if not isinstance(hotel_id, str) or not re.fullmatch(r"H-\d{4,}", hotel_id):
            violations.append("INVALID_CANONICAL_HOTEL_ID")
        else:
            ids.append(hotel_id)
        if "action" in item or "resolution_action" in item or "classification" in item:
            violations.append("QUEUE_MUST_NOT_ENCODE_TERMINAL_DECISION")
        if item.get("required_action") != "EVIDENCE_BACKED_REVERSE_GAP_REVIEW":
            violations.append("INVALID_REQUIRED_ACTION")
        if item.get("terminal_decision_allowed_from_queue") is not False:
            violations.append("TERMINAL_DECISION_MUST_BE_FALSE")
        if item.get("authority_mutation_allowed_from_queue") is not False:
            violations.append("AUTHORITY_MUTATION_MUST_BE_FALSE")
        suggestions = item.get("suggestions")
        if not isinstance(suggestions, list) or len(suggestions) > TOP_SAME_CITY_SUGGESTIONS:
            violations.append("INVALID_SUGGESTION_LIST")
            continue
        canonical_city = _normalize(item.get("canonical_city"))
        for suggestion in suggestions:
            if not isinstance(suggestion, Mapping):
                violations.append("SUGGESTION_NOT_OBJECT")
                continue
            if _normalize(suggestion.get("source_city")) != canonical_city:
                violations.append("CROSS_CITY_SUGGESTION_FORBIDDEN")
    if len(ids) != len(set(ids)):
        violations.append("DUPLICATE_GAP_CANONICAL_ID")
    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        violations.append("SUMMARY_NOT_OBJECT")
    elif summary.get("reverse_authority_source_gaps") != len(queue):
        violations.append("REVERSE_GAP_COUNT_MISMATCH")
    return tuple(dict.fromkeys(violations))


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.reverse_authority_gap_review")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("source_universe")
    build.add_argument("canonical_catalog")
    build.add_argument("terminal_coverage")
    build.add_argument("--snapshot-id", required=True)
    build.add_argument("--authority-epoch", required=True)
    build.add_argument("--source-records-sha256", required=True)
    build.add_argument("--canonical-catalog-sha256", required=True)
    build.add_argument("--terminal-coverage-sha256", required=True)
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build_reverse_authority_gap_review(
                snapshot_id=args.snapshot_id,
                authority_epoch=args.authority_epoch,
                source_universe=_read_json(args.source_universe),
                canonical_catalog=_read_json(args.canonical_catalog),
                terminal_coverage=_read_json(args.terminal_coverage),
                source_records_sha256=args.source_records_sha256,
                canonical_catalog_sha256=args.canonical_catalog_sha256,
                terminal_coverage_sha256=args.terminal_coverage_sha256,
            )
            _write_json(args.out, result)
            print(json.dumps({"valid": True, "summary": result["summary"], "queue_sha256": result["queue_sha256"], "out": args.out}, indent=2, sort_keys=True))
            return 0
        payload = _read_json(args.path)
        if not isinstance(payload, Mapping):
            raise ReverseAuthorityGapReviewError("queue must be an object")
        violations = validate_reverse_authority_gap_review(payload)
        print(json.dumps({"valid": not violations, "violations": list(violations), "queue_sha256": payload.get("queue_sha256")}, indent=2, sort_keys=True))
        return 0 if not violations else 2
    except (ReverseAuthorityGapReviewError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
