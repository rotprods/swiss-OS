from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .cwp_lineage_guard import (
    CwpLineageError,
    _load_multipart_candidate_export,
    validate_candidate_export,
)
from .snapshot_freeze import normalize_url


SCHEMA_VERSION = "CEP-1.1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalize_identity(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip())
    asciiish = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(re.findall(r"[a-z0-9]+", asciiish.casefold()))


def _stable_id(prefix: str, kind: str, keys: Iterable[str]) -> str:
    seed = kind + "|" + "|".join(sorted(keys))
    return f"{prefix}-{_sha256(seed.encode())[:20]}"


@dataclass(frozen=True)
class CandidateEntityRecord:
    source_record_key: str
    name: str
    city: str
    detail_url: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, object]) -> "CandidateEntityRecord":
        if not isinstance(row, Mapping):
            raise ValueError("candidate record must be an object")
        key = row.get("source_record_key")
        name = row.get("name")
        city = row.get("city")
        detail_url = row.get("detail_url", "")
        if not all(isinstance(value, str) for value in (key, name, city, detail_url)):
            raise ValueError("candidate identity fields must be strings")
        key = key.strip()
        name = name.strip()
        city = city.strip()
        if not key or not name or not city:
            raise ValueError("source_record_key, name and city are required")
        return cls(
            source_record_key=key,
            name=name,
            city=city,
            detail_url=normalize_url(detail_url),
        )

    @property
    def name_city_key(self) -> tuple[str, str]:
        return _normalize_identity(self.name), _normalize_identity(self.city)


def build_candidate_entity_partition(
    *,
    snapshot_id: str,
    records: Iterable[CandidateEntityRecord | Mapping[str, object]],
    candidate_records_sha256: str,
    candidate_gzip_sha256: str,
) -> dict[str, Any]:
    if not snapshot_id.strip():
        raise ValueError("snapshot_id is required")
    for label, digest in {
        "candidate_records_sha256": candidate_records_sha256,
        "candidate_gzip_sha256": candidate_gzip_sha256,
    }.items():
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError(f"{label} must be lowercase SHA-256")

    rows = tuple(
        row if isinstance(row, CandidateEntityRecord)
        else CandidateEntityRecord.from_mapping(row)
        for row in records
    )
    if not rows:
        raise ValueError("at least one candidate record is required")
    by_key = {row.source_record_key: row for row in rows}
    if len(by_key) != len(rows):
        raise ValueError("duplicate source_record_key")

    url_groups: dict[str, list[str]] = {}
    for row in rows:
        if row.detail_url:
            url_groups.setdefault(row.detail_url, []).append(row.source_record_key)

    clusters: list[dict[str, Any]] = []
    assigned: dict[str, str] = {}
    for detail_url, members in sorted(url_groups.items()):
        keys = sorted(set(members))
        if len(keys) < 2:
            continue
        cluster_id = _stable_id("CEP", "EXACT_DETAIL_URL", keys)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "partition_state": "STABLE_SAME_ENTITY_CLUSTER",
                "stable_identity_basis": "EXACT_DETAIL_URL",
                "stable_identity_ref": detail_url,
                "leader_source_record_key": keys[0],
                "member_source_record_keys": keys,
                "members_count": len(keys),
            }
        )
        assigned.update({key: cluster_id for key in keys})

    for key, row in sorted(by_key.items()):
        if key in assigned:
            continue
        cluster_id = _stable_id("CEP", "SINGLETON", [key])
        clusters.append(
            {
                "cluster_id": cluster_id,
                "partition_state": "SINGLETON_DISTINCT_CANDIDATE",
                "stable_identity_basis": (
                    "UNIQUE_EXACT_DETAIL_URL" if row.detail_url else "SOURCE_RECORD_ONLY"
                ),
                "stable_identity_ref": row.detail_url or key,
                "leader_source_record_key": key,
                "member_source_record_keys": [key],
                "members_count": 1,
            }
        )
        assigned[key] = cluster_id
    clusters.sort(key=lambda item: str(item["leader_source_record_key"]))

    name_city_groups: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        name_city_groups.setdefault(row.name_city_key, []).append(row.source_record_key)

    conflicts: list[dict[str, Any]] = []
    review_keys: set[str] = set()
    name_city_collision_groups = 0
    for (name, city), members in sorted(name_city_groups.items()):
        keys = sorted(set(members))
        cluster_ids = sorted({assigned[key] for key in keys})
        if len(keys) < 2 or len(cluster_ids) == 1:
            continue
        name_city_collision_groups += 1
        conflicts.append(
            {
                "conflict_id": _stable_id(
                    "CEPC", "NAME_CITY_MULTIPLE_STABLE_IDENTITIES", keys
                ),
                "conflict_type": "NAME_CITY_MULTIPLE_STABLE_IDENTITIES",
                "normalized_name": name,
                "normalized_city": city,
                "member_source_record_keys": keys,
                "candidate_cluster_ids": cluster_ids,
                "required_action": "EXPLICIT_ENTITY_REVIEW_NO_AUTOMERGE",
            }
        )
        review_keys.update(keys)

    missing_detail_keys = sorted(
        key for key, row in by_key.items() if not row.detail_url
    )
    for key in missing_detail_keys:
        conflicts.append(
            {
                "conflict_id": _stable_id("CEPC", "MISSING_DETAIL_URL", [key]),
                "conflict_type": "MISSING_DETAIL_URL",
                "member_source_record_keys": [key],
                "candidate_cluster_ids": [assigned[key]],
                "required_action": "REFRESH_STABLE_ENTITY_DETAIL",
            }
        )
        review_keys.add(key)
    conflicts.sort(key=lambda item: str(item["conflict_id"]))

    assigned_keys = [
        key
        for cluster in clusters
        for key in cluster["member_source_record_keys"]
    ]
    assigned_unique = set(assigned_keys)
    omitted = set(by_key) - assigned_unique
    foreign = assigned_unique - set(by_key)
    duplicate_assignments = len(assigned_keys) - len(assigned_unique)
    if omitted or foreign or duplicate_assignments:
        raise ValueError("candidate partition assignment invariant failed")

    stable_clusters = [
        row
        for row in clusters
        if row["partition_state"] == "STABLE_SAME_ENTITY_CLUSTER"
    ]
    summary: dict[str, Any] = {
        "candidate_records": len(rows),
        "partition_clusters": len(clusters),
        "singleton_clusters": len(clusters) - len(stable_clusters),
        "stable_detail_url_clusters": len(stable_clusters),
        "stable_detail_url_cluster_members": sum(
            int(row["members_count"]) for row in stable_clusters
        ),
        "review_conflict_groups": len(conflicts),
        "review_required_records": len(review_keys),
        "name_city_collision_groups": name_city_collision_groups,
        "missing_detail_url_records": len(missing_detail_keys),
        "exact_assignment_count": len(assigned_keys),
        "assignment_duplicates": duplicate_assignments,
        "omitted_source_records": len(omitted),
        "foreign_source_records": len(foreign),
        "proposed_distinct_candidate_entities": len(clusters),
    }
    core = {
        "snapshot_id": snapshot_id,
        "candidate_records_sha256": candidate_records_sha256,
        "candidate_gzip_sha256": candidate_gzip_sha256,
        "clusters": clusters,
        "review_conflicts": conflicts,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": snapshot_id,
        "partition_state": (
            "EXACT_PARTITION"
            if not conflicts
            else "PARTITION_COMPLETE_REVIEW_REQUIRED"
        ),
        "partition_sha256": _sha256(_canonical_json(core)),
        "candidate_records_sha256": candidate_records_sha256,
        "candidate_gzip_sha256": candidate_gzip_sha256,
        "summary": summary,
        "clusters": clusters,
        "review_conflicts": conflicts,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "outbound_opened": False,
        "send_allowed": 0,
    }


