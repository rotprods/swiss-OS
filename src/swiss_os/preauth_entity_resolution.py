from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

from .snapshot_freeze import normalize_text, normalize_url


class EntityResolutionError(ValueError):
    """Raised when a safe pre-authority entity-resolution workset cannot be built."""


SCHEMA_VERSION = "CRM-PREAUTH-ENTITY-RESOLUTION-1.0"
DUPLICATE_REVIEW = "EXACT_DUPLICATE_GROUP_REVIEW"
UNIQUE_PREAUTH = "UNIQUE_NEW_ENTITY_PREAUTH"


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _assert_exact_current_complete(next_payload: Mapping[str, object], expected_records: int) -> None:
    ecv = next_payload.get("ecv_frontier")
    if not isinstance(ecv, Mapping):
        raise EntityResolutionError("NEXT is missing ecv_frontier")
    total = int(ecv.get("candidate_records_total", -1))
    verified = int(ecv.get("current_detail_verified", -1))
    remaining = int(ecv.get("remaining_unverified", -1))
    pending = int(ecv.get("pending_requeue", -1))
    holes = ecv.get("lineage_holes", [])
    if total != expected_records or verified != expected_records:
        raise EntityResolutionError("exact-current frontier is not complete for expected records")
    if remaining != 0 or pending != 0 or holes not in ([], ()):
        raise EntityResolutionError("exact-current frontier still has unresolved work")


def _safe_packet(path: Path, snapshot_id: str) -> Mapping[str, object]:
    payload = _read_json(path)
    if not isinstance(payload, Mapping):
        raise EntityResolutionError(f"{path.name}: packet must be a JSON object")
    batch_id = str(payload.get("batch_id", "")).strip()
    packet_snapshot = str(payload.get("snapshot_id", "")).strip()
    if snapshot_id and packet_snapshot and packet_snapshot != snapshot_id:
        raise EntityResolutionError(f"{path.name}: snapshot_id mismatch")
    if snapshot_id and batch_id and not batch_id.startswith(snapshot_id):
        raise EntityResolutionError(f"{path.name}: batch_id snapshot mismatch")
    if bool(payload.get("authority_advanced", False)):
        raise EntityResolutionError(f"{path.name}: authority_advanced must be false")
    if int(payload.get("h_id_allocations", 0)) != 0:
        raise EntityResolutionError(f"{path.name}: h_id_allocations must be zero")
    if payload.get("outbound", "CLOSED") != "CLOSED":
        raise EntityResolutionError(f"{path.name}: outbound must be CLOSED")
    if int(payload.get("send_allowed", 0)) != 0:
        raise EntityResolutionError(f"{path.name}: send_allowed must be zero")
    items = payload.get("items")
    if not isinstance(items, list) or not all(isinstance(item, Mapping) for item in items):
        raise EntityResolutionError(f"{path.name}: items must be an array of objects")
    return payload


def _load_candidate_records(state_dir: Path, snapshot_id: str) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    paths = sorted(
        path
        for path in state_dir.glob("CMI_WORK_BATCH_0001*.json")
        if "REQUEUE" not in path.name.upper()
    )
    if not paths:
        raise EntityResolutionError("no CMI work packets found")

    for path in paths:
        packet = _safe_packet(path, snapshot_id)
        for raw in packet["items"]:
            key = str(raw.get("source_record_key", "")).strip()
            if not key:
                raise EntityResolutionError(f"{path.name}: empty source_record_key")
            record = {
                "source_record_key": key,
                "name": str(raw.get("name", "")).strip(),
                "city": str(raw.get("city", "")).strip(),
                "detail_url": str(raw.get("detail_url", "")).strip(),
            }
            if not record["name"]:
                raise EntityResolutionError(f"{path.name}: {key} has empty name")
            prior = records.get(key)
            if prior is not None and prior != record:
                raise EntityResolutionError(f"conflicting duplicate source_record_key: {key}")
            records[key] = record
    return records


