from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit


class SourceResolutionEvidenceTriageError(ValueError):
    """Raised when source-resolution evidence triage cannot be built safely."""


MATCH_EXISTING_REVIEW = "MATCH_EXISTING_REVIEW"
AMBIGUOUS_REVIEW = "AMBIGUOUS_REVIEW"
NOVELTY_REVIEW = "NOVELTY_REVIEW"
EVIDENCE_PENDING = "EVIDENCE_PENDING"

TRIAGE_STATES = (
    MATCH_EXISTING_REVIEW,
    AMBIGUOUS_REVIEW,
    NOVELTY_REVIEW,
    EVIDENCE_PENDING,
)
TERMINAL_MAPPING_STATES = frozenset(
    {"ACTIVE_CANONICAL", "ALIAS_TO_CANONICAL", "EXCLUDED_WITH_REASON"}
)


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", _text(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _normalize_url(value: object) -> str:
    raw = _text(value)
    if not raw:
        return ""
    parsed = urlsplit(raw)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    path = re.sub(r"/{2,}", "/", parsed.path or "/").rstrip("/") or "/"
    return urlunsplit((scheme, host, path, "", ""))


def _token_set(value: object) -> frozenset[str]:
    return frozenset(token for token in _normalize_text(value).split() if len(token) > 1)


def _jaccard_ppm(left: frozenset[str], right: frozenset[str]) -> int:
    if not left or not right:
        return 0
    union = left | right
    if not union:
        return 0
    return int(round((len(left & right) / len(union)) * 1_000_000))


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


