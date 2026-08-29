from __future__ import annotations

from dataclasses import dataclass
import argparse
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
_PUBLIC_SUMMARY_SCHEMA_VERSION = "CEP-PUBLIC-SUMMARY-1.0"
_SOURCE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{2,255}$")


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_identity_component(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip())
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    folded = without_marks.casefold()
    return " ".join(re.findall(r"[a-z0-9]+", folded))


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
            raise ValueError("candidate records must contain only mapping rows")

        provider_key = row.get("provider_record_key")
        source_key = row.get("source_record_key")
        if provider_key not in (None, "") and source_key not in (None, ""):
            if not isinstance(provider_key, str) or not isinstance(source_key, str):
                raise ValueError("candidate source keys must be strings")
            if provider_key.strip() != source_key.strip():
                raise ValueError(
                    "provider_record_key and source_record_key disagree"
                )
        raw_key = provider_key if provider_key not in (None, "") else source_key
        raw_name = row.get("raw_name", row.get("name"))
        raw_city = row.get("raw_city", row.get("city"))
        raw_detail = row.get("detail_url", "")
        raw_source = row.get("source_url", "")

        for label, value in {
            "source_record_key": raw_key,
            "name": raw_name,
            "city": raw_city,
            "detail_url": raw_detail,
            "source_url": raw_source,
        }.items():
            if value is None:
                value = ""
            if not isinstance(value, str):
                raise ValueError(f"{label} must be a string")

        key = str(raw_key or "").strip()
        name = str(raw_name or "").strip()
        city = str(raw_city or "").strip()
        detail_url = normalize_url(str(raw_detail or ""))
        source_url = normalize_url(str(raw_source or ""))

        if not key or not _SOURCE_KEY_RE.fullmatch(key):
            raise ValueError(f"invalid source_record_key: {key!r}")
        if not name:
            raise ValueError(f"candidate {key} is missing name")
        if not city:
            raise ValueError(f"candidate {key} is missing city")

        return cls(
            source_record_key=key,
            name=name,
            city=city,
            detail_url=detail_url,
            source_url=source_url,
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


def load_candidate_export(
    gzip_path: str | Path,
    manifest_path: str | Path,
) -> LoadedCandidateExport:
    archive_path = Path(gzip_path)
    metadata_path = Path(manifest_path)
    manifest = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, Mapping):
        raise ValueError("candidate export manifest must be a JSON object")

    snapshot_id = manifest.get("snapshot_id")
    expected_gzip_sha = manifest.get("gzip_sha256")
    expected_records_sha = manifest.get("records_sha256")
    expected_count = manifest.get("records_count")
    for label, value in {
        "snapshot_id": snapshot_id,
        "gzip_sha256": expected_gzip_sha,
        "records_sha256": expected_records_sha,
    }.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"manifest {label} is required")
    if isinstance(expected_count, bool) or not isinstance(expected_count, int):
        raise ValueError("manifest records_count must be an integer")
    if expected_count < 1:
        raise ValueError("manifest records_count must be positive")

    compressed = archive_path.read_bytes()
    actual_gzip_sha = _sha256_bytes(compressed)
    if actual_gzip_sha != expected_gzip_sha:
        raise ValueError(
            f"candidate gzip SHA mismatch: {actual_gzip_sha} != {expected_gzip_sha}"
        )

    try:
        raw = gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        raise ValueError("candidate export is not valid gzip") from exc
    actual_records_sha = _sha256_bytes(raw)
    if actual_records_sha != expected_records_sha:
        raise ValueError(
            "candidate records SHA mismatch: "
            f"{actual_records_sha} != {expected_records_sha}"
        )

    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("candidate export payload must be a JSON array")
    if len(payload) != expected_count:
        raise ValueError(
            f"candidate export count {len(payload)} != manifest {expected_count}"
        )

    records = tuple(CandidateEntityRecord.from_mapping(row) for row in payload)
    seen: set[str] = set()
    for record in records:
        if record.source_record_key in seen:
            raise ValueError(
                f"duplicate source_record_key: {record.source_record_key}"
            )
        seen.add(record.source_record_key)

    return LoadedCandidateExport(
        snapshot_id=str(snapshot_id).strip(),
        records_sha256=str(expected_records_sha),
        gzip_sha256=str(expected_gzip_sha),
        records=records,
    )


