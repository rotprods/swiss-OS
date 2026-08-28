from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable, Mapping, Sequence


class IngestPacketError(ValueError):
    """Raised when CMI decisions cannot be transformed safely."""


TERMINAL_MATCH = "MATCHED_EXISTING"
# Public compatibility alias: downstream pre-authority engines may refer to
# the serialized state name directly. Both constants intentionally resolve to
# the same immutable work-state value.
MATCHED_EXISTING = TERMINAL_MATCH
RECONCILE = "RECONCILE_REQUIRED"
VERIFY_NEW = "VERIFY_NEW_ENTITY"
REVIEW_UNKNOWN = "REVIEW_UNKNOWN_DECISION"

PRIORITY = {
    RECONCILE: 100,
    VERIFY_NEW: 80,
    REVIEW_UNKNOWN: 60,
    TERMINAL_MATCH: 0,
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _first(payload: Mapping[str, object], keys: Sequence[str]) -> str:
    for key in keys:
        value = _text(payload.get(key))
        if value:
            return value
    return ""


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def classify_work_state(decision: str, matched_hotel_id: str) -> str:
    normalized = decision.upper().replace("-", "_").replace(" ", "_")
    if matched_hotel_id and not any(
        token in normalized for token in ("AMBIG", "CONFLICT", "RECONCILE")
    ):
        return TERMINAL_MATCH
    if any(token in normalized for token in ("AMBIG", "CONFLICT", "RECONCILE")):
        return RECONCILE
    # CMI-1.0's canonical no-match classification is TRUE_MISSING. Treat it as
    # exactly the same pre-authority work state as the older/new-candidate
    # compatibility spellings. This is routing only: it never authorizes H-ID
    # allocation or canonical promotion.
    if normalized == "TRUE_MISSING" or any(
        token in normalized
        for token in ("NEW", "UNMATCHED", "NO_MATCH", "MISSING_CANONICAL")
    ):
        return VERIFY_NEW
    if any(token in normalized for token in ("MATCH", "EXISTING", "DUPLICATE")):
        return TERMINAL_MATCH
    return REVIEW_UNKNOWN


@dataclass(frozen=True)
class IngestDecision:
    source_record_key: str
    name: str
    city: str
    detail_url: str
    decision: str
    matched_hotel_id: str
    reason: str
    work_state: str
    priority: int

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object], index: int) -> "IngestDecision":
        source_record_key = _first(
            payload,
            (
                "source_record_key",
                "provider_record_key",
                "record_key",
                "source_key",
                "staging_key",
            ),
        )
        if not source_record_key:
            source_record_key = f"decision-index:{index:08d}"
        decision = _first(
            payload,
            (
                "decision",
                "decision_type",
                "classification",
                "staging_class",
                "state",
                "outcome",
            ),
        ) or "UNKNOWN"
        matched_hotel_id = _first(
            payload,
            ("matched_hotel_id", "canonical_hotel_id", "canonical_id", "hotel_id"),
        )
        work_state = classify_work_state(decision, matched_hotel_id)
        return cls(
            source_record_key=source_record_key,
            name=_first(
                payload,
                (
                    "raw_name",
                    "name",
                    "canonical_name",
                    "hotel_name",
                    "normalized_name",
                ),
            ),
            city=_first(payload, ("raw_city", "city", "locality", "normalized_city")),
            detail_url=_first(
                payload,
                ("detail_url", "source_url", "url", "normalized_detail_url"),
            ),
            decision=decision,
            matched_hotel_id=matched_hotel_id,
            reason=_first(payload, ("reason", "reason_code", "notes", "explanation")),
            work_state=work_state,
            priority=PRIORITY[work_state],
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "source_record_key": self.source_record_key,
            "name": self.name,
            "city": self.city,
            "detail_url": self.detail_url,
            "decision": self.decision,
            "matched_hotel_id": self.matched_hotel_id,
            "reason": self.reason,
            "work_state": self.work_state,
            "priority": self.priority,
        }


def _extract_decisions(payload: object) -> list[Mapping[str, object]]:
    if isinstance(payload, list):
        raw = payload
    elif isinstance(payload, Mapping):
        raw = payload.get("decisions")
        if raw is None and isinstance(payload.get("result"), Mapping):
            raw = payload["result"].get("decisions")
        if raw is None and isinstance(payload.get("payload"), Mapping):
            raw = payload["payload"].get("decisions")
    else:
        raw = None
    if not isinstance(raw, list):
        raise IngestPacketError("CMI payload must contain a decisions array")
    if not all(isinstance(item, Mapping) for item in raw):
        raise IngestPacketError("CMI decisions must contain only JSON objects")
    return list(raw)


