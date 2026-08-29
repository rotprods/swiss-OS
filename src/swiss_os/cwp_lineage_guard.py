from __future__ import annotations

import base64
import binascii
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class CwpLineageError(ValueError):
    pass


def _sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise CwpLineageError(f"{path}: expected JSON object")
    return value


def _load_gzip_json(path: Path) -> tuple[Mapping[str, Any], str]:
    """Load a gzip JSON artifact from raw gzip bytes or GitHub text-safe base64.

    GitHub's contents writer in this execution environment is UTF-8 text-only. Binary
    gzip bytes therefore cannot be persisted losslessly through that actuator. The
    durable fallback is the base64 text representation of the *same* gzip payload.
    We hash the decoded gzip bytes so the provenance digest remains transport-neutral.
    Any non-gzip/non-canonical-base64 input fails closed.
    """
    stored = path.read_bytes()
    compressed = stored
    if not stored.startswith(b"\x1f\x8b"):
        try:
            compact = b"".join(stored.split())
            compressed = base64.b64decode(compact, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise CwpLineageError(f"{path}: invalid gzip or base64-gzip transport") from exc
        if not compressed.startswith(b"\x1f\x8b"):
            raise CwpLineageError(f"{path}: decoded transport is not gzip")
    digest = hashlib.sha256(compressed).hexdigest()
    try:
        value = json.loads(gzip.decompress(compressed).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CwpLineageError(f"{path}: invalid gzip JSON payload") from exc
    if not isinstance(value, Mapping):
        raise CwpLineageError(f"{path}: expected JSON object")
    return value, digest


def parse_offset_spec(value: object) -> list[int]:
    if isinstance(value, list):
        offsets = list(value)
    elif isinstance(value, int) and not isinstance(value, bool):
        offsets = [value]
    else:
        text = str(value or "").strip()
        if not text:
            return []
        if ".." in text:
            start, end = (int(part) for part in text.split("..", 1))
            offsets = list(range(start, end + 1))
        else:
            offsets = [int(text)]
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in offsets):
        raise CwpLineageError("offsets must be non-negative integers")
    return offsets


def validate_candidate_export(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != "CRM-CANDIDATE-EXPORT-1.0":
        errors.append("INVALID_CANDIDATE_EXPORT_SCHEMA")
    records = payload.get("records")
    if not isinstance(records, list) or not all(isinstance(row, Mapping) for row in records):
        return errors + ["CANDIDATE_RECORDS_NOT_ARRAY"]
    if len(records) != 1438 or payload.get("records_count") != 1438 or payload.get("candidate_new_entity_preauth") != 1438:
        errors.append("CANDIDATE_TOTAL_MISMATCH")
    offsets = [row.get("original_candidate_offset") for row in records]
    if offsets != list(range(len(records))):
        errors.append("CANDIDATE_OFFSETS_NOT_CONTIGUOUS")
    keys = [str(row.get("source_record_key", "")) for row in records]
    if keys != sorted(keys) or len(set(keys)) != len(keys) or any(not key for key in keys):
        errors.append("CANDIDATE_KEY_ORDER_OR_UNIQUENESS_DRIFT")
    if payload.get("candidate_order") != "source_record_key ascending":
        errors.append("CANDIDATE_ORDER_CONTRACT_DRIFT")
    if payload.get("records_sha256") != _sha256_json(records):
        errors.append("CANDIDATE_RECORDS_SHA_MISMATCH")
    if payload.get("source_records") != 2061 or payload.get("exact_name_city_matches") != 623:
        errors.append("SOURCE_ANTI_JOIN_COUNTS_DRIFT")
    if payload.get("authority_advanced") is not False or payload.get("h_id_allocations") != 0:
        errors.append("CANDIDATE_EXPORT_AUTHORITY_MUTATION")
    if payload.get("outbound") != "CLOSED" or payload.get("send_allowed") != 0:
        errors.append("CANDIDATE_EXPORT_OUTBOUND_OPEN")
    return errors


def validate_staged_lineage(next_payload: Mapping[str, Any], export: Mapping[str, Any], packet: Mapping[str, Any]) -> list[str]:
    errors = validate_candidate_export(export)
    records = export.get("records")
    if not isinstance(records, list):
        return errors
    offset_by_key = {str(row["source_record_key"]): int(row["original_candidate_offset"]) for row in records}
    ecv = next_payload.get("ecv_frontier")
    if not isinstance(ecv, Mapping):
        return errors + ["NEXT_ECV_FRONTIER_MISSING"]
    expected = parse_offset_spec(ecv.get("next_staged_original_candidate_offsets", ecv.get("next_staged_original_candidate_offset_range")))
    items = packet.get("items")
    if not isinstance(items, list) or not all(isinstance(item, Mapping) for item in items):
        return errors + ["STAGED_ITEMS_NOT_ARRAY"]
    actual: list[int] = []
    for item in items:
        key = str(item.get("source_record_key", ""))
        if key not in offset_by_key:
            errors.append("STAGED_KEY_NOT_IN_CANDIDATE_EXPORT")
        else:
            actual.append(offset_by_key[key])
    if actual != expected:
        errors.append(f"STAGED_ORIGINAL_CANDIDATE_OFFSETS_MISMATCH:{actual}!={expected}")
    if packet.get("batch_id") != ecv.get("next_staged_batch"):
        errors.append("NEXT_STAGED_BATCH_ID_MISMATCH")
    if packet.get("items_count") != len(items) or ecv.get("next_staged_items") != len(items):
        errors.append("STAGED_ITEMS_COUNT_MISMATCH")
    items_sha = _sha256_json(items)
    if packet.get("items_sha256") != items_sha or ecv.get("next_staged_items_sha256") != items_sha:
        errors.append("STAGED_ITEMS_SHA_MISMATCH")
    if packet.get("authority_advanced") is not False or packet.get("h_id_allocations") != 0:
        errors.append("STAGING_AUTHORITY_MUTATION")
    if packet.get("outbound") != "CLOSED" or packet.get("send_allowed") != 0:
        errors.append("STAGING_OUTBOUND_OPEN")
    return list(dict.fromkeys(errors))


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    next_payload = _load_json(root / "docs/state/NEXT.json")
    source = next_payload.get("source_universe")
    if not isinstance(source, Mapping):
        raise CwpLineageError("NEXT source_universe must be an object")
    export_path = root / str(source.get("candidate_export_path", ""))
    export, gzip_sha = _load_gzip_json(export_path)
    errors: list[str] = []
    if gzip_sha != source.get("candidate_export_gzip_sha256"):
        errors.append("CANDIDATE_EXPORT_GZIP_SHA_MISMATCH")
    ecv = next_payload.get("ecv_frontier")
    if not isinstance(ecv, Mapping):
        errors.append("NEXT_ECV_FRONTIER_MISSING")
    else:
        packet_path = root / str(ecv.get("next_staged_batch_path", ""))
        if packet_path.is_file():
            errors.extend(validate_staged_lineage(next_payload, export, _load_json(packet_path)))
        else:
            errors.extend(validate_candidate_export(export))
    if errors:
        print("cwp_lineage_guard: FAIL")
        for error in dict.fromkeys(errors):
            print(f"- {error}")
        return 1
    print("cwp_lineage_guard: PASS candidate_records=1438 staged_offsets=" + str(parse_offset_spec(ecv.get("next_staged_original_candidate_offsets", ecv.get("next_staged_original_candidate_offset_range")))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