def _cluster_id(member_keys: Sequence[str]) -> str:
    digest = _sha256_bytes("|".join(member_keys).encode("utf-8"))[:20]
    return f"CEP-{digest}"


def _conflict_id(kind: str, member_keys: Sequence[str]) -> str:
    digest = _sha256_bytes(
        f"{kind}|{'|'.join(member_keys)}".encode("utf-8")
    )[:20]
    return f"CEPC-{digest}"


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
    if source_records_sha256 and not re.fullmatch(
        r"[0-9a-f]{64}", source_records_sha256
    ):
        raise ValueError("source_records_sha256 must be lowercase SHA-256")
    if source_gzip_sha256 and not re.fullmatch(
        r"[0-9a-f]{64}", source_gzip_sha256
    ):
        raise ValueError("source_gzip_sha256 must be lowercase SHA-256")

    materialized = tuple(
        item
        if isinstance(item, CandidateEntityRecord)
        else CandidateEntityRecord.from_mapping(item)
        for item in records
    )
    if not materialized:
        raise ValueError("at least one candidate record is required")

    by_key: dict[str, CandidateEntityRecord] = {}
    for record in materialized:
        if record.source_record_key in by_key:
            raise ValueError(
                f"duplicate source_record_key: {record.source_record_key}"
            )
        by_key[record.source_record_key] = record

    url_groups: dict[str, list[str]] = {}
    for record in materialized:
        if record.detail_url:
            url_groups.setdefault(record.detail_url, []).append(
                record.source_record_key
            )

    assigned: set[str] = set()
    clusters: list[dict[str, object]] = []
    source_to_cluster: dict[str, str] = {}

    for detail_url, keys in sorted(url_groups.items()):
        unique_keys = sorted(set(keys))
        if len(unique_keys) < 2:
            continue
        cluster_id = _cluster_id(unique_keys)
        cluster = {
            "cluster_id": cluster_id,
            "partition_state": "STABLE_SAME_ENTITY_CLUSTER",
            "stable_identity_basis": "EXACT_DETAIL_URL",
            "stable_identity_ref": detail_url,
            "leader_source_record_key": unique_keys[0],
            "member_source_record_keys": unique_keys,
            "members_count": len(unique_keys),
        }
        clusters.append(cluster)
        for key in unique_keys:
            assigned.add(key)
            source_to_cluster[key] = cluster_id

    for key in sorted(by_key):
        if key in assigned:
            continue
        record = by_key[key]
        cluster_id = _cluster_id([key])
        cluster = {
            "cluster_id": cluster_id,
            "partition_state": "SINGLETON_DISTINCT_CANDIDATE",
            "stable_identity_basis": (
                "UNIQUE_EXACT_DETAIL_URL"
                if record.detail_url
                else "SOURCE_RECORD_ONLY"
            ),
            "stable_identity_ref": record.detail_url or key,
            "leader_source_record_key": key,
            "member_source_record_keys": [key],
            "members_count": 1,
        }
        clusters.append(cluster)
        source_to_cluster[key] = cluster_id

    clusters.sort(key=lambda item: str(item["leader_source_record_key"]))

    name_city_groups: dict[tuple[str, str], list[str]] = {}
    for record in materialized:
        name_city_groups.setdefault(record.name_city_key, []).append(
            record.source_record_key
        )

    conflicts: list[dict[str, object]] = []
    review_keys: set[str] = set()

    for (normalized_name, normalized_city), keys in sorted(
        name_city_groups.items()
    ):
        unique_keys = sorted(set(keys))
        cluster_ids = sorted({source_to_cluster[key] for key in unique_keys})
        if len(unique_keys) < 2 or len(cluster_ids) == 1:
            continue
        detail_urls = sorted(
            {
                by_key[key].detail_url
                for key in unique_keys
                if by_key[key].detail_url
            }
        )
        conflict = {
            "conflict_id": _conflict_id(
                "NAME_CITY_MULTIPLE_STABLE_IDENTITIES", unique_keys
            ),
            "conflict_type": "NAME_CITY_MULTIPLE_STABLE_IDENTITIES",
            "normalized_name": normalized_name,
            "normalized_city": normalized_city,
            "member_source_record_keys": unique_keys,
            "candidate_cluster_ids": cluster_ids,
            "detail_urls": detail_urls,
            "required_action": "EXPLICIT_ENTITY_REVIEW_NO_AUTOMERGE",
        }
        conflicts.append(conflict)
        review_keys.update(unique_keys)

    missing_detail_records = sorted(
        record.source_record_key
        for record in materialized
        if not record.detail_url
    )
    for key in missing_detail_records:
        conflict = {
            "conflict_id": _conflict_id("MISSING_DETAIL_URL", [key]),
            "conflict_type": "MISSING_DETAIL_URL",
            "normalized_name": by_key[key].name_city_key[0],
            "normalized_city": by_key[key].name_city_key[1],
            "member_source_record_keys": [key],
            "candidate_cluster_ids": [source_to_cluster[key]],
            "detail_urls": [],
            "required_action": "REFRESH_STABLE_ENTITY_DETAIL",
        }
        conflicts.append(conflict)
        review_keys.add(key)

    conflicts.sort(key=lambda item: str(item["conflict_id"]))

    assigned_keys = [
        key
        for cluster in clusters
        for key in cluster["member_source_record_keys"]
    ]
    assignment_duplicates = len(assigned_keys) - len(set(assigned_keys))
    omitted_keys = sorted(set(by_key) - set(assigned_keys))
    foreign_keys = sorted(set(assigned_keys) - set(by_key))

    if assignment_duplicates or omitted_keys or foreign_keys:
        raise ValueError("candidate partition assignment invariant failed")

    stable_clusters = [
        cluster
        for cluster in clusters
        if cluster["partition_state"] == "STABLE_SAME_ENTITY_CLUSTER"
    ]
    singleton_clusters = [
        cluster
        for cluster in clusters
        if cluster["partition_state"] == "SINGLETON_DISTINCT_CANDIDATE"
    ]
    partition_state = (
        "EXACT_PARTITION"
        if not conflicts
        else "PARTITION_COMPLETE_REVIEW_REQUIRED"
    )

    partition_core = {
        "snapshot_id": snapshot,
        "source_records_sha256": source_records_sha256,
        "source_gzip_sha256": source_gzip_sha256,
        "clusters": clusters,
        "review_conflicts": conflicts,
    }
    partition_sha = _sha256_bytes(_canonical_json_bytes(partition_core))

    return {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": snapshot,
        "partition_state": partition_state,
        "partition_sha256": partition_sha,
        "source_records_sha256": source_records_sha256,
        "source_gzip_sha256": source_gzip_sha256,
        "summary": {
            "candidate_records": len(materialized),
            "partition_clusters": len(clusters),
            "singleton_clusters": len(singleton_clusters),
            "stable_detail_url_clusters": len(stable_clusters),
            "stable_detail_url_cluster_members": sum(
                int(cluster["members_count"])
                for cluster in stable_clusters
            ),
            "review_conflict_groups": len(conflicts),
            "review_required_records": len(review_keys),
            "name_city_collision_groups": sum(
                conflict["conflict_type"]
                == "NAME_CITY_MULTIPLE_STABLE_IDENTITIES"
                for conflict in conflicts
            ),
            "missing_detail_url_records": len(missing_detail_records),
            "exact_assignment_count": len(assigned_keys),
            "assignment_duplicates": assignment_duplicates,
            "omitted_source_records": len(omitted_keys),
            "foreign_source_records": len(foreign_keys),
            "proposed_distinct_candidate_entities": len(clusters),
        },
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
    if partition.get("schema_version") != SCHEMA_VERSION:
        violations.append("schema_version must be CEP-1.0")
    snapshot_id = partition.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        violations.append("snapshot_id is required")

    summary = partition.get("summary")
    clusters = partition.get("clusters")
    conflicts = partition.get("review_conflicts")
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
    seen_cluster_ids: set[str] = set()
    for cluster in clusters:
        if not isinstance(cluster, Mapping):
            violations.append("clusters must contain only objects")
            continue
        cluster_id = cluster.get("cluster_id")
        members = cluster.get("member_source_record_keys")
        leader = cluster.get("leader_source_record_key")
        if not isinstance(cluster_id, str) or not cluster_id.startswith("CEP-"):
            violations.append("invalid cluster_id")
        elif cluster_id in seen_cluster_ids:
            violations.append(f"duplicate cluster_id: {cluster_id}")
        else:
            seen_cluster_ids.add(cluster_id)
        if not isinstance(members, list) or not members:
            violations.append(f"cluster {cluster_id} has no members")
            continue
        if not all(isinstance(key, str) and key for key in members):
            violations.append(f"cluster {cluster_id} has invalid member key")
            continue
        if len(members) != len(set(members)):
            violations.append(f"cluster {cluster_id} repeats a member")
        if leader not in members:
            violations.append(f"cluster {cluster_id} leader is not a member")
        if leader != sorted(members)[0]:
            violations.append(
                f"cluster {cluster_id} leader is not deterministic"
            )
        assigned.extend(members)

    candidate_records = summary.get("candidate_records")
    exact_assignments = summary.get("exact_assignment_count")
    if (
        isinstance(candidate_records, bool)
        or not isinstance(candidate_records, int)
        or candidate_records < 1
    ):
        violations.append("summary candidate_records must be positive integer")
    if exact_assignments != len(assigned):
        violations.append("summary exact_assignment_count mismatch")
    if len(assigned) != len(set(assigned)):
        violations.append("source record assigned to multiple clusters")
    if candidate_records != len(set(assigned)):
        violations.append("candidate record count does not match assignments")

    if partition.get("authority_advanced") is not False:
        violations.append("authority_advanced must be false")
    if partition.get("h_id_allocations") != 0 or isinstance(
        partition.get("h_id_allocations"), bool
    ):
        violations.append("h_id_allocations must be integer zero")
    if partition.get("canonical_id_reservations") != 0 or isinstance(
        partition.get("canonical_id_reservations"), bool
    ):
        violations.append("canonical_id_reservations must be integer zero")
    if partition.get("outbound") != "CLOSED":
        violations.append("outbound must be CLOSED")
    if partition.get("outbound_opened") is not False:
        violations.append("outbound_opened must be false")
    if partition.get("send_allowed") != 0 or isinstance(
        partition.get("send_allowed"), bool
    ):
        violations.append("send_allowed must be integer zero")

    core = {
        "snapshot_id": partition.get("snapshot_id"),
        "source_records_sha256": partition.get("source_records_sha256", ""),
        "source_gzip_sha256": partition.get("source_gzip_sha256", ""),
        "clusters": clusters,
        "review_conflicts": conflicts,
    }
    expected_sha = _sha256_bytes(_canonical_json_bytes(core))
    if partition.get("partition_sha256") != expected_sha:
        violations.append("partition_sha256 mismatch")
    return tuple(violations)


def build_public_summary(
    partition: Mapping[str, object],
) -> dict[str, object]:
    violations = validate_candidate_entity_partition(partition)
    summary = partition.get("summary")
    return {
        "schema_version": _PUBLIC_SUMMARY_SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": partition.get("snapshot_id"),
        "partition_state": partition.get("partition_state"),
        "partition_sha256": partition.get("partition_sha256"),
        "source_records_sha256": partition.get("source_records_sha256"),
        "source_gzip_sha256": partition.get("source_gzip_sha256"),
        "summary": dict(summary) if isinstance(summary, Mapping) else {},
        "validation_pass": not violations,
        "validation_violations": list(violations),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "outbound_opened": False,
        "send_allowed": 0,
    }


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_canonical_json_bytes(payload))


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
        args.candidate_export_gzip,
        args.candidate_export_manifest,
    )
    partition = build_candidate_entity_partition(
        loaded.snapshot_id,
        loaded.records,
        source_records_sha256=loaded.records_sha256,
        source_gzip_sha256=loaded.gzip_sha256,
    )
    violations = validate_candidate_entity_partition(partition)
    _write_json(args.out, partition)
    _write_json(args.summary_out, build_public_summary(partition))
    print(
        json.dumps(
            {
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
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not violations else 2


if __name__ == "__main__":
    sys.exit(main())
