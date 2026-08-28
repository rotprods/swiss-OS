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

from .source_mapping import validate_source_mapping_candidate


class SourceResolutionError(ValueError):
    """Raised when an SMC candidate cannot be resolved safely."""


MATCH_EXISTING = "MATCH_EXISTING"
ALIAS_EXISTING = "ALIAS_EXISTING"
EXCLUDE = "EXCLUDE"
NEW_CANONICAL = "NEW_CANONICAL"
UNRESOLVED = "UNRESOLVED"
CARRY_TERMINAL = "CARRY_TERMINAL"

ALLOWED_ACTIONS = frozenset(
    {MATCH_EXISTING, ALIAS_EXISTING, EXCLUDE, NEW_CANONICAL, UNRESOLVED}
)
TERMINAL_MAPPING_STATES = frozenset(
    {"ACTIVE_CANONICAL", "ALIAS_TO_CANONICAL", "EXCLUDED_WITH_REASON"}
)
ALL_MAPPING_STATES = TERMINAL_MAPPING_STATES | {"RECONCILE_REQUIRED"}


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


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


def _text(value: object) -> str:
    return str(value or "").strip()


def _string_field(
    payload: Mapping[str, object],
    key: str,
    *,
    required: bool = False,
) -> str:
    if key not in payload or payload.get(key) is None:
        if required:
            raise SourceResolutionError(f"{key} must be a non-empty string")
        return ""
    value = payload.get(key)
    if not isinstance(value, str):
        raise SourceResolutionError(f"{key} must be a string")
    text = value.strip()
    if required and not text:
        raise SourceResolutionError(f"{key} must be a non-empty string")
    return text


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
    if parsed.port:
        host = f"{host}:{parsed.port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/").rstrip("/") or "/"
    return urlunsplit((scheme, host, path, "", ""))


def _strict_bool(payload: Mapping[str, object], key: str, expected: bool) -> None:
    value = payload.get(key)
    if not isinstance(value, bool) or value is not expected:
        raise SourceResolutionError(f"{key} must be exactly {expected}")


