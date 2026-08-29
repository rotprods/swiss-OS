from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .source_resolution import (
    ALLOWED_ACTIONS,
    NEW_CANONICAL,
    TERMINAL_MAPPING_STATES,
    UNRESOLVED,
    SourceResolutionError,
    _normalize_text,
    _sha256,
    build_resolution_review,
    validate_resolution_review,
)

SCHEMA_VERSION = "BATCH-SAFE-SOURCE-RESOLUTION-1.0"
DUPLICATE_RISK_RULE_VERSION = "SAME-CITY-DUPLICATE-RISK-1.0"

# Terms that cannot establish entity identity by themselves. A candidate must
# share at least one non-generic token before similarity can trigger review.
_GENERIC_TOKENS = frozenset(
    {
        "hotel",
        "hotels",
        "boutique",
        "resort",
        "spa",
        "restaurant",
        "hostel",
        "lodge",
        "apart",
        "aparthotel",
        "gasthof",
        "pension",
        "garni",
        "swiss",
        "quality",
    }
)


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _catalog_rows(payload: object) -> list[Mapping[str, object]]:
    raw = payload.get("hotels") if isinstance(payload, Mapping) else payload
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise SourceResolutionError(
            "canonical catalog must be an array or object with hotels array"
        )
    return list(raw)


def _tokens(value: object) -> frozenset[str]:
    return frozenset(token for token in _normalize_text(value).split() if token)


def _duplicate_risk(
    source_name: object,
    canonical_name: object,
) -> dict[str, object] | None:
    left = _normalize_text(source_name)
    right = _normalize_text(canonical_name)
    if not left or not right or left == right:
        return None

    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    shared = left_tokens & right_tokens
    shared_identity = shared - _GENERIC_TOKENS
    if not shared_identity:
        return None

    union = left_tokens | right_tokens
    jaccard = 0.0 if not union else len(shared) / len(union)
    sequence = SequenceMatcher(None, left, right).ratio()
    subset_variant = (
        min(len(left_tokens), len(right_tokens)) >= 2
        and (left_tokens <= right_tokens or right_tokens <= left_tokens)
        and abs(len(left_tokens) - len(right_tokens)) <= 2
    )
    strong_overlap = jaccard >= 0.80 and sequence >= 0.86
    if not (subset_variant or strong_overlap):
        return None

    return {
        "rule_version": DUPLICATE_RISK_RULE_VERSION,
        "sequence_similarity": round(sequence, 6),
        "token_jaccard": round(jaccard, 6),
        "shared_identity_tokens": sorted(shared_identity),
        "subset_variant": subset_variant,
    }


def _active_catalog_by_city(
    canonical_catalog: object,
) -> dict[str, list[dict[str, object]]]:
    by_city: dict[str, list[dict[str, object]]] = {}
    for row in _catalog_rows(canonical_catalog):
        hotel_id = str(row.get("hotel_id", "")).strip()
        active = row.get("is_active")
        if active is not True:
            continue
        name = str(row.get("name") or row.get("canonical_name") or "").strip()
        city = str(row.get("city") or "").strip()
        if not hotel_id or not name or not city:
            continue
        by_city.setdefault(_normalize_text(city), []).append(
            {"hotel_id": hotel_id, "name": name, "city": city}
        )
    for rows in by_city.values():
        rows.sort(key=lambda item: str(item["hotel_id"]))
    return by_city


def _risk_candidates(
    mapping: Mapping[str, object],
    by_city: Mapping[str, Sequence[Mapping[str, object]]],
) -> list[dict[str, object]]:
    city = _normalize_text(mapping.get("city"))
    source_name = mapping.get("name")
    candidates: list[dict[str, object]] = []
    for canonical in by_city.get(city, ()):
        risk = _duplicate_risk(source_name, canonical.get("name"))
        if risk is None:
            continue
        candidates.append(
            {
                "canonical_hotel_id": str(canonical.get("hotel_id", "")),
                "canonical_name": str(canonical.get("name", "")),
                **risk,
            }
        )
    candidates.sort(
        key=lambda item: (
            -float(item["sequence_similarity"]),
            -float(item["token_jaccard"]),
            str(item["canonical_hotel_id"]),
        )
    )
    return candidates