def validate_candidate_entity_partition(
    partition: Mapping[str, object],
) -> tuple[str, ...]:
    violations: list[str] = []
    summary = partition.get("summary")
    clusters = partition.get("clusters")
    if partition.get("schema_version") != SCHEMA_VERSION:
        violations.append("schema_version must be CEP-1.1")
    if not isinstance(summary, Mapping):
        violations.append("summary must be an object")
        return tuple(violations)
    if not isinstance(clusters, list):
        violations.append("clusters must be an array")
        return tuple(violations)
    if summary.get("candidate_records") != summary.get("exact_assignment_count"):
        violations.append("candidate_records must equal exact_assignment_count")
    for field in (
        "assignment_duplicates",
        "omitted_source_records",
        "foreign_source_records",
    ):
        if summary.get(field) != 0:
            violations.append(f"{field} must be zero")
    for field in ("h_id_allocations", "canonical_id_reservations", "send_allowed"):
        value = partition.get(field)
        if value != 0 or isinstance(value, bool):
            violations.append(f"{field} must be integer zero")
    if partition.get("authority_advanced") is not False:
        violations.append("authority_advanced must be false")
    if partition.get("outbound") != "CLOSED":
        violations.append("outbound must be CLOSED")
    if partition.get("outbound_opened") is not False:
        violations.append("outbound_opened must be false")
    digest = partition.get("partition_sha256")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        violations.append("partition_sha256 is invalid")
    return tuple(violations)


def load_current_candidate_partition(
    root: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    payload, gzip_sha, manifest = _load_multipart_candidate_export(
        root.resolve(), manifest_path.resolve()
    )
    candidate_errors = validate_candidate_export(payload)
    if candidate_errors:
        raise CwpLineageError(
            "CANDIDATE_EXPORT_VALIDATION_FAILED:" + ",".join(candidate_errors)
        )
    records = payload.get("records")
    if not isinstance(records, list):
        raise CwpLineageError("CANDIDATE_RECORDS_NOT_ARRAY")
    partition = build_candidate_entity_partition(
        snapshot_id=str(manifest["snapshot_id"]),
        records=records,
        candidate_records_sha256=str(manifest["records_sha256"]),
        candidate_gzip_sha256=gzip_sha,
    )
    violations = validate_candidate_entity_partition(partition)
    if violations:
        raise CwpLineageError("CEP_VALIDATION_FAILED:" + ",".join(violations))
    return partition


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a deterministic pre-authority candidate entity partition"
    )
    parser.add_argument(
        "--manifest",
        default="docs/state/CRM_CANDIDATE_EXPORT_33206402141.manifest.json",
    )
    parser.add_argument("--out-dir", default=".artifacts/cep")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        partition = load_current_candidate_partition(
            root, root / args.manifest
        )
    except (CwpLineageError, ValueError, KeyError) as exc:
        print("candidate_entity_partition: FAIL")
        print(f"- {exc}")
        return 1

    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    full_path = out_dir / "CANDIDATE_ENTITY_PARTITION.json"
    summary_path = out_dir / "CANDIDATE_ENTITY_PARTITION_SUMMARY.json"
    full_path.write_text(
        json.dumps(partition, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    summary_payload = {
        key: value
        for key, value in partition.items()
        if key not in {"clusters", "review_conflicts"}
    }
    summary_payload["summary"] = partition["summary"]
    summary_payload["validation_pass"] = True
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("candidate_entity_partition: PASS")
    print(json.dumps(summary_payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
