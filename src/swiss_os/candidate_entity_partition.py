from __future__ import annotations

from dataclasses import dataclass
import argparse
import base64
import binascii
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Iterable, Mapping, Sequence

from .snapshot_freeze import normalize_url


SCHEMA_VERSION = "CEP-1.0"
PUBLIC_SUMMARY_SCHEMA_VERSION = "CEP-PUBLIC-SUMMARY-1.0"
_SOURCE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{2,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_identity_component(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip())
    asciiish = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(re.findall(r"[a-z0-9]+", asciiish.casefold()))


@dataclass(frozen=True)
class CandidateEntityRecord:
    source_record_key: str
    name: str
    city: str
    detail_url: str
    source_url: str = ""

    @classmethod
    def from_mapping(cls, row: Mapping[str, object]) -> "CandidateEntityRecord":
        if not isinstance(row, Mapping):
            raise ValueError("candidate records must contain only objects")
        provider_key = row.get("provider_record_key")
        source_key = row.get("source_record_key")
        if provider_key not in (None, "") and source_key not in (None, ""):
            if not isinstance(provider_key, str) or not isinstance(source_key, str):
                raise ValueError("candidate source keys must be strings")
            if provider_key.strip() != source_key.strip():
                raise ValueError("provider_record_key and source_record_key disagree")
        key = provider_key if provider_key not in (None, "") else source_key
        values = {
            "source_record_key": key,
            "name": row.get("raw_name", row.get("name")),
            "city": row.get("raw_city", row.get("city")),
            "detail_url": row.get("detail_url", ""),
            "source_url": row.get("source_url", ""),
        }
        if any(value is not None and not isinstance(value, str) for value in values.values()):
            raise ValueError("candidate identity fields must be strings")
        key_text = str(values["source_record_key"] or "").strip()
        name = str(values["name"] or "").strip()
        city = str(values["city"] or "").strip()
        if not _SOURCE_KEY_RE.fullmatch(key_text):
            raise ValueError(f"invalid source_record_key: {key_text!r}")
        if not name:
            raise ValueError(f"candidate {key_text} is missing name")
        if not city:
            raise ValueError(f"candidate {key_text} is missing city")
        return cls(
            source_record_key=key_text,
            name=name,
            city=city,
            detail_url=normalize_url(str(values["detail_url"] or "")),
            source_url=normalize_url(str(values["source_url"] or "")),
        )

    @property
    def name_city_key(self) -> tuple[str, str]:
        return (
            normalize_identity_component(self.name),
            normalize_identity_component(self.city),
        )


@dataclass(frozen=True)
class LoadedCandidateExport:
    snapshot_id: str
    records_sha256: str
    gzip_sha256: str
    records: tuple[CandidateEntityRecord, ...]


def _decode_gzip_transport(path: Path) -> bytes:
    stored = path.read_bytes()
    if stored.startswith(b"\x1f\x8b"):
        return stored
    try:
        decoded = base64.b64decode(b"".join(stored.split()), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            "candidate export is neither gzip nor strict base64(gzip)"
        ) from exc
    if not decoded.startswith(b"\x1f\x8b"):
        raise ValueError("decoded candidate export is not gzip")
    return decoded


def load_candidate_export(
    gzip_path: str | Path,
    manifest_path: str | Path,
) -> LoadedCandidateExport:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(manifest, Mapping):
        raise ValueError("candidate export manifest must be an object")
    snapshot_id = manifest.get("snapshot_id")
    gzip_digest = manifest.get("gzip_sha256")
    records_digest = manifest.get("records_sha256")
    records_count = manifest.get("records_count")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        raise ValueError("manifest snapshot_id is required")
    if not isinstance(gzip_digest, str) or not _SHA256_RE.fullmatch(gzip_digest):
        raise ValueError("manifest gzip_sha256 is invalid")
    if not isinstance(records_digest, str) or not _SHA256_RE.fullmatch(records_digest):
        raise ValueError("manifest records_sha256 is invalid")
    if isinstance(records_count, bool) or not isinstance(records_count, int) or records_count < 1:
        raise ValueError("manifest records_count must be a positive integer")

    compressed = _decode_gzip_transport(Path(gzip_path))
    actual_gzip = sha256(compressed)
    if actual_gzip != gzip_digest:
        raise ValueError(f"candidate gzip SHA mismatch: {actual_gzip} != {gzip_digest}")
    try:
        decoded = json.loads(gzip.decompress(compressed))
    except (OSError, EOFError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("candidate export contains invalid gzip JSON") from exc

    if isinstance(decoded, Mapping):
        records = decoded.get("records")
        if decoded.get("snapshot_id") not in (None, "", snapshot_id):
            raise ValueError("candidate payload snapshot_id disagrees with manifest")
        if decoded.get("records_count") not in (None, records_count):
            raise ValueError("candidate payload records_count disagrees with manifest")
    elif isinstance(decoded, list):
        records = decoded
    else:
        records = None
    if not isinstance(records, list):
        raise ValueError("candidate export records must be an array")
    if len(records) != records_count:
        raise ValueError(
            f"candidate export count {len(records)} != manifest {records_count}"
        )
    actual_records = sha256(canonical_json_bytes(records))
    if actual_records != records_digest:
        raise ValueError(
            f"candidate records SHA mismatch: {actual_records} != {records_digest}"
        )

    parsed = tuple(CandidateEntityRecord.from_mapping(row) for row in records)
    keys = [row.source_record_key for row in parsed]
    if len(keys) != len(set(keys)):
        duplicate = next(key for key in keys if keys.count(key) > 1)
        raise ValueError(f"duplicate source_record_key: {duplicate}")
    return LoadedCandidateExport(
        snapshot_id=snapshot_id.strip(),
        records_sha256=records_digest,
        gzip_sha256=gzip_digest,
        records=parsed,
    )


def _stable_id(prefix: str, kind: str, keys: Sequence[str]) -> str:
    seed = kind + "|" + "|".join(keys)
    return f"{prefix}-{sha256(seed.encode())[:20]}"


def build_candidate_entity_partition(
    snapshot_id: str,
    records: Iterable[CandidateEntityRecord | Mapping[str, object]],
    *,
    source_records_sha256: str = "",
    source_gzip_sha256: str = "",
) -> dict[str, object]:
    snapshot = snapshot_id.strip()
    if not snapshot:
        raise ValueError("snapshot_id is required")
    for label, digest in {
        "source_records_sha256": source_records_sha256,
        "source_gzip_sha256": source_gzip_sha256,
    }.items():
        if digest and not _SHA256_RE.fullmatch(digest):
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

    clusters: list[dict[str, object]] = []
    assigned: dict[str, str] = {}
    for url, members in sorted(url_groups.items()):
        keys = sorted(set(members))
        if len(keys) < 2:
            continue
        cluster_id = _stable_id("CEP", "EXACT_DETAIL_URL", keys)
        clusters.append({
            "cluster_id": cluster_id,
            "partition_state": "STABLE_SAME_ENTITY_CLUSTER",
            "stable_identity_basis": "EXACT_DETAIL_URL",
            "stable_identity_ref": url,
            "leader_source_record_key": keys[0],
            "member_source_record_keys": keys,
            "members_count": len(keys),
        })
        assigned.update({key: cluster_id for key in keys})

    for key, row in sorted(by_key.items()):
        if key in assigned:
            continue
        cluster_id = _stable_id("CEP", "SINGLETON", [key])
        clusters.append({
            "cluster_id": cluster_id,
            "partition_state": "SINGLETON_DISTINCT_CANDIDATE",
            "stable_identity_basis": (
                "UNIQUE_EXACT_DETAIL_URL" if row.detail_url else "SOURCE_RECORD_ONLY"
            ),
            "stable_identity_ref": row.detail_url or key,
            "leader_source_record_key": key,
            "member_source_record_keys": [key],
            "members_count": 1,
        })
        assigned[key] = cluster_id
    clusters.sort(key=lambda row: str(row["leader_source_record_key"]))

    name_city_groups: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        name_city_groups.setdefault(row.name_city_key, []).append(row.source_record_key)

    conflicts: list[dict[str, object]] = []
    review_keys: set[str] = set()
    for (name, city), members in sorted(name_city_groups.items()):
        keys = sorted(set(members))
        cluster_ids = sorted({assigned[key] for key in keys})
        if len(keys) < 2 or len(cluster_ids) == 1:
            continue
        conflicts.append({
            "conflict_id": _stable_id(
                "CEPC", "NAME_CITY_MULTIPLE_STABLE_IDENTITIES", keys
            ),
            "conflict_type": "NAME_CITY_MULTIPLE_STABLE_IDENTITIES",
            "normalized_name": name,
            "normalized_city": city,
            "member_source_record_keys": keys,
            "candidate_cluster_ids": cluster_ids,
            "detail_urls": sorted(
                {by_key[key].detail_url for key in keys if by_key[key].detail_url}
            ),
            "required_action": "EXPLICIT_ENTITY_REVIEW_NO_AUTOMERGE",
        })
        review_keys.update(keys)

    missing_detail = sorted(key for key, row in by_key.items() if not row.detail_url)
    for key in missing_detail:
        name, city = by_key[key].name_city_key
        conflicts.append({
            "conflict_id": _stable_id("CEPC", "MISSING_DETAIL_URL", [key]),
            "conflict_type": "MISSING_DETAIL_URL",
            "normalized_name": name,
            "normalized_city": city,
            "member_source_record_keys": [key],
            "candidate_cluster_ids": [assigned[key]],
            "detail_urls": [],
            "required_action": "REFRESH_STABLE_ENTITY_DETAIL",
        })
        review_keys.add(key)
    conflicts.sort(key=lambda row: str(row["conflict_id"]))

    assigned_keys = [
        key for cluster in clusters for key in cluster["member_source_record_keys"]
    ]
    duplicates = len(assigned_keys) - len(set(assigned_keys))
    omitted = set(by_key) - set(assigned_keys)
    foreign = set(assigned_keys) - set(by_key)
    if duplicates or omitted or foreign:
        raise ValueError("candidate partition assignment invariant failed")

    stable_clusters = [
        row for row in clusters
        if row["partition_state"] == "STABLE_SAME_ENTITY_CLUSTER"
    ]
    summary = {
        "candidate_records": len(rows),
        "partition_clusters": len(clusters),
        "singleton_clusters": len(clusters) - len(stable_clusters),
        "stable_detail_url_clusters": len(stable_clusters),
        "stable_detail_url_cluster_members": sum(
            int(row["members_count"]) for row in stable_clusters
        ),
        "review_conflict_groups": len(conflicts),
        "review_required_records": len(review_keys),
        "name_city_collision_groups": sum(
            row["conflict_type"] == "NAME_CITY_MULTIPLE_STABLE_IDENTITIES"
            for row in conflicts
        ),
        "missing_detail_url_records": len(missing_detail),
        "exact_assignment_count": len(assigned_keys),
        "assignment_duplicates": duplicates,
        "omitted_source_records": len(omitted),
        "foreign_source_records": len(foreign),
        "proposed_distinct_candidate_entities": len(clusters),
    }
    core = {
        "snapshot_id": snapshot,
        "source_records_sha256": source_records_sha256,
        "source_gzip_sha256": source_gzip_sha256,
        "clusters": clusters,
        "review_conflicts": conflicts,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": snapshot,
        "partition_state": (
            "EXACT_PARTITION"
            if not conflicts
            else "PARTITION_COMPLETE_REVIEW_REQUIRED"
        ),
        "partition_sha256": sha256(canonical_json_bytes(core)),
        "source_records_sha256": source_records_sha256,
        "source_gzip_sha256": source_gzip_sha256,
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
    conflicts = partition.get("review_conflicts")
    if partition.get("schema_version") != SCHEMA_VERSION:
        violations.append("schema_version must be CEP-1.0")
    if not isinstance(partition.get("snapshot_id"), str) or not partition["snapshot_id"].strip():
        violations.append("snapshot_id is required")
    if not isinstance(summary, Mapping):
        violations.append("summary must be an object")
        summary = {}
    if not isinstance(clusters, list):
        violations.append("clusters must be an array")
        clusters = []
    if not isinstance(conflicts, list):
        violations.append("review_conflicts must be an array")
        conflicts = []

    assigned: list[str] = []
    cluster_ids: set[str] = set()
    for cluster in clusters:
        if not isinstance(cluster, Mapping):
            violations.append("clusters must contain only objects")
            continue
        cluster_id = cluster.get("cluster_id")
        members = cluster.get("member_source_record_keys")
        leader = cluster.get("leader_source_record_key")
        if not isinstance(cluster_id, str) or not cluster_id.startswith("CEP-"):
            violations.append("invalid cluster_id")
        elif cluster_id in cluster_ids:
            violations.append(f"duplicate cluster_id: {cluster_id}")
        else:
            cluster_ids.add(cluster_id)
        if not isinstance(members, list) or not members:
            violations.append(f"cluster {cluster_id} has no members")
            continue
        if len(members) != len(set(members)):
            violations.append(f"cluster {cluster_id} repeats a member")
        if leader not in members:
            violations.append(f"cluster {cluster_id} leader is not a member")
        if members and leader != sorted(members)[0]:
            violations.append(f"cluster {cluster_id} leader is not deterministic")
        assigned.extend(key for key in members if isinstance(key, str))

    if summary.get("exact_assignment_count") != len(assigned):
        violations.append("summary exact_assignment_count mismatch")
    if len(assigned) != len(set(assigned)):
        violations.append("source record assigned to multiple clusters")
    if summary.get("candidate_records") != len(set(assigned)):
        violations.append("candidate record count does not match assignments")

    locks = {
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "outbound_opened": False,
        "send_allowed": 0,
    }
    for key, expected in locks.items():
        if partition.get(key) != expected:
            violations.append(f"{key} must be {expected!r}")
    for key in ("h_id_allocations", "canonical_id_reservations", "send_allowed"):
        if isinstance(partition.get(key), bool):
            violations.append(f"{key} must be integer zero")

    core = {
        "snapshot_id": partition.get("snapshot_id"),
        "source_records_sha256": partition.get("source_records_sha256", ""),
        "source_gzip_sha256": partition.get("source_gzip_sha256", ""),
        "clusters": clusters,
        "review_conflicts": conflicts,
    }
    if partition.get("partition_sha256") != sha256(canonical_json_bytes(core)):
        violations.append("partition_sha256 mismatch")
    return tuple(violations)


def build_public_summary(partition: Mapping[str, object]) -> dict[str, object]:
    violations = validate_candidate_entity_partition(partition)
    return {
        "schema_version": PUBLIC_SUMMARY_SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": partition.get("snapshot_id"),
        "partition_state": partition.get("partition_state"),
        "partition_sha256": partition.get("partition_sha256"),
        "source_records_sha256": partition.get("source_records_sha256"),
        "source_gzip_sha256": partition.get("source_gzip_sha256"),
        "summary": dict(partition.get("summary", {})),
        "validation_pass": not violations,
        "validation_violations": list(violations),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "outbound_opened": False,
        "send_allowed": 0,
    }


def write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_json_bytes(payload) + b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m swiss_os.candidate_entity_partition"
    )
    parser.add_argument("candidate_export_gzip")
    parser.add_argument("candidate_export_manifest")
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary-out", required=True)
    args = parser.parse_args(argv)
    loaded = load_candidate_export(
        args.candidate_export_gzip, args.candidate_export_manifest
    )
    partition = build_candidate_entity_partition(
        loaded.snapshot_id,
        loaded.records,
        source_records_sha256=loaded.records_sha256,
        source_gzip_sha256=loaded.gzip_sha256,
    )
    violations = validate_candidate_entity_partition(partition)
    write_json(args.out, partition)
    write_json(args.summary_out, build_public_summary(partition))
    print(json.dumps({
        "snapshot_id": loaded.snapshot_id,
        "partition_state": partition["partition_state"],
        "partition_sha256": partition["partition_sha256"],
        "summary": partition["summary"],
        "validation_pass": not violations,
        "validation_violations": list(violations),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "out": args.out,
        "summary_out": args.summary_out,
    }, indent=2, sort_keys=True))
    return 0 if not violations else 2


if __name__ == "__main__":
    sys.exit(main())