def build_work_packet(
    cmi_payload: object,
    *,
    snapshot_id: str,
    batch_size: int = 100,
) -> dict[str, object]:
    if not snapshot_id.strip():
        raise IngestPacketError("snapshot_id must be non-empty")
    if batch_size <= 0:
        raise IngestPacketError("batch_size must be positive")

    raw_decisions = _extract_decisions(cmi_payload)
    decisions = tuple(
        IngestDecision.from_mapping(payload, index)
        for index, payload in enumerate(raw_decisions, start=1)
    )
    duplicate_keys = sorted(
        key
        for key in {decision.source_record_key for decision in decisions}
        if sum(1 for item in decisions if item.source_record_key == key) > 1
    )
    if duplicate_keys:
        raise IngestPacketError(
            "duplicate source_record_key values: " + ", ".join(duplicate_keys[:10])
        )

    ordered = sorted(
        decisions,
        key=lambda item: (-item.priority, item.source_record_key),
    )
    active = [item for item in ordered if item.work_state != TERMINAL_MATCH]
    terminal = [item for item in ordered if item.work_state == TERMINAL_MATCH]

    batches: list[dict[str, object]] = []
    for offset in range(0, len(active), batch_size):
        items = active[offset : offset + batch_size]
        batch_id = f"{snapshot_id}:WORK:{offset // batch_size + 1:04d}"
        batch_payload = [item.as_dict() for item in items]
        batches.append(
            {
                "batch_id": batch_id,
                "batch_index": offset // batch_size + 1,
                "items_count": len(items),
                "items_sha256": _sha256(batch_payload),
                "items": batch_payload,
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound": "CLOSED",
                "send_allowed": 0,
            }
        )

    counts = {
        state: sum(1 for item in decisions if item.work_state == state)
        for state in (RECONCILE, VERIFY_NEW, REVIEW_UNKNOWN, TERMINAL_MATCH)
    }
    packet: dict[str, object] = {
        "schema_version": "CMI-WORK-PACKET-1.0",
        "snapshot_id": snapshot_id,
        "input_decisions": len(decisions),
        "active_work_items": len(active),
        "terminal_matches": len(terminal),
        "counts_by_state": counts,
        "batch_size": batch_size,
        "batches_count": len(batches),
        "batches": batches,
        "terminal_match_sha256": _sha256(
            [item.as_dict() for item in terminal]
        ),
        "packet_sha256": "",
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "next_route": (
            "EXACT_CURRENT_ENTITY_RESOLUTION"
            if active
            else "SOURCE_SCOPE_RECONCILIATION_OR_AUTHORITY_RECOVERY"
        ),
    }
    packet["packet_sha256"] = _sha256(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    return packet


def validate_work_packet(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != "CMI-WORK-PACKET-1.0":
        violations.append("INVALID_SCHEMA_VERSION")
    if bool(payload.get("authority_advanced")):
        violations.append("AUTHORITY_ADVANCED_FORBIDDEN")
    if int(payload.get("h_id_allocations", 0)) != 0:
        violations.append("H_ID_ALLOCATIONS_FORBIDDEN")
    if payload.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")
    if int(payload.get("send_allowed", 0)) != 0:
        violations.append("SEND_ALLOWED_NOT_ZERO")
    batches = payload.get("batches")
    if not isinstance(batches, list):
        violations.append("BATCHES_NOT_ARRAY")
        batches = []
    if int(payload.get("batches_count", -1)) != len(batches):
        violations.append("BATCH_COUNT_MISMATCH")
    total = 0
    seen_keys: set[str] = set()
    for batch in batches:
        if not isinstance(batch, Mapping):
            violations.append("BATCH_NOT_OBJECT")
            continue
        items = batch.get("items")
        if not isinstance(items, list):
            violations.append("BATCH_ITEMS_NOT_ARRAY")
            continue
        if int(batch.get("items_count", -1)) != len(items):
            violations.append("BATCH_ITEMS_COUNT_MISMATCH")
        if batch.get("items_sha256") != _sha256(items):
            violations.append("BATCH_ITEMS_SHA_MISMATCH")
        total += len(items)
        for item in items:
            if not isinstance(item, Mapping):
                violations.append("WORK_ITEM_NOT_OBJECT")
                continue
            key = _text(item.get("source_record_key"))
            if not key:
                violations.append("EMPTY_SOURCE_RECORD_KEY")
            elif key in seen_keys:
                violations.append("DUPLICATE_SOURCE_RECORD_KEY")
            seen_keys.add(key)
            if item.get("work_state") == TERMINAL_MATCH:
                violations.append("TERMINAL_MATCH_IN_ACTIVE_BATCH")
    if total != int(payload.get("active_work_items", -1)):
        violations.append("ACTIVE_WORK_COUNT_MISMATCH")
    expected_sha = _sha256(
        {key: value for key, value in payload.items() if key != "packet_sha256"}
    )
    if payload.get("packet_sha256") != expected_sha:
        violations.append("PACKET_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.ingest_packet")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("cmi_payload")
    build.add_argument("--snapshot-id", required=True)
    build.add_argument("--batch-size", type=int, default=100)
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            packet = build_work_packet(
                _read_json(args.cmi_payload),
                snapshot_id=args.snapshot_id,
                batch_size=args.batch_size,
            )
            _write_json(args.out, packet)
            print(json.dumps({
                "valid": True,
                "snapshot_id": packet["snapshot_id"],
                "input_decisions": packet["input_decisions"],
                "active_work_items": packet["active_work_items"],
                "terminal_matches": packet["terminal_matches"],
                "counts_by_state": packet["counts_by_state"],
                "batches_count": packet["batches_count"],
                "packet_sha256": packet["packet_sha256"],
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound": "CLOSED",
                "send_allowed": 0,
                "out": args.out,
            }, indent=2, sort_keys=True))
            return 0
        payload = _read_json(args.path)
        if not isinstance(payload, Mapping):
            raise IngestPacketError("work packet must be a JSON object")
        violations = validate_work_packet(payload)
        print(json.dumps({
            "valid": not violations,
            "violations": list(violations),
            "packet_sha256": payload.get("packet_sha256"),
        }, indent=2, sort_keys=True))
        return 0 if not violations else 2
    except (IngestPacketError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
