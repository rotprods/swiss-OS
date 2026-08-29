from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "CMRQ-1.0"
NORMALIZATION_PROFILE = "NAME_CITY_GENERIC_TOKEN_V1"
VERY_HIGH_NAME_SIMILARITY = 0.92
HIGH_TOKEN_JACCARD = 0.75
HIGH_TOKEN_MIN_NAME_SIMILARITY = 0.75

_GENERIC_TOKENS = frozenset(
    {
        "alpin",
        "alpine",
        "am",
        "and",
        "apartment",
        "apartements",
        "apartments",
        "boutique",
        "das",
        "de",
        "der",
        "des",
        "die",
        "du",
        "garni",
        "gasthof",
        "haus",
        "hostel",
        "hotel",
        "hotels",
        "house",
        "im",
        "inn",
        "la",
        "le",
        "les",
        "restaurant",
        "resort",
        "spa",
        "the",
        "und",
        "wellness",
        "zum",
        "zur",
    }
)


class CanonicalMatchReviewError(ValueError):
    """Raised when a review-only queue cannot be built safely."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: object) -> str:
    payload = value if isinstance(value, bytes) else _canonical_json(value)
    return hashlib.sha256(payload).hexdigest()


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalize_text(value: object) -> str:
    decomposed = unicodedata.normalize("NFKD", _text(value))
    asciiish = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", asciiish.casefold()))


def _token_signature(value: object) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                token
                for token in _normalize_text(value).split()
                if len(token) > 1 and token not in _GENERIC_TOKENS
            }
        )
    )


def _round_score(value: float) -> float:
    return round(float(value), 6)


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class CandidateIdentity:
    source_record_key: str
    name: str
    city: str
    detail_url: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, object]) -> "CandidateIdentity":
        if not isinstance(row, Mapping):
            raise CanonicalMatchReviewError("candidate record must be an object")
        key = row.get("source_record_key")
        name = row.get("name")
        city = row.get("city")
        detail_url = row.get("detail_url", "")
        if not all(isinstance(value, str) for value in (key, name, city, detail_url)):
            raise CanonicalMatchReviewError("candidate identity fields must be strings")
        key, name, city, detail_url = (
            key.strip(),
            name.strip(),
            city.strip(),
            detail_url.strip(),
        )
        if not key or not name or not city or not detail_url:
            raise CanonicalMatchReviewError(
                "candidate source_record_key, name, city and detail_url are required"
            )
        if row.get("matched_hotel_id") not in {"", None}:
            raise CanonicalMatchReviewError(
                f"candidate {key} already has matched_hotel_id; review queue is pre-authority only"
            )
        if row.get("decision") not in {None, "CANDIDATE_NEW_ENTITY_PREAUTH"}:
            raise CanonicalMatchReviewError(
                f"candidate {key} has unexpected decision {row.get('decision')!r}"
            )
        return cls(key, name, city, detail_url)


@dataclass(frozen=True)
class CanonicalIdentity:
    hotel_id: str
    name: str
    city: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, object]) -> "CanonicalIdentity | None":
        if not isinstance(row, Mapping):
            raise CanonicalMatchReviewError("canonical record must be an object")
        hotel_id = _text(row.get("hotel_id"))
        name = _text(row.get("name") or row.get("canonical_name"))
        city = _text(row.get("city"))
        active = row.get("is_active", True)
        if not re.fullmatch(r"H-\d{4,}", hotel_id):
            raise CanonicalMatchReviewError(
                f"invalid canonical hotel_id: {hotel_id or '<empty>'}"
            )
        if not isinstance(active, bool):
            raise CanonicalMatchReviewError(
                f"canonical is_active must be boolean: {hotel_id}"
            )
        if not active:
            return None
        if not name or not city:
            raise CanonicalMatchReviewError(
                f"active canonical name/city required: {hotel_id}"
            )
        return cls(hotel_id, name, city)


def _catalog_rows(payload: object) -> list[Mapping[str, object]]:
    raw = payload.get("hotels") if isinstance(payload, Mapping) else payload
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise CanonicalMatchReviewError(
            "canonical catalog must be an array or object with hotels array"
        )
    return list(raw)


def _signal_set(
    candidate_name: str,
    canonical_name: str,
) -> tuple[list[str], float, float]:
    left = _normalize_text(candidate_name)
    right = _normalize_text(canonical_name)
    left_tokens = _token_signature(candidate_name)
    right_tokens = _token_signature(canonical_name)
    similarity = SequenceMatcher(None, left, right).ratio()
    jaccard = _jaccard(left_tokens, right_tokens)
    signals: list[str] = []
    if left == right:
        signals.append("EXACT_NORMALIZED_NAME_CITY")
    if left_tokens and left_tokens == right_tokens:
        signals.append("TOKEN_SIGNATURE_EQUAL")
    if similarity >= VERY_HIGH_NAME_SIMILARITY:
        signals.append("VERY_HIGH_NAME_SIMILARITY")
    if (
        jaccard >= HIGH_TOKEN_JACCARD
        and similarity >= HIGH_TOKEN_MIN_NAME_SIMILARITY
    ):
        signals.append("HIGH_TOKEN_OVERLAP")
    return signals, similarity, jaccard


def build_canonical_match_review_queue(
    *,
    snapshot_id: str,
    candidate_records: Iterable[CandidateIdentity | Mapping[str, object]],
    canonical_catalog: object,
    candidate_records_sha256: str,
    canonical_catalog_sha256: str,
) -> dict[str, Any]:
    if not snapshot_id.strip():
        raise CanonicalMatchReviewError("snapshot_id is required")
    for label, digest in {
        "candidate_records_sha256": candidate_records_sha256,
        "canonical_catalog_sha256": canonical_catalog_sha256,
    }.items():
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CanonicalMatchReviewError(f"{label} must be lowercase SHA-256")

    candidates = tuple(
        item
        if isinstance(item, CandidateIdentity)
        else CandidateIdentity.from_mapping(item)
        for item in candidate_records
    )
    if not candidates:
        raise CanonicalMatchReviewError("at least one candidate is required")
    candidate_keys = [item.source_record_key for item in candidates]
    if len(candidate_keys) != len(set(candidate_keys)):
        raise CanonicalMatchReviewError("duplicate candidate source_record_key")

    canonicals: list[CanonicalIdentity] = []
    for row in _catalog_rows(canonical_catalog):
        item = CanonicalIdentity.from_mapping(row)
        if item is not None:
            canonicals.append(item)
    canonical_ids = [item.hotel_id for item in canonicals]
    if len(canonical_ids) != len(set(canonical_ids)):
        raise CanonicalMatchReviewError("duplicate canonical hotel_id")
    if not canonicals:
        raise CanonicalMatchReviewError("at least one active canonical is required")

    by_city: dict[str, list[CanonicalIdentity]] = {}
    for item in canonicals:
        by_city.setdefault(_normalize_text(item.city), []).append(item)
    for values in by_city.values():
        values.sort(key=lambda item: item.hotel_id)

    queue: list[dict[str, Any]] = []
    same_city_pairs_evaluated = 0
    for candidate in sorted(candidates, key=lambda item: item.source_record_key):
        candidate_city = _normalize_text(candidate.city)
        for canonical in by_city.get(candidate_city, ()):
            same_city_pairs_evaluated += 1
            signals, similarity, jaccard = _signal_set(
                candidate.name, canonical.name
            )
            if not signals:
                continue
            queue.append(
                {
                    "source_record_key": candidate.source_record_key,
                    "candidate_name": candidate.name,
                    "candidate_city": candidate.city,
                    "candidate_detail_url": candidate.detail_url,
                    "suggested_canonical_hotel_id": canonical.hotel_id,
                    "canonical_name": canonical.name,
                    "canonical_city": canonical.city,
                    "signals": signals,
                    "name_similarity": _round_score(similarity),
                    "token_jaccard": _round_score(jaccard),
                    "candidate_token_signature": list(
                        _token_signature(candidate.name)
                    ),
                    "canonical_token_signature": list(
                        _token_signature(canonical.name)
                    ),
                    "required_action": "EVIDENCE_BACKED_EXPLICIT_REVIEW",
                    "auto_merge_allowed": False,
                    "terminal_mapping_allowed_from_queue": False,
                }
            )

    signal_rank = {
        "EXACT_NORMALIZED_NAME_CITY": 0,
        "TOKEN_SIGNATURE_EQUAL": 1,
        "VERY_HIGH_NAME_SIMILARITY": 2,
        "HIGH_TOKEN_OVERLAP": 3,
    }
    queue.sort(
        key=lambda item: (
            str(item["source_record_key"]),
            min(signal_rank[signal] for signal in item["signals"]),
            -float(item["name_similarity"]),
            -float(item["token_jaccard"]),
            str(item["suggested_canonical_hotel_id"]),
        )
    )

    by_source = Counter(str(item["source_record_key"]) for item in queue)
    signal_counts = Counter(
        signal for item in queue for signal in item["signals"]
    )
    policy = {
        "normalization_profile": NORMALIZATION_PROFILE,
        "same_city_required": True,
        "generic_tokens": sorted(_GENERIC_TOKENS),
        "very_high_name_similarity": VERY_HIGH_NAME_SIMILARITY,
        "high_token_jaccard": HIGH_TOKEN_JACCARD,
        "high_token_min_name_similarity": HIGH_TOKEN_MIN_NAME_SIMILARITY,
        "auto_merge_allowed": False,
    }
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": snapshot_id,
        "candidate_records_sha256": candidate_records_sha256,
        "canonical_catalog_sha256": canonical_catalog_sha256,
        "policy": policy,
        "policy_sha256": _sha256(policy),
        "summary": {
            "candidate_records": len(candidates),
            "active_canonical_records": len(canonicals),
            "same_city_pairs_evaluated": same_city_pairs_evaluated,
            "review_pairs": len(queue),
            "review_source_records": len(by_source),
            "source_records_with_multiple_targets": sum(
                1 for count in by_source.values() if count > 1
            ),
            "signal_counts": dict(sorted(signal_counts.items())),
        },
        "review_queue": queue,
        "queue_sha256": _sha256(queue),
        "review_only": True,
        "auto_merge_allowed": False,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "outbound_opened": False,
        "send_allowed": 0,
    }
    violations = validate_canonical_match_review_queue(result)
    if violations:
        raise CanonicalMatchReviewError(
            "queue validation failed: " + ", ".join(violations)
        )
    return result


def validate_canonical_match_review_queue(
    payload: Mapping[str, object],
) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        violations.append("INVALID_SCHEMA_VERSION")
    if payload.get("review_only") is not True:
        violations.append("REVIEW_ONLY_MUST_BE_TRUE")
    if payload.get("auto_merge_allowed") is not False:
        violations.append("AUTO_MERGE_MUST_BE_FALSE")
    if payload.get("authority_advanced") is not False:
        violations.append("AUTHORITY_ADVANCED_MUST_BE_FALSE")
    if (
        payload.get("outbound") != "CLOSED"
        or payload.get("outbound_opened") is not False
    ):
        violations.append("OUTBOUND_MUST_REMAIN_CLOSED")
    for key in ("h_id_allocations", "canonical_id_reservations", "send_allowed"):
        value = payload.get(key)
        if isinstance(value, bool) or value != 0:
            violations.append(f"{key.upper()}_MUST_BE_INTEGER_ZERO")

    queue = payload.get("review_queue")
    if not isinstance(queue, list) or not all(
        isinstance(item, Mapping) for item in queue
    ):
        violations.append("REVIEW_QUEUE_NOT_ARRAY_OF_OBJECTS")
        return tuple(dict.fromkeys(violations))
    if payload.get("queue_sha256") != _sha256(queue):
        violations.append("QUEUE_SHA_MISMATCH")

    seen: set[tuple[str, str]] = set()
    valid_signals = {
        "EXACT_NORMALIZED_NAME_CITY",
        "TOKEN_SIGNATURE_EQUAL",
        "VERY_HIGH_NAME_SIMILARITY",
        "HIGH_TOKEN_OVERLAP",
    }
    for item in queue:
        if "action" in item or "resolution_action" in item:
            violations.append("QUEUE_MUST_NOT_ENCODE_RESOLUTION_ACTION")
        source_key = item.get("source_record_key")
        target = item.get("suggested_canonical_hotel_id")
        if not isinstance(source_key, str) or not source_key.strip():
            violations.append("INVALID_SOURCE_RECORD_KEY")
            continue
        if not isinstance(target, str) or not re.fullmatch(r"H-\d{4,}", target):
            violations.append("INVALID_SUGGESTED_CANONICAL_ID")
            continue
        pair = (source_key, target)
        if pair in seen:
            violations.append("DUPLICATE_REVIEW_PAIR")
        seen.add(pair)
        if _normalize_text(item.get("candidate_city")) != _normalize_text(
            item.get("canonical_city")
        ):
            violations.append("CROSS_CITY_REVIEW_PAIR_FORBIDDEN")
        signals = item.get("signals")
        if (
            not isinstance(signals, list)
            or not signals
            or any(signal not in valid_signals for signal in signals)
        ):
            violations.append("INVALID_SIGNAL_SET")
        if item.get("required_action") != "EVIDENCE_BACKED_EXPLICIT_REVIEW":
            violations.append("INVALID_REQUIRED_ACTION")
        if item.get("auto_merge_allowed") is not False:
            violations.append("PAIR_AUTO_MERGE_MUST_BE_FALSE")
        if item.get("terminal_mapping_allowed_from_queue") is not False:
            violations.append("PAIR_TERMINAL_MAPPING_MUST_BE_FALSE")

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        violations.append("SUMMARY_NOT_OBJECT")
    else:
        if summary.get("review_pairs") != len(queue):
            violations.append("REVIEW_PAIR_COUNT_MISMATCH")
        source_count = len(
            {str(item.get("source_record_key")) for item in queue}
        )
        if summary.get("review_source_records") != source_count:
            violations.append("REVIEW_SOURCE_COUNT_MISMATCH")
    return tuple(dict.fromkeys(violations))


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m swiss_os.canonical_match_review"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("candidate_export")
    build.add_argument("canonical_catalog")
    build.add_argument("--candidate-records-sha256", required=True)
    build.add_argument("--canonical-catalog-sha256", required=True)
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            candidate_export = _read_json(args.candidate_export)
            if not isinstance(candidate_export, Mapping):
                raise CanonicalMatchReviewError("candidate export must be an object")
            for key, expected in (
                ("authority_advanced", False),
                ("outbound", "CLOSED"),
            ):
                if candidate_export.get(key) != expected:
                    raise CanonicalMatchReviewError(
                        f"candidate export {key} must be {expected!r}"
                    )
            for key in ("h_id_allocations", "send_allowed"):
                value = candidate_export.get(key)
                if isinstance(value, bool) or value != 0:
                    raise CanonicalMatchReviewError(
                        f"candidate export {key} must be integer zero"
                    )
            records = candidate_export.get("records")
            if not isinstance(records, list):
                raise CanonicalMatchReviewError(
                    "candidate export records must be an array"
                )
            result = build_canonical_match_review_queue(
                snapshot_id=_text(candidate_export.get("snapshot_id")),
                candidate_records=records,
                canonical_catalog=_read_json(args.canonical_catalog),
                candidate_records_sha256=args.candidate_records_sha256,
                canonical_catalog_sha256=args.canonical_catalog_sha256,
            )
            _write_json(args.out, result)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "queue_sha256": result["queue_sha256"],
                        "summary": result["summary"],
                        "out": args.out,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        payload = _read_json(args.path)
        if not isinstance(payload, Mapping):
            raise CanonicalMatchReviewError("queue must be an object")
        violations = validate_canonical_match_review_queue(payload)
        print(
            json.dumps(
                {
                    "valid": not violations,
                    "violations": list(violations),
                    "queue_sha256": payload.get("queue_sha256"),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if not violations else 2
    except (CanonicalMatchReviewError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