def _require_mapping_payload(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise SourceResolutionEvidenceTriageError("mapping payload must be a JSON object")
    mappings = payload.get("mappings")
    if not isinstance(mappings, list) or not all(isinstance(item, Mapping) for item in mappings):
        raise SourceResolutionEvidenceTriageError("mapping payload must contain a mappings array")
    if payload.get("authority_advanced") not in (None, False):
        raise SourceResolutionEvidenceTriageError("authority_advanced must not be true")
    if payload.get("outbound") not in (None, "CLOSED"):
        raise SourceResolutionEvidenceTriageError("outbound must remain CLOSED")
    if payload.get("h_id_allocations") not in (None, 0):
        raise SourceResolutionEvidenceTriageError("h_id_allocations must remain zero")
    if payload.get("send_allowed") not in (None, 0):
        raise SourceResolutionEvidenceTriageError("send_allowed must remain zero")
    return payload


def _catalog(payload: object) -> list[Mapping[str, object]]:
    raw = payload.get("hotels") if isinstance(payload, Mapping) else payload
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise SourceResolutionEvidenceTriageError(
            "canonical catalog must be an array or an object containing hotels"
        )
    seen: set[str] = set()
    active: list[Mapping[str, object]] = []
    for item in raw:
        hotel_id = _text(item.get("hotel_id"))
        if not re.fullmatch(r"H-\d{4,}", hotel_id):
            raise SourceResolutionEvidenceTriageError(f"invalid canonical hotel_id: {hotel_id}")
        if hotel_id in seen:
            raise SourceResolutionEvidenceTriageError(f"duplicate canonical hotel_id: {hotel_id}")
        seen.add(hotel_id)
        is_active = item.get("is_active")
        if not isinstance(is_active, bool):
            raise SourceResolutionEvidenceTriageError(
                f"catalog is_active must be boolean for {hotel_id}"
            )
        if is_active:
            active.append(item)
    return active


def _indexes(
    active: Sequence[Mapping[str, object]],
) -> tuple[
    dict[str, list[Mapping[str, object]]],
    dict[tuple[str, str], list[Mapping[str, object]]],
    dict[str, list[Mapping[str, object]]],
    dict[str, list[Mapping[str, object]]],
]:
    by_detail: dict[str, list[Mapping[str, object]]] = {}
    by_name_city: dict[tuple[str, str], list[Mapping[str, object]]] = {}
    by_name: dict[str, list[Mapping[str, object]]] = {}
    by_city: dict[str, list[Mapping[str, object]]] = {}
    for item in active:
        detail = _normalize_url(item.get("detail_url") or item.get("hotelleriesuisse_url"))
        name = _normalize_text(item.get("name") or item.get("canonical_name"))
        city = _normalize_text(item.get("city"))
        if detail:
            by_detail.setdefault(detail, []).append(item)
        if name and city:
            by_name_city.setdefault((name, city), []).append(item)
        if name:
            by_name.setdefault(name, []).append(item)
        if city:
            by_city.setdefault(city, []).append(item)
    return by_detail, by_name_city, by_name, by_city


def _suggestions(
    source: Mapping[str, object],
    by_city: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    limit: int = 3,
    minimum_score_ppm: int = 350_000,
) -> list[dict[str, object]]:
    city = _normalize_text(source.get("city"))
    source_tokens = _token_set(source.get("name"))
    candidates: list[tuple[int, str, Mapping[str, object]]] = []
    for item in by_city.get(city, ()) if city else ():
        score = _jaccard_ppm(source_tokens, _token_set(item.get("name") or item.get("canonical_name")))
        if score >= minimum_score_ppm:
            candidates.append((score, _text(item.get("hotel_id")), item))
    candidates.sort(key=lambda row: (-row[0], row[1]))
    return [
        {
            "hotel_id": hotel_id,
            "name": _text(item.get("name") or item.get("canonical_name")),
            "city": _text(item.get("city")),
            "token_jaccard_ppm": score,
            "evidence_role": "REVIEW_SPACE_REDUCTION_ONLY",
        }
        for score, hotel_id, item in candidates[:limit]
    ]


def _ids(items: Sequence[Mapping[str, object]]) -> list[str]:
    return sorted(_text(item.get("hotel_id")) for item in items)


def build_evidence_triage(
    mapping_payload: object,
    canonical_catalog: object,
) -> dict[str, object]:
    """Classify unresolved source records without producing terminal authority decisions.

    Exact identity signals may create MATCH_EXISTING_REVIEW work, but never a mapping.
    Current verification without an exact signal creates NOVELTY_REVIEW, not NEW_CANONICAL.
    Token similarity is suggestion-only and cannot change the triage state.
    """

    payload = _require_mapping_payload(mapping_payload)
    active = _catalog(canonical_catalog)
    by_detail, by_name_city, by_name, by_city = _indexes(active)
    raw_mappings = payload["mappings"]
    assert isinstance(raw_mappings, list)

    keys: set[str] = set()
    items: list[dict[str, object]] = []
    carried_terminal = 0
    for source in sorted(raw_mappings, key=lambda item: _text(item.get("source_record_key"))):
        assert isinstance(source, Mapping)
        key = _text(source.get("source_record_key"))
        if not key:
            raise SourceResolutionEvidenceTriageError("empty source_record_key")
        if key in keys:
            raise SourceResolutionEvidenceTriageError(f"duplicate source_record_key: {key}")
        keys.add(key)
        mapping_state = _text(source.get("mapping_state"))
        if mapping_state in TERMINAL_MAPPING_STATES:
            carried_terminal += 1
            continue
        if mapping_state != "RECONCILE_REQUIRED":
            raise SourceResolutionEvidenceTriageError(
                f"unsupported mapping_state for {key}: {mapping_state or '<empty>'}"
            )

        detail = _normalize_url(source.get("detail_url"))
        name = _normalize_text(source.get("name"))
        city = _normalize_text(source.get("city"))
        exact_detail = list(by_detail.get(detail, ())) if detail else []
        exact_name_city = list(by_name_city.get((name, city), ())) if name and city else []
        global_name = list(by_name.get(name, ())) if name else []

        exact_ids: list[str] = []
        if len(exact_detail) == 1:
            state = MATCH_EXISTING_REVIEW
            reason = "UNIQUE_EXACT_DETAIL_URL_SIGNAL_REVIEW_REQUIRED"
            exact_ids = _ids(exact_detail)
        elif len(exact_detail) > 1:
            state = AMBIGUOUS_REVIEW
            reason = "AMBIGUOUS_EXACT_DETAIL_URL_SIGNAL"
            exact_ids = _ids(exact_detail)
        elif len(exact_name_city) == 1:
            state = MATCH_EXISTING_REVIEW
            reason = "UNIQUE_EXACT_NAME_CITY_SIGNAL_REVIEW_REQUIRED"
            exact_ids = _ids(exact_name_city)
        elif len(exact_name_city) > 1:
            state = AMBIGUOUS_REVIEW
            reason = "AMBIGUOUS_EXACT_NAME_CITY_SIGNAL"
            exact_ids = _ids(exact_name_city)
        elif global_name:
            state = AMBIGUOUS_REVIEW
            reason = "EXACT_NAME_LOCALITY_CONFLICT_OR_VARIANT_REVIEW_REQUIRED"
            exact_ids = _ids(global_name)
        elif source.get("current_evidence_verified") is True:
            state = NOVELTY_REVIEW
            reason = "CURRENT_VERIFIED_NO_EXACT_IDENTITY_SIGNAL_DISTINCTNESS_UNPROVEN"
        else:
            state = EVIDENCE_PENDING
            reason = "CURRENT_EXACT_EVIDENCE_REQUIRED_BEFORE_IDENTITY_CLASSIFICATION"

        items.append(
            {
                "source_record_key": key,
                "name": _text(source.get("name")),
                "city": _text(source.get("city")),
                "detail_url": _text(source.get("detail_url")),
                "triage_state": state,
                "reason_code": reason,
                "current_evidence_verified": source.get("current_evidence_verified") is True,
                "exact_signal_hotel_ids": exact_ids,
                "candidate_suggestions": _suggestions(source, by_city),
                "terminal_mapping_allowed": False,
                "canonical_id_reservation_allowed": False,
                "authority_action": "NONE",
            }
        )

    counts = {state: sum(1 for item in items if item["triage_state"] == state) for state in TRIAGE_STATES}
    result: dict[str, object] = {
        "schema_version": "SOURCE-RESOLUTION-EVIDENCE-TRIAGE-1.0",
        "snapshot_id": payload.get("snapshot_id"),
        "source_manifest_sha256": payload.get("source_manifest_sha256"),
        "source_mapping_parent_sha256": payload.get("candidate_sha256")
        or payload.get("review_sha256")
        or payload.get("mapping_sha256")
        or "",
        "source_records": len(raw_mappings),
        "carried_terminal_mappings": carried_terminal,
        "triage_records": len(items),
        "counts_by_triage_state": counts,
        "items": items,
        "items_sha256": _sha256(items),
        "review_only": True,
        "terminal_mapping_allowed": False,
        "canonical_id_reservation_allowed": False,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "crm_universe_complete": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "triage_sha256": "",
    }
    result["triage_sha256"] = _sha256(
        {key: value for key, value in result.items() if key != "triage_sha256"}
    )
    return result


def validate_evidence_triage(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != "SOURCE-RESOLUTION-EVIDENCE-TRIAGE-1.0":
        violations.append("INVALID_SCHEMA_VERSION")
    strict_false = (
        "terminal_mapping_allowed",
        "canonical_id_reservation_allowed",
        "authority_advanced",
        "crm_universe_complete",
    )
    for key in strict_false:
        if payload.get(key) is not False:
            violations.append(f"INVALID_{key.upper()}")
    if payload.get("review_only") is not True:
        violations.append("REVIEW_ONLY_REQUIRED")
    if payload.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")
    for key in ("h_id_allocations", "send_allowed"):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != 0:
            violations.append(f"INVALID_{key.upper()}")

    items = payload.get("items")
    if not isinstance(items, list) or not all(isinstance(item, Mapping) for item in items):
        violations.append("ITEMS_NOT_ARRAY_OF_OBJECTS")
        items = []
    keys: set[str] = set()
    for item in items:
        assert isinstance(item, Mapping)
        key = _text(item.get("source_record_key"))
        if not key:
            violations.append("EMPTY_SOURCE_RECORD_KEY")
        elif key in keys:
            violations.append("DUPLICATE_SOURCE_RECORD_KEY")
        keys.add(key)
        if item.get("triage_state") not in TRIAGE_STATES:
            violations.append("INVALID_TRIAGE_STATE")
        if item.get("terminal_mapping_allowed") is not False:
            violations.append("ITEM_TERMINAL_MAPPING_FORBIDDEN")
        if item.get("canonical_id_reservation_allowed") is not False:
            violations.append("ITEM_CANONICAL_ID_RESERVATION_FORBIDDEN")
        if item.get("authority_action") != "NONE":
            violations.append("ITEM_AUTHORITY_ACTION_FORBIDDEN")
        if _text(item.get("canonical_hotel_id")) or _text(item.get("allocated_hotel_id")):
            violations.append("ITEM_CANONICAL_TARGET_FORBIDDEN")
        suggestions = item.get("candidate_suggestions")
        if not isinstance(suggestions, list):
            violations.append("SUGGESTIONS_NOT_ARRAY")
        else:
            for suggestion in suggestions:
                if not isinstance(suggestion, Mapping):
                    violations.append("SUGGESTION_NOT_OBJECT")
                    continue
                if suggestion.get("evidence_role") != "REVIEW_SPACE_REDUCTION_ONLY":
                    violations.append("SUGGESTION_ROLE_INVALID")

    if payload.get("triage_records") != len(items):
        violations.append("TRIAGE_RECORD_COUNT_MISMATCH")
    source_records = payload.get("source_records")
    carried = payload.get("carried_terminal_mappings")
    if not isinstance(source_records, int) or not isinstance(carried, int):
        violations.append("INVALID_SOURCE_COUNTS")
    elif source_records != carried + len(items):
        violations.append("SOURCE_COUNT_PARTITION_MISMATCH")
    counts = payload.get("counts_by_triage_state")
    expected_counts = {
        state: sum(1 for item in items if item.get("triage_state") == state)
        for state in TRIAGE_STATES
    }
    if counts != expected_counts:
        violations.append("TRIAGE_STATE_COUNT_MISMATCH")
    if payload.get("items_sha256") != _sha256(items):
        violations.append("ITEMS_SHA_MISMATCH")
    expected_sha = _sha256(
        {key: value for key, value in payload.items() if key != "triage_sha256"}
    )
    if payload.get("triage_sha256") != expected_sha:
        violations.append("TRIAGE_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.source_resolution_evidence_triage")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("mapping_payload")
    build.add_argument("canonical_catalog")
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_evidence_triage(
                _read_json(args.mapping_payload), _read_json(args.canonical_catalog)
            )
            violations = validate_evidence_triage(result)
            if violations:
                raise SourceResolutionEvidenceTriageError(
                    "generated triage failed validation: " + ", ".join(violations)
                )
            _write_json(args.out, result)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "source_records": result["source_records"],
                        "carried_terminal_mappings": result["carried_terminal_mappings"],
                        "triage_records": result["triage_records"],
                        "counts_by_triage_state": result["counts_by_triage_state"],
                        "triage_sha256": result["triage_sha256"],
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
        raw = _read_json(args.path)
        if not isinstance(raw, Mapping):
            raise SourceResolutionEvidenceTriageError("triage payload must be an object")
        violations = validate_evidence_triage(raw)
        print(json.dumps({"valid": not violations, "violations": list(violations)}, indent=2, sort_keys=True))
        return 0 if not violations else 2
    except (SourceResolutionEvidenceTriageError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