class _UnionFind:
    def __init__(self, keys: Sequence[str]) -> None:
        self.parent = {key: key for key in keys}

    def find(self, key: str) -> str:
        parent = self.parent[key]
        if parent != key:
            self.parent[key] = self.find(parent)
        return self.parent[key]

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def build_workset(
    state_dir: str | Path,
    *,
    next_path: str | Path,
    snapshot_id: str,
    expected_records: int,
) -> dict[str, object]:
    if expected_records <= 0:
        raise EntityResolutionError("expected_records must be greater than zero")
    next_payload = _read_json(Path(next_path))
    if not isinstance(next_payload, Mapping):
        raise EntityResolutionError("NEXT must be a JSON object")
    _assert_exact_current_complete(next_payload, expected_records)

    records = _load_candidate_records(Path(state_dir), snapshot_id)
    if len(records) != expected_records:
        raise EntityResolutionError(
            f"candidate record count mismatch: expected {expected_records}, got {len(records)}"
        )

    keys = sorted(records)
    uf = _UnionFind(keys)
    signal_members: dict[tuple[str, str], list[str]] = {}

    for key in keys:
        record = records[key]
        detail = normalize_url(record["detail_url"])
        if detail:
            signal_members.setdefault(("EXACT_DETAIL_URL", detail), []).append(key)
        name_city = (normalize_text(record["name"]), normalize_text(record["city"]))
        if all(name_city):
            signal_members.setdefault(("EXACT_NAME_CITY", "\x1f".join(name_city)), []).append(key)

    for members in signal_members.values():
        if len(members) > 1:
            anchor = min(members)
            for member in members:
                uf.union(anchor, member)

    components: dict[str, list[str] = {}
    for key in keys:
        components.setdefault(uf.find(key), []).append(key)

    duplicate_groups: list[dict[str, object]] = []
    duplicate_keys: set[str] = set()
    for members in sorted((sorted(v) for v in components.values() if len(v) > 1), key=lambda v: v[0]):
        member_set = set(members)
        signals: list[str] = []
        for (signal, _value), signal_keys in signal_members.items():
            if len(member_set.intersection(signal_keys)) > 1:
                signals.append(signal)
        group_id = "ER-" + hashlib.sha256("|".join(members).encode("utf-8")).hexdigest()[:20]
        duplicate_keys.update(members)
        duplicate_groups.append(
            {
                "group_id": group_id,
                "resolution_state": DUPLICATE_REVIEW,
                "signals": sorted(set(signals)),
                "members": [records[key] for key in members],
            }
        )

    unique_keys = [key for key in keys if key not in duplicate_keys]
    workset: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "source_records": len(records),
        "exact_current_verified_records": expected_records,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_records": len(duplicate_keys),
        "unique_records": len(unique_keys),
        "entity_group_candidates": len(unique_keys) + len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
        "unique_source_record_keys": unique_keys,
        "resolution_policy": "EXACT_SIGNALS_ONLY_FAIL_CLOSED",
        "terminal_mapping_effect": "NONE",
        "canonical_id_allocation_allowed": False,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "workset_sha256": "",
    }
    workset["workset_sha256"] = _sha256(
        {key: value for key, value in workset.items() if key != "workset_sha256"}
    )
    violations = validate_workset(workset)
    if violations:
        raise EntityResolutionError(";".join(violations))
    return workset