def _strict_zero_int(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise SourceResolutionError(f"{key} must be integer 0")


def _require_smc(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise SourceResolutionError("SMC candidate must be a JSON object")
    _strict_bool(payload, "crm_universe_complete", False)
    _strict_bool(payload, "authority_advanced", False)
    _strict_zero_int(payload, "h_id_allocations")
    if payload.get("outbound") != "CLOSED":
        raise SourceResolutionError("SMC outbound must be CLOSED")
    _strict_zero_int(payload, "send_allowed")
    violations = validate_source_mapping_candidate(payload)
    if violations:
        raise SourceResolutionError("invalid SMC candidate: " + ", ".join(violations))
    return payload


def _catalog_index(
    payload: object,
) -> tuple[
    dict[str, Mapping[str, object]],
    dict[tuple[str, str], list[str]],
    dict[str, list[str]],
]:
    if isinstance(payload, Mapping):
        raw = payload.get("hotels")
    else:
        raw = payload
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise SourceResolutionError(
            "canonical catalog must be an array or object with hotels array"
        )

    by_id: dict[str, Mapping[str, object]] = {}
    by_name_city: dict[tuple[str, str], list[str]] = {}
    by_detail: dict[str, list[str]] = {}
    for item in raw:
        hotel_id = _text(item.get("hotel_id"))
        if not re.fullmatch(r"H-\d{4,}", hotel_id):
            raise SourceResolutionError(
                f"invalid canonical hotel_id: {hotel_id or '<empty>'}"
            )
        if "is_active" not in item:
            raise SourceResolutionError(
                f"catalog is_active must be explicitly present for {hotel_id}"
            )
        active = item.get("is_active")
        if not isinstance(active, bool):
            raise SourceResolutionError(
                f"catalog is_active must be boolean for {hotel_id}"
            )
        if hotel_id in by_id:
            raise SourceResolutionError(f"duplicate canonical hotel_id: {hotel_id}")
        by_id[hotel_id] = item
        if not active:
            continue
        name_city = (
            _normalize_text(item.get("name") or item.get("canonical_name")),
            _normalize_text(item.get("city")),
        )
        if all(name_city):
            by_name_city.setdefault(name_city, []).append(hotel_id)
        detail = _normalize_url(
            item.get("detail_url") or item.get("hotelleriesuisse_url")
        )
        if detail:
            by_detail.setdefault(detail, []).append(hotel_id)
    return by_id, by_name_city, by_detail


def _review_index(payload: object | None) -> dict[str, Mapping[str, object]]:
    if payload is None:
        return {}
    if not isinstance(payload, list) or not all(
        isinstance(item, Mapping) for item in payload
    ):
        raise SourceResolutionError("reviews must be an array of objects")
    out: dict[str, Mapping[str, object]] = {}
    for item in payload:
        key = _string_field(item, "source_record_key", required=True)
        if key in out:
            raise SourceResolutionError(f"duplicate review source_record_key: {key}")
        action = _string_field(item, "action", required=True).upper()
        if action not in ALLOWED_ACTIONS:
            raise SourceResolutionError(
                f"invalid resolution action for {key}: {action}"
            )
        _string_field(item, "canonical_hotel_id")
        _string_field(item, "reason_code", required=True)
        _string_field(item, "evidence_ref", required=True)
        out[key] = item
    return out


def _auto_proposal(
    mapping: Mapping[str, object],
    by_name_city: Mapping[tuple[str, str], Sequence[str]],
    by_detail: Mapping[str, Sequence[str]],
) -> dict[str, str]:
    detail = _normalize_url(mapping.get("detail_url"))
    detail_matches = list(by_detail.get(detail, ())) if detail else []
    if len(detail_matches) == 1:
        return {
            "action": MATCH_EXISTING,
            "canonical_hotel_id": detail_matches[0],
            "reason_code": "UNIQUE_EXACT_DETAIL_URL_MATCH",
            "evidence_ref": _text(mapping.get("evidence_ref")) or "SMC_EVIDENCE",
            "review_origin": "AUTO_PROPOSED",
        }
    if len(detail_matches) > 1:
        return {
            "action": UNRESOLVED,
            "canonical_hotel_id": "",
            "reason_code": "AMBIGUOUS_EXACT_DETAIL_URL_MATCH",
            "evidence_ref": _text(mapping.get("evidence_ref")) or "SMC_EVIDENCE",
            "review_origin": "AUTO_PROPOSED",
        }

    name_city = (
        _normalize_text(mapping.get("name")),
        _normalize_text(mapping.get("city")),
    )
    name_city_matches = list(by_name_city.get(name_city, ())) if all(name_city) else []
    if len(name_city_matches) == 1:
        return {
            "action": MATCH_EXISTING,
            "canonical_hotel_id": name_city_matches[0],
            "reason_code": "UNIQUE_EXACT_NAME_CITY_MATCH",
            "evidence_ref": _text(mapping.get("evidence_ref")) or "SMC_EVIDENCE",
            "review_origin": "AUTO_PROPOSED",
        }
    if len(name_city_matches) > 1:
        return {
            "action": UNRESOLVED,
            "canonical_hotel_id": "",
            "reason_code": "AMBIGUOUS_EXACT_NAME_CITY_MATCH",
            "evidence_ref": _text(mapping.get("evidence_ref")) or "SMC_EVIDENCE",
            "review_origin": "AUTO_PROPOSED",
        }
    if mapping.get("current_evidence_verified") is True:
        return {
            "action": NEW_CANONICAL,
            "canonical_hotel_id": "",
            "reason_code": "CURRENT_VERIFIED_NO_CANONICAL_MATCH",
            "evidence_ref": _text(mapping.get("evidence_ref")) or "SMC_EVIDENCE",
            "review_origin": "AUTO_PROPOSED",
        }
    return {
        "action": UNRESOLVED,
        "canonical_hotel_id": "",
        "reason_code": "CURRENT_EVIDENCE_NOT_VERIFIED",
        "evidence_ref": _text(mapping.get("evidence_ref"))
        or "EXACT_CURRENT_EVIDENCE_PENDING",
        "review_origin": "AUTO_PROPOSED",
    }


def _explicit_review(item: Mapping[str, object]) -> dict[str, str]:
    return {
        "action": _string_field(item, "action", required=True).upper(),
        "canonical_hotel_id": _string_field(item, "canonical_hotel_id"),
        "reason_code": _string_field(item, "reason_code", required=True),
        "evidence_ref": _string_field(item, "evidence_ref", required=True),
        "review_origin": "EXPLICIT_REVIEW",
    }


def _validate_review(
    source: Mapping[str, object],
    review: Mapping[str, str],
    catalog: Mapping[str, Mapping[str, object]],
) -> None:
    action = review["action"]
    target = review["canonical_hotel_id"]
    if not review["reason_code"]:
        raise SourceResolutionError(
            f"review reason_code required for {source.get('source_record_key')}"
        )
    if not review["evidence_ref"]:
        raise SourceResolutionError(
            f"review evidence_ref required for {source.get('source_record_key')}"
        )
    if action in {MATCH_EXISTING, ALIAS_EXISTING}:
        if not target:
            raise SourceResolutionError(f"canonical target required for {action}")
        target_payload = catalog.get(target)
        if target_payload is None or target_payload.get("is_active") is not True:
            raise SourceResolutionError(
                f"canonical target must exist and be active: {target}"
            )
        if source.get("current_evidence_verified") is not True:
            raise SourceResolutionError(
                f"current exact evidence required before {action}: "
                f"{source.get('source_record_key')}"
            )
    elif target:
        raise SourceResolutionError(f"canonical target forbidden for {action}")
    if action == NEW_CANONICAL and source.get("current_evidence_verified") is not True:
        raise SourceResolutionError(
            "current exact evidence required before NEW_CANONICAL: "
            f"{source.get('source_record_key')}"
        )


def build_resolution_review(
    smc_payload: object,
    canonical_catalog: object,
    reviews: object | None = None,
) -> dict[str, object]:
    smc = _require_smc(smc_payload)
    catalog, by_name_city, by_detail = _catalog_index(canonical_catalog)
    review_index = _review_index(reviews)
    mappings = smc.get("mappings")
    assert isinstance(mappings, list)
    source_index = {
        _text(item.get("source_record_key")): item
        for item in mappings
        if isinstance(item, Mapping)
    }
    extra_reviews = sorted(set(review_index) - set(source_index))
    if extra_reviews:
        raise SourceResolutionError(
            "reviews contain unknown source keys: " + ", ".join(extra_reviews[:10])
        )
    terminal_review_keys = sorted(
        key
        for key in review_index
        if source_index[key].get("mapping_state") != "RECONCILE_REQUIRED"
    )
    if terminal_review_keys:
        raise SourceResolutionError(
            "reviews may only target RECONCILE_REQUIRED mappings: "
            + ", ".join(terminal_review_keys[:10])
        )

    output: list[dict[str, object]] = []
    reviewed_reconcile = 0
    for source in sorted(
        (item for item in mappings if isinstance(item, Mapping)),
        key=lambda item: _text(item.get("source_record_key")),
    ):
        key = _text(source.get("source_record_key"))
        if source.get("mapping_state") != "RECONCILE_REQUIRED":
            carried = dict(source)
            carried["resolution_action"] = CARRY_TERMINAL
            carried["resolution_origin"] = "SMC_TERMINAL"
            carried["authority_action"] = "NONE"
            output.append(carried)
            continue

        raw_review = review_index.get(key)
        review = (
            _explicit_review(raw_review)
            if raw_review
            else _auto_proposal(source, by_name_city, by_detail)
        )
        _validate_review(source, review, catalog)
        if raw_review:
            reviewed_reconcile += 1
        action = review["action"]
        target = review["canonical_hotel_id"]
        resolved = dict(source)
        resolved.update(
            {
                "resolution_action": action,
                "resolution_origin": review["review_origin"],
                "resolution_reason_code": review["reason_code"],
                "resolution_evidence_ref": review["evidence_ref"],
                "authority_action": "NONE",
            }
        )
        if action == MATCH_EXISTING:
            resolved["mapping_state"] = "ACTIVE_CANONICAL"
            resolved["canonical_hotel_id"] = target
            resolved["authority_action"] = "MAP_EXISTING_ON_AUTHORITY_COMMIT"
        elif action == ALIAS_EXISTING:
            resolved["mapping_state"] = "ALIAS_TO_CANONICAL"
            resolved["canonical_hotel_id"] = target
            resolved["authority_action"] = "CREATE_ALIAS_MAPPING_ON_AUTHORITY_COMMIT"
        elif action == EXCLUDE:
            resolved["mapping_state"] = "EXCLUDED_WITH_REASON"
            resolved["canonical_hotel_id"] = ""
            resolved["authority_action"] = "PERSIST_EXCLUSION_ON_AUTHORITY_COMMIT"
        elif action == NEW_CANONICAL:
            resolved["mapping_state"] = "RECONCILE_REQUIRED"
            resolved["canonical_hotel_id"] = ""
            resolved["authority_action"] = "ALLOCATE_NEW_CANONICAL_ON_AUTHORITY_COMMIT"
        else:
            resolved["mapping_state"] = "RECONCILE_REQUIRED"
            resolved["canonical_hotel_id"] = ""
            resolved["authority_action"] = "RESEARCH_OR_MANUAL_REVIEW_REQUIRED"
        output.append(resolved)

    counts = {
        state: sum(1 for item in output if item.get("mapping_state") == state)
        for state in (
            "ACTIVE_CANONICAL",
            "ALIAS_TO_CANONICAL",
            "EXCLUDED_WITH_REASON",
            "RECONCILE_REQUIRED",
        )
    }
    action_counts = {
        action: sum(1 for item in output if item.get("resolution_action") == action)
        for action in sorted(ALLOWED_ACTIONS)
    }
    new_canonical_candidates = action_counts[NEW_CANONICAL]
    unresolved_review = action_counts[UNRESOLVED]
    original_reconcile = sum(
        1
        for item in mappings
        if isinstance(item, Mapping)
        and item.get("mapping_state") == "RECONCILE_REQUIRED"
    )
    explicit_review_complete = reviewed_reconcile == original_reconcile
    review_decision_complete = unresolved_review == 0 and all(
        item.get("resolution_action") not in {"", None}
        for item in output
        if item.get("mapping_state") == "RECONCILE_REQUIRED"
    )
    terminal = sum(counts[state] for state in TERMINAL_MAPPING_STATES)

    result: dict[str, object] = {
        "schema_version": "SOURCE-RESOLUTION-REVIEW-1.0",
        "snapshot_id": smc.get("snapshot_id"),
        "source_manifest_sha256": smc.get("source_manifest_sha256"),
        "smc_candidate_sha256": smc.get("candidate_sha256"),
        "source_records": len(output),
        "original_reconcile_required": original_reconcile,
        "explicit_reviews_supplied": reviewed_reconcile,
        "explicit_review_complete": explicit_review_complete,
        "review_decision_complete": review_decision_complete,
        "counts_by_mapping_state": counts,
        "counts_by_resolution_action": action_counts,
        "terminal_mappings_candidate": terminal,
        "new_canonical_candidates": new_canonical_candidates,
        "unresolved_review": unresolved_review,
        "reconcile_required_after_review": counts["RECONCILE_REQUIRED"],
        "terminal_mapping_coverage_pct": 0.0 if not output else terminal / len(output),
        "authority_batch_ready": unresolved_review == 0,
        "mappings": output,
        "mappings_sha256": _sha256(output),
        "crm_universe_complete": False,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "review_sha256": "",
    }
    result["review_sha256"] = _sha256(
        {key: value for key, value in result.items() if key != "review_sha256"}
    )
    return result


def validate_resolution_review(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != "SOURCE-RESOLUTION-REVIEW-1.0":
        violations.append("INVALID_SCHEMA_VERSION")
    for key, expected in (
        ("crm_universe_complete", False),
        ("authority_advanced", False),
    ):
        value = payload.get(key)
        if not isinstance(value, bool) or value is not expected:
            violations.append(f"INVALID_{key.upper()}")
    for key in ("h_id_allocations", "send_allowed"):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != 0:
            violations.append(f"INVALID_{key.upper()}")
    if payload.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")

    for key in (
        "snapshot_id",
        "source_manifest_sha256",
        "smc_candidate_sha256",
        "mappings_sha256",
        "review_sha256",
    ):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            violations.append(f"INVALID_{key.upper()}_SCALAR")
    for key in ("source_manifest_sha256", "smc_candidate_sha256"):
        value = payload.get(key)
        if isinstance(value, str) and not re.fullmatch(r"[0-9a-f]{64}", value):
            violations.append(f"INVALID_{key.upper()}_FORMAT")

    mappings = payload.get("mappings")
    if not isinstance(mappings, list) or not all(
        isinstance(item, Mapping) for item in mappings
    ):
        violations.append("MAPPINGS_NOT_ARRAY_OF_OBJECTS")
        mappings = []
    source_records = payload.get("source_records")
    if isinstance(source_records, bool) or not isinstance(source_records, int):
        violations.append("SOURCE_RECORD_COUNT_NOT_INTEGER")
    elif source_records != len(mappings):
        violations.append("SOURCE_RECORD_COUNT_MISMATCH")

    keys: list[str] = []
    for item in mappings:
        assert isinstance(item, Mapping)
        key_value = item.get("source_record_key")
        if not isinstance(key_value, str) or not key_value.strip():
            violations.append("EMPTY_OR_NON_STRING_SOURCE_RECORD_KEY")
            key = ""
        else:
            key = key_value.strip()
        keys.append(key)

        mapping_state = item.get("mapping_state")
        action = item.get("resolution_action")
        target = item.get("canonical_hotel_id")
        authority_action = item.get("authority_action")
        if not isinstance(mapping_state, str) or mapping_state not in ALL_MAPPING_STATES:
            violations.append("INVALID_MAPPING_STATE")
            continue
        if not isinstance(action, str) or action not in (ALLOWED_ACTIONS | {CARRY_TERMINAL}):
            violations.append("INVALID_RESOLUTION_ACTION")
            continue
        if not isinstance(target, str):
            violations.append("NON_STRING_CANONICAL_TARGET")
            target = ""
        if not isinstance(authority_action, str) or not authority_action:
            violations.append("INVALID_AUTHORITY_ACTION_SCALAR")

        if action == CARRY_TERMINAL:
            if mapping_state not in TERMINAL_MAPPING_STATES:
                violations.append("CARRY_TERMINAL_ON_NON_TERMINAL_MAPPING")
            if authority_action != "NONE":
                violations.append("CARRY_TERMINAL_AUTHORITY_ACTION_MUST_BE_NONE")
            continue

        reason = item.get("resolution_reason_code")
        evidence = item.get("resolution_evidence_ref")
        origin = item.get("resolution_origin")
        if not isinstance(reason, str) or not reason.strip():
            violations.append("INVALID_RESOLUTION_REASON_CODE")
        if not isinstance(evidence, str) or not evidence.strip():
            violations.append("INVALID_RESOLUTION_EVIDENCE_REF")
        if not isinstance(origin, str) or origin not in {"AUTO_PROPOSED", "EXPLICIT_REVIEW"}:
            violations.append("INVALID_RESOLUTION_ORIGIN")

        expected_state = {
            MATCH_EXISTING: "ACTIVE_CANONICAL",
            ALIAS_EXISTING: "ALIAS_TO_CANONICAL",
            EXCLUDE: "EXCLUDED_WITH_REASON",
            NEW_CANONICAL: "RECONCILE_REQUIRED",
            UNRESOLVED: "RECONCILE_REQUIRED",
        }[action]
        if mapping_state != expected_state:
            violations.append("INVALID_ACTION_MAPPING_TRANSITION")
        if action in {MATCH_EXISTING, ALIAS_EXISTING}:
            if not re.fullmatch(r"H-\d{4,}", target):
                violations.append("EXISTING_ACTION_REQUIRES_CANONICAL_TARGET")
            if item.get("current_evidence_verified") is not True:
                violations.append("EXISTING_ACTION_REQUIRES_CURRENT_EVIDENCE")
        elif target:
            violations.append("NON_EXISTING_ACTION_FORBIDS_CANONICAL_TARGET")
        if action == NEW_CANONICAL and item.get("current_evidence_verified") is not True:
            violations.append("NEW_CANONICAL_REQUIRES_CURRENT_EVIDENCE")

    if any(not key for key in keys):
        violations.append("EMPTY_SOURCE_RECORD_KEY")
    if len(keys) != len(set(keys)):
        violations.append("DUPLICATE_SOURCE_RECORD_KEY")

    expected_counts = {
        state: sum(1 for item in mappings if item.get("mapping_state") == state)
        for state in (
            "ACTIVE_CANONICAL",
            "ALIAS_TO_CANONICAL",
            "EXCLUDED_WITH_REASON",
            "RECONCILE_REQUIRED",
        )
    }
    if payload.get("counts_by_mapping_state") != expected_counts:
        violations.append("MAPPING_STATE_COUNTS_MISMATCH")
    expected_action_counts = {
        action: sum(1 for item in mappings if item.get("resolution_action") == action)
        for action in sorted(ALLOWED_ACTIONS)
    }
    if payload.get("counts_by_resolution_action") != expected_action_counts:
        violations.append("RESOLUTION_ACTION_COUNTS_MISMATCH")

    terminal = sum(expected_counts[state] for state in TERMINAL_MAPPING_STATES)
    unresolved = expected_action_counts[UNRESOLVED]
    new_candidates = expected_action_counts[NEW_CANONICAL]
    if payload.get("terminal_mappings_candidate") != terminal:
        violations.append("TERMINAL_MAPPING_COUNT_MISMATCH")
    if payload.get("reconcile_required_after_review") != expected_counts["RECONCILE_REQUIRED"]:
        violations.append("RECONCILE_REQUIRED_COUNT_MISMATCH")
    if payload.get("unresolved_review") != unresolved:
        violations.append("UNRESOLVED_REVIEW_COUNT_MISMATCH")
    if payload.get("new_canonical_candidates") != new_candidates:
        violations.append("NEW_CANONICAL_COUNT_MISMATCH")

    expected_coverage = 0.0 if not mappings else terminal / len(mappings)
    coverage = payload.get("terminal_mapping_coverage_pct")
    if isinstance(coverage, bool) or not isinstance(coverage, (int, float)):
        violations.append("INVALID_TERMINAL_MAPPING_COVERAGE")
    elif abs(float(coverage) - expected_coverage) > 1e-12:
        violations.append("TERMINAL_MAPPING_COVERAGE_MISMATCH")

    authority_ready = payload.get("authority_batch_ready")
    if not isinstance(authority_ready, bool) or authority_ready is not (unresolved == 0):
        violations.append("AUTHORITY_BATCH_READY_MISMATCH")
    for key in ("explicit_review_complete", "review_decision_complete"):
        if not isinstance(payload.get(key), bool):
            violations.append(f"INVALID_{key.upper()}_SCALAR")

    if payload.get("mappings_sha256") != _sha256(mappings):
        violations.append("MAPPINGS_SHA_MISMATCH")
    expected_sha = _sha256(
        {key: value for key, value in payload.items() if key != "review_sha256"}
    )
    if payload.get("review_sha256") != expected_sha:
        violations.append("REVIEW_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.source_resolution")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("smc_candidate")
    build.add_argument("canonical_catalog")
    build.add_argument("--reviews")
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_resolution_review(
                _read_json(args.smc_candidate),
                _read_json(args.canonical_catalog),
                _read_json(args.reviews) if args.reviews else None,
            )
            _write_json(args.out, result)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "snapshot_id": result["snapshot_id"],
                        "source_records": result["source_records"],
                        "original_reconcile_required": result[
                            "original_reconcile_required"
                        ],
                        "counts_by_mapping_state": result["counts_by_mapping_state"],
                        "counts_by_resolution_action": result[
                            "counts_by_resolution_action"
                        ],
                        "new_canonical_candidates": result[
                            "new_canonical_candidates"
                        ],
                        "unresolved_review": result["unresolved_review"],
                        "authority_batch_ready": result["authority_batch_ready"],
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
        payload = _read_json(args.path)
        if not isinstance(payload, Mapping):
            raise SourceResolutionError("resolution review must be a JSON object")
        violations = validate_resolution_review(payload)
        print(
            json.dumps(
                {
                    "valid": not violations,
                    "violations": list(violations),
                    "review_sha256": payload.get("review_sha256"),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if not violations else 2
    except (SourceResolutionError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps({"valid": False, "error": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