def _refresh_summary(result: dict[str, object]) -> None:
    raw = result.get("mappings")
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise SourceResolutionError("resolution mappings must be an array of objects")
    mappings = list(raw)
    counts = {
        state: sum(1 for item in mappings if item.get("mapping_state") == state)
        for state in (
            "ACTIVE_CANONICAL",
            "ALIAS_TO_CANONICAL",
            "EXCLUDED_WITH_REASON",
            "RECONCILE_REQUIRED",
        )
    }
    action_counts = {
        action: sum(1 for item in mappings if item.get("resolution_action") == action)
        for action in sorted(ALLOWED_ACTIONS)
    }
    terminal = sum(counts[state] for state in TERMINAL_MAPPING_STATES)
    unresolved = action_counts[UNRESOLVED]
    result["counts_by_mapping_state"] = counts
    result["counts_by_resolution_action"] = action_counts
    result["terminal_mappings_candidate"] = terminal
    result["new_canonical_candidates"] = action_counts[NEW_CANONICAL]
    result["unresolved_review"] = unresolved
    result["reconcile_required_after_review"] = counts["RECONCILE_REQUIRED"]
    result["terminal_mapping_coverage_pct"] = 0.0 if not mappings else terminal / len(mappings)
    result["authority_batch_ready"] = unresolved == 0
    result["review_decision_complete"] = unresolved == 0 and all(
        item.get("resolution_action") not in {"", None}
        for item in mappings
        if item.get("mapping_state") == "RECONCILE_REQUIRED"
    )
    result["mappings_sha256"] = _sha256(mappings)
    result["review_sha256"] = _sha256(
        {key: value for key, value in result.items() if key != "review_sha256"}
    )


def build_batch_safe_resolution_review(
    smc_payload: object,
    canonical_catalog: object,
    reviews: object | None = None,
    *,
    expected_snapshot_id: str | None = None,
) -> dict[str, object]:
    """Build SRR with a fail-closed duplicate-risk barrier before NEW_CANONICAL.

    Exact matching and explicit-review validation stay delegated to SRR-1.1.
    This layer never fuzzy-binds a source to a canonical hotel. Similarity is
    used only to convert an automatic NEW_CANONICAL proposal into UNRESOLVED
    and attach deterministic review candidates.
    """

    if expected_snapshot_id is not None:
        if not isinstance(smc_payload, Mapping):
            raise SourceResolutionError("SMC candidate must be a JSON object")
        actual_snapshot = smc_payload.get("snapshot_id")
        if actual_snapshot != expected_snapshot_id:
            raise SourceResolutionError(
                "snapshot mismatch: "
                f"expected {expected_snapshot_id!r}, got {actual_snapshot!r}"
            )

    result = build_resolution_review(smc_payload, canonical_catalog, reviews)
    by_city = _active_catalog_by_city(canonical_catalog)
    mappings = result.get("mappings")
    assert isinstance(mappings, list)

    converted = 0
    for raw in mappings:
        if not isinstance(raw, dict):
            continue
        if raw.get("resolution_action") != NEW_CANONICAL:
            continue
        if raw.get("resolution_origin") != "AUTO_PROPOSED":
            continue
        candidates = _risk_candidates(raw, by_city)
        if not candidates:
            continue
        converted += 1
        raw["resolution_action"] = UNRESOLVED
        raw["mapping_state"] = "RECONCILE_REQUIRED"
        raw["canonical_hotel_id"] = ""
        raw["resolution_reason_code"] = "SAME_CITY_DUPLICATE_RISK_REVIEW_REQUIRED"
        raw["authority_action"] = "RESEARCH_OR_MANUAL_REVIEW_REQUIRED"
        raw["resolution_candidate_hotel_ids"] = [
            item["canonical_hotel_id"] for item in candidates
        ]
        raw["resolution_duplicate_risk_candidates"] = candidates

    result["batch_safe_resolver"] = {
        "schema_version": SCHEMA_VERSION,
        "duplicate_risk_rule_version": DUPLICATE_RISK_RULE_VERSION,
        "converted_new_canonical_to_unresolved": converted,
        "fuzzy_autobind_allowed": False,
        "authority_mutation_allowed": False,
        "canonical_id_reservation_allowed": False,
    }
    _refresh_summary(result)
    violations = validate_batch_safe_resolution_review(result, canonical_catalog)
    if violations:
        raise SourceResolutionError(
            "batch-safe resolution validation failed: " + ", ".join(violations)
        )
    return result