def validate_workset(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        violations.append("INVALID_SCHEMA_VERSION")
    if bool(payload.get("authority_advanced")):
        violations.append("AUTHORITY_ADVANCED_FORBIDDEN")
    if int(payload.get("h_id_allocations", 0)) != 0:
        violations.append("H_ID_ALLOCATIONS_FORBIDDEN")
    if bool(payload.get("canonical_id_allocation_allowed")):
        violations.append("CANONICAL_ID_ALLOCATION_FORBIDDEN")
    if payload.get("terminal_mapping_effect") != "NONE":
        violations.append("TERMINAL_MAPPING_EFFECT_FORBIDDEN")
    if payload.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")
    if int(payload.get("send_allowed", 0)) != 0:
        violations.append("SEND_ALLOWED_NOT_ZERO")

    groups = payload.get("duplicate_groups")
    unique = payload.get("unique_source_record_keys")
    if not isinstance(groups, list):
        violations.append("DUPLICATE_GROUPS_NOT_ARRAY")
        groups = []
    if not isinstance(unique, list):
        violations.append("UNIQUE_KEYS_NOT_ARRAY")
        unique = []

    seen: set[str] = set()
    duplicate_records = 0
    for group in groups:
        if not isinstance(group, Mapping):
            violations.append("DUPLICATE_GROUP_NOT_OBJECT")
            continue
        if group.get("resolution_state") != DUPLICATE_REVIEW:
            violations.append("INVALID_DUPLICATE_GROUP_STATE")
        members = group.get("members")
        if not isinstance(members, list) or len(members) < 2:
            violations.append("DUPLICATE_GROUP_TOO_SMALL")
            continue
        duplicate_records += len(members)
        member_keys = [str(item.get("source_record_key", "")).strip() for item in members if isinstance(item, Mapping)]
        if len(member_keys) != len(members) or len(member_keys) != len(set(member_keys)):
            violations.append("INVALID_GROUP_MEMBER_KEYS")
        for key in member_keys:
            if not key or key in seen:
                violations.append("OVERLAPPING_OR_EMPTY_SOURCE_KEY")
            seen.add(key)

    for key in unique:
        value = str(key).strip()
        if not value or value in seen:
            violations.append("OVERLAPPING_OR_EMPTY_SOURCE_KEY")
        seen.add(value)

    if int(payload.get("duplicate_records", -1)) != duplicate_records:
        violations.append("DUPLICATE_RECORD_COUNT_MISMATCH")
    if int(payload.get("unique_records", -1)) != len(unique):
        violations.append("UNIQUE_RECORD_COUNT_MISMATCH")
    if int(payload.get("source_records", -1)) != len(seen):
        violations.append("SOURCE_RECORD_COUNT_MISMATCH")
    if int(payload.get("exact_current_verified_records", -1)) != int(payload.get("source_records", -2)):
        violations.append("EXACT_CURRENT_COVERAGE_MISMATCH")
    if int(payload.get("duplicate_group_count", -1)) != len(groups):
        violations.append("DUPLICATE_GROUP_COUNT_MISMATCH")
    if int(payload.get("entity_group_candidates", -1)) != len(unique) + len(groups):
        violations.append("ENTITY_GROUP_CANDIDATE_COUNT_MISMATCH")

    expected_sha = _sha256({key: value for key, value in payload.items() if key != "workset_sha256"})
    if payload.get("workset_sha256") != expected_sha:
        violations.append("WORKSET_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.preauth_entity_resolution")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("state_dir")
    build.add_argument("--next", dest="next_path", required=True)
    build.add_argument("--snapshot-id", required=True)
    build.add_argument("--expected-records", required=True, type=int)
    build.add_argument("--out", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            workset = build_workset(
                args.state_dir,
                next_path=args.next_path,
                snapshot_id=args.snapshot_id,
                expected_records=args.expected_records,
            )
            _write_json(Path(args.out), workset)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "snapshot_id": workset["snapshot_id"],
                        "source_records": workset["source_records"],
                        "duplicate_group_count": workset["duplicate_group_count"],
                        "duplicate_records": workset["duplicate_records"],
                        "unique_records": workset["unique_records"],
                        "entity_group_candidates": workset["entity_group_candidates"],
                        "workset_sha256": workset["workset_sha256"],
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

        raw = _read_json(Path(args.path))
        if not isinstance(raw, Mapping):
            raise EntityResolutionError("workset must be a JSOn object")
        violations = validate_workset(raw)
        print(json.dumps({"valid": not violations, "violations": list(violations)}, indent=2, sort_keys=True))
        return 0 if not violations else 2
    except (EntityResolutionError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
