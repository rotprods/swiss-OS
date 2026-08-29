from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from swiss_os.cwp_lineage_guard import CwpLineageError, _load_candidate_export, validate_candidate_export


WORK_ITEM_FIELDS = (
    "city",
    "decision",
    "detail_url",
    "matched_hotel_id",
    "name",
    "priority",
    "reason",
    "source_record_key",
    "work_state",
)


class CwpMaterializeError(ValueError):
    pass


def _sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _require_int(mapping: Mapping[str, Any], key: str, *, minimum: int = 0) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise CwpMaterializeError(f"{key} must be an integer >= {minimum}")
    return value


def _canonical_work_item(row: Mapping[str, Any]) -> dict[str, Any]:
    item = {field: row.get(field, "") for field in WORK_ITEM_FIELDS}
    if item["decision"] != "CANDIDATE_NEW_ENTITY_PREAUTH":
        raise CwpMaterializeError("candidate decision must remain CANDIDATE_NEW_ENTITY_PREAUTH")
    if item["work_state"] != "VERIFY_NEW_ENTITY":
        raise CwpMaterializeError("candidate work_state must remain VERIFY_NEW_ENTITY")
    if item["reason"] != "NO_EXACT_CURRENT_CANONICAL_MATCH":
        raise CwpMaterializeError("candidate reason drift")
    if item["matched_hotel_id"] not in ("", None):
        raise CwpMaterializeError("staging must not carry a canonical hotel ID")
    item["matched_hotel_id"] = ""
    if not isinstance(item["source_record_key"], str) or not item["source_record_key"]:
        raise CwpMaterializeError("source_record_key missing")
    if not isinstance(item["detail_url"], str) or not item["detail_url"].startswith("https://www.hotelleriesuisse.ch/"):
        raise CwpMaterializeError("detail_url outside qualified HotellerieSuisse source")
    if isinstance(item["priority"], bool) or not isinstance(item["priority"], int):
        raise CwpMaterializeError("priority must be an integer")
    return item


def build_work_packet(
    records: list[Mapping[str, Any]],
    *,
    snapshot_id: str,
    start_offset: int,
    items_count: int,
    subbatch_number: int,
) -> dict[str, Any]:
    if start_offset < 0 or items_count < 1 or subbatch_number < 1:
        raise CwpMaterializeError("invalid materialization bounds")
    end_offset = start_offset + items_count
    if end_offset > len(records):
        raise CwpMaterializeError("materialization exceeds candidate export")
    selected = records[start_offset:end_offset]
    offsets = [row.get("original_candidate_offset") for row in selected]
    expected_offsets = list(range(start_offset, end_offset))
    if offsets != expected_offsets:
        raise CwpMaterializeError(f"candidate lineage drift: {offsets!r} != {expected_offsets!r}")
    items = [_canonical_work_item(row) for row in selected]
    batch_id = f"{snapshot_id}:WORK:0001:SUB:{subbatch_number:04d}"
    return {
        "schema_version": "CMI-WORK-PACKET-1.0",
        "snapshot_id": snapshot_id,
        "batch_id": batch_id,
        "batch_index": 1,
        "items_count": len(items),
        "items": items,
        "items_sha256": _sha256_json(items),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def build_idle_report(next_payload: Mapping[str, Any]) -> dict[str, Any]:
    source = next_payload.get("source_universe")
    snapshot_id = ""
    if isinstance(source, Mapping):
        snapshot_id = str(source.get("snapshot_id", ""))
    return {
        "schema_version": "CWP-MATERIALIZE-REPORT-1.0",
        "state": "NO_ACTIVE_CWP_REQUEST",
        "materialized": False,
        "snapshot_id": snapshot_id,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def materialize_from_next(root: Path, next_payload: Mapping[str, Any]) -> tuple[dict[str, Any], Mapping[str, Any]]:
    source = next_payload.get("source_universe")
    if not isinstance(source, Mapping):
        raise CwpMaterializeError("NEXT source_universe missing")
    request = next_payload.get("cwp_materialization_request")
    if not isinstance(request, Mapping):
        raise CwpMaterializeError("NEXT cwp_materialization_request missing")
    try:
        export, gzip_sha = _load_candidate_export(root, source)
    except CwpLineageError as exc:
        raise CwpMaterializeError(str(exc)) from exc
    errors = validate_candidate_export(export)
    if errors:
        raise CwpMaterializeError("candidate export invalid: " + ",".join(errors))
    if gzip_sha != source.get("candidate_export_gzip_sha256"):
        raise CwpMaterializeError("candidate export gzip SHA does not match NEXT")
    records = export.get("records")
    if not isinstance(records, list) or not all(isinstance(row, Mapping) for row in records):
        raise CwpMaterializeError("candidate records unavailable")

    start_offset = _require_int(request, "original_candidate_offset_start")
    items_count = _require_int(request, "items_count", minimum=1)
    subbatch_number = _require_int(request, "subbatch_number", minimum=1)
    snapshot_id = str(next_payload.get("source_universe", {}).get("snapshot_id", ""))
    if not snapshot_id or snapshot_id != export.get("snapshot_id"):
        raise CwpMaterializeError("snapshot mismatch between NEXT and candidate export")

    packet = build_work_packet(
        records,
        snapshot_id=snapshot_id,
        start_offset=start_offset,
        items_count=items_count,
        subbatch_number=subbatch_number,
    )
    expected_batch_id = str(request.get("batch_id", ""))
    if packet["batch_id"] != expected_batch_id:
        raise CwpMaterializeError(f"batch ID drift: {packet['batch_id']} != {expected_batch_id}")
    expected_range = f"{start_offset}..{start_offset + items_count - 1}"
    if request.get("original_candidate_offset_range") != expected_range:
        raise CwpMaterializeError("materialization offset range drift")
    return packet, request


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CwpMaterializeError(f"cannot read {path}") from exc
    if not isinstance(value, Mapping):
        raise CwpMaterializeError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize the next bounded CMI work packet from the durable candidate export")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--next", dest="next_path", default="docs/state/NEXT.json")
    parser.add_argument("--out-dir", default=".artifacts")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    next_payload = _load_json(root / args.next_path)
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not isinstance(next_payload.get("cwp_materialization_request"), Mapping):
        report = build_idle_report(next_payload)
        (out_dir / "CWP_MATERIALIZE_REPORT.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0

    packet, request = materialize_from_next(root, next_payload)
    requested_path = Path(str(request.get("batch_path", "")))
    if not requested_path.name.startswith("CMI_WORK_BATCH_") or requested_path.suffix != ".json":
        raise CwpMaterializeError("requested batch_path is not a CMI work packet JSON")
    out_path = out_dir / requested_path.name
    out_path.write_text(json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    report = {
        "schema_version": "CWP-MATERIALIZE-REPORT-1.0",
        "state": "MATERIALIZED",
        "materialized": True,
        "batch_id": packet["batch_id"],
        "batch_file": out_path.name,
        "items_count": packet["items_count"],
        "items_sha256": packet["items_sha256"],
        "original_candidate_offset_range": request["original_candidate_offset_range"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    (out_dir / "CWP_MATERIALIZE_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
