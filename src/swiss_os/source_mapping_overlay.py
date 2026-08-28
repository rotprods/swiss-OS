from __future__ import annotations

import hashlib
import json
import re
from typing import Mapping, Sequence

_HID = re.compile(r"^H-\d{4}$")


class SourceMappingOverlayError(ValueError):
    pass


def _sha(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _require_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise SourceMappingOverlayError(f"{name} must be a non-negative integer")
    return value


def build_match_existing_overlay(
    reviews_payload: Mapping[str, object],
    *,
    snapshot_id: str,
    base_candidate_sha256: str,
    base_source_records: int,
    base_terminal_mappings: int,
    base_reconcile_required: int,
) -> dict[str, object]:
    if reviews_payload.get("schema_version") != "SOURCE-RESOLUTION-EXPLICIT-REVIEWS-1.0":
        raise SourceMappingOverlayError("unsupported review schema")
    if reviews_payload.get("review_state") != "READY_FOR_SRR_APPLICATION":
        raise SourceMappingOverlayError("reviews are not READY_FOR_SRR_APPLICATION")
    if reviews_payload.get("source_snapshot_id") != snapshot_id:
        raise SourceMappingOverlayError("snapshot mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", base_candidate_sha256):
        raise SourceMappingOverlayError("base_candidate_sha256 must be lowercase sha256")

    source_records = _require_int(base_source_records, "base_source_records")
    terminal = _require_int(base_terminal_mappings, "base_terminal_mappings")
    reconcile = _require_int(base_reconcile_required, "base_reconcile_required")
    if terminal + reconcile != source_records:
        raise SourceMappingOverlayError("base terminal + reconcile must equal source records")

    reviews = reviews_payload.get("reviews")
    if not isinstance(reviews, list) or not all(isinstance(row, Mapping) for row in reviews):
        raise SourceMappingOverlayError("reviews must be an array of objects")
    if reviews_payload.get("reviews_count") != len(reviews):
        raise SourceMappingOverlayError("reviews_count mismatch")

    deltas: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in reviews:
        key = str(row.get("source_record_key", "")).strip()
        hid = str(row.get("canonical_hotel_id", "")).strip()
        if not key or key in seen:
            raise SourceMappingOverlayError("review source_record_key must be unique and non-empty")
        seen.add(key)
        if row.get("action") != "MATCH_EXISTING":
            raise SourceMappingOverlayError(f"{key}: only MATCH_EXISTING is supported by this overlay")
        if not _HID.fullmatch(hid):
            raise SourceMappingOverlayError(f"{key}: canonical_hotel_id invalid")
        if row.get("current_evidence_verified") is not True:
            raise SourceMappingOverlayError(f"{key}: current evidence must be verified")
        if row.get("authority_action") != "NONE_PREAUTH_REVIEW":
            raise SourceMappingOverlayError(f"{key}: authority_action must be NONE_PREAUTH_REVIEW")
        evidence = str(row.get("evidence_ref", "")).strip()
        reason = str(row.get("reason_code", "")).strip()
        if not evidence or not reason:
            raise SourceMappingOverlayError(f"{key}: evidence_ref and reason_code are required")
        deltas.append({
            "source_record_key": key,
            "from_mapping_state": "RECONCILE_REQUIRED",
            "to_mapping_state": "ACTIVE_CANONICAL",
            "canonical_hotel_id": hid,
            "reason_code": reason,
            "evidence_ref": evidence,
        })

    deltas.sort(key=lambda row: str(row["source_record_key"]))
    if len(deltas) > reconcile:
        raise SourceMappingOverlayError("delta exceeds base reconcile frontier")

    effective_terminal = terminal + len(deltas)
    effective_reconcile = reconcile - len(deltas)
    payload: dict[str, object] = {
        "schema_version": "CRM-SOURCE-MAPPING-OVERLAY-1.0",
        "snapshot_id": snapshot_id,
        "base_candidate_sha256": base_candidate_sha256,
        "base_source_records": source_records,
        "base_terminal_mappings": terminal,
        "base_reconcile_required": reconcile,
        "terminal_deltas": deltas,
        "terminal_deltas_count": len(deltas),
        "effective_terminal_mappings": effective_terminal,
        "effective_reconcile_required": effective_reconcile,
        "effective_terminal_mapping_coverage_pct": 0.0 if not source_records else effective_terminal / source_records,
        "materialization_state": "OVERLAY_VALIDATED_BASE_REBUILD_PENDING",
        "authority_advanced": False,
        "h_id_allocations": 0,
        "crm_universe_complete": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "overlay_sha256": "",
    }
    payload["overlay_sha256"] = _sha({k: v for k, v in payload.items() if k != "overlay_sha256"})
    return payload


def validate_overlay(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != "CRM-SOURCE-MAPPING-OVERLAY-1.0": violations.append("INVALID_SCHEMA")
    if payload.get("authority_advanced") is not False: violations.append("AUTHORITY_ADVANCED_FORBIDDEN")
    if payload.get("h_id_allocations") != 0: violations.append("H_ID_ALLOCATIONS_FORBIDDEN")
    if payload.get("crm_universe_complete") is not False: violations.append("CRM_COMPLETE_FORBIDDEN")
    if payload.get("outbound") != "CLOSED": violations.append("OUTBOUND_NOT_CLOSED")
    if payload.get("send_allowed") != 0: violations.append("SEND_ALLOWED_NOT_ZERO")
    deltas = payload.get("terminal_deltas")
    if not isinstance(deltas, list):
        violations.append("DELTAS_NOT_ARRAY"); deltas = []
    if payload.get("terminal_deltas_count") != len(deltas): violations.append("DELTA_COUNT_MISMATCH")
    keys: set[str] = set()
    for row in deltas:
        if not isinstance(row, Mapping): violations.append("DELTA_NOT_OBJECT"); continue
        key = str(row.get("source_record_key", "")).strip()
        if not key or key in keys: violations.append("INVALID_OR_DUPLICATE_SOURCE_KEY")
        keys.add(key)
        if row.get("from_mapping_state") != "RECONCILE_REQUIRED" or row.get("to_mapping_state") != "ACTIVE_CANONICAL": violations.append("INVALID_MAPPING_TRANSITION")
        if not _HID.fullmatch(str(row.get("canonical_hotel_id", ""))): violations.append("INVALID_CANONICAL_HID")
    try:
        source = _require_int(payload.get("base_source_records"), "base_source_records")
        base_terminal = _require_int(payload.get("base_terminal_mappings"), "base_terminal_mappings")
        base_reconcile = _require_int(payload.get("base_reconcile_required"), "base_reconcile_required")
        if source != base_terminal + base_reconcile: violations.append("BASE_COUNT_INVARIANT_FAILED")
        if payload.get("effective_terminal_mappings") != base_terminal + len(deltas): violations.append("EFFECTIVE_TERMINAL_COUNT_MISMATCH")
        if payload.get("effective_reconcile_required") != base_reconcile - len(deltas): violations.append("EFFECTIVE_RECONCILE_COUNT_MISMATCH")
    except SourceMappingOverlayError:
        violations.append("INVALID_COUNTS")
    expected = _sha({k: v for k, v in payload.items() if k != "overlay_sha256"})
    if payload.get("overlay_sha256") != expected: violations.append("OVERLAY_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))