def validate_batch_safe_resolution_review(
    payload: Mapping[str, object],
    canonical_catalog: object,
) -> tuple[str, ...]:
    violations = list(validate_resolution_review(payload))
    safety = payload.get("batch_safe_resolver")
    if not isinstance(safety, Mapping):
        violations.append("BATCH_SAFE_METADATA_MISSING")
    else:
        if safety.get("schema_version") != SCHEMA_VERSION:
            violations.append("INVALID_BATCH_SAFE_SCHEMA")
        if safety.get("duplicate_risk_rule_version") != DUPLICATE_RISK_RULE_VERSION:
            violations.append("INVALID_DUPLICATE_RISK_RULE_VERSION")
        if safety.get("fuzzy_autobind_allowed") is not False:
            violations.append("FUZZY_AUTOBIND_MUST_BE_FALSE")
        if safety.get("authority_mutation_allowed") is not False:
            violations.append("AUTHORITY_MUTATION_MUST_BE_FALSE")
        if safety.get("canonical_id_reservation_allowed") is not False:
            violations.append("CANONICAL_ID_RESERVATION_MUST_BE_FALSE")

    by_city = _active_catalog_by_city(canonical_catalog)
    mappings = payload.get("mappings")
    if not isinstance(mappings, list):
        mappings = []
    converted = 0
    for raw in mappings:
        if not isinstance(raw, Mapping):
            continue
        candidates = _risk_candidates(raw, by_city)
        action = raw.get("resolution_action")
        origin = raw.get("resolution_origin")
        if action == NEW_CANONICAL and origin == "AUTO_PROPOSED" and candidates:
            violations.append("AUTO_NEW_CANONICAL_HAS_SAME_CITY_DUPLICATE_RISK")
        if raw.get("resolution_reason_code") == "SAME_CITY_DUPLICATE_RISK_REVIEW_REQUIRED":
            converted += 1
            if action != UNRESOLVED:
                violations.append("DUPLICATE_RISK_MUST_BE_UNRESOLVED")
            expected_ids = [item["canonical_hotel_id"] for item in candidates]
            if raw.get("resolution_candidate_hotel_ids") != expected_ids:
                violations.append("DUPLICATE_RISK_CANDIDATE_IDS_MISMATCH")
            if raw.get("canonical_hotel_id") not in {"", None}:
                violations.append("DUPLICATE_RISK_MUST_NOT_BIND_CANONICAL")
    if isinstance(safety, Mapping) and safety.get(
        "converted_new_canonical_to_unresolved"
    ) != converted:
        violations.append("DUPLICATE_RISK_CONVERTED_COUNT_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.source_resolution_batch_safe")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("smc_candidate")
    build.add_argument("canonical_catalog")
    build.add_argument("--reviews")
    build.add_argument("--expected-snapshot-id")
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    validate.add_argument("canonical_catalog")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_batch_safe_resolution_review(
                _read_json(args.smc_candidate),
                _read_json(args.canonical_catalog),
                _read_json(args.reviews) if args.reviews else None,
                expected_snapshot_id=args.expected_snapshot_id,
            )
            _write_json(args.out, result)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "snapshot_id": result["snapshot_id"],
                        "source_records": result["source_records"],
                        "counts_by_resolution_action": result[
                            "counts_by_resolution_action"
                        ],
                        "unresolved_review": result["unresolved_review"],
                        "new_canonical_candidates": result[
                            "new_canonical_candidates"
                        ],
                        "batch_safe_resolver": result["batch_safe_resolver"],
                        "authority_advanced": False,
                        "h_id_allocations": 0,
                        "outbound": "CLOSED",
                        "send_allowed": 0,
                        "review_sha256": result["review_sha256"],
                        "out": args.out,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        raw = _read_json(args.path)
        if not isinstance(raw, Mapping):
            raise SourceResolutionError("resolution review must be a JSON object")
        violations = validate_batch_safe_resolution_review(
            raw, _read_json(args.canonical_catalog)
        )
        print(
            json.dumps(
                {
                    "valid": not violations,
                    "violations": list(violations),
                    "review_sha256": raw.get("review_sha256"),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if not violations else 2
    except (SourceResolutionError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
