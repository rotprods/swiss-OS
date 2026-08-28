from __future__ import annotations

"""Durable materializable constrained-parent manifests.

A Composite Constrained Parent (CCP-1.0) represents constrained SQLite state as:

    immutable remote base bytes + pinned deterministic repair definition
    + precommitted materialized SHA-256 + verified materialization proof

It exists for recovery environments where the repaired binary itself cannot be
written back through the active provider connector. It is deliberately fail-closed:
CCP never advances authority, allocates canonical IDs, or opens outbound. Cross-plane
reconciliation remains mandatory before any canonical promotion.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Mapping

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_PROVIDER = {"GOOGLE_DRIVE", "S3", "GCS", "AZURE_BLOB", "PERSISTENT_OPERATOR"}


def _strict_positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a strict positive integer")
    return value


def _strict_nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a strict non-negative integer")
    return value


def _sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field} must be lowercase SHA-256 hex")
    return value


def _git_sha(value: object, field: str) -> str:
    if not isinstance(value, str) or not _GIT_SHA_RE.fullmatch(value):
        raise ValueError(f"{field} must be lowercase 40-char Git SHA hex")
    return value


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_composite_parent(payload: Mapping[str, object]) -> dict[str, object]:
    """Validate CCP-1.0 semantics without granting authority.

    The manifest is a durable constrained-state representation only. Even a valid
    composite remains cross-plane RECONCILE_REQUIRED until DB/Sheets/Intelligence/
    Graph/governance are synchronized in one recovery wave.
    """

    if not isinstance(payload, Mapping):
        raise ValueError("composite parent must be a mapping")
    if payload.get("schema_version") != "CCP-1.0":
        raise ValueError("schema_version must be CCP-1.0")

    _nonempty(payload.get("project"), "project")
    base_sha = _sha256(payload.get("base_sha256"), "base_sha256")
    base_size = _strict_positive_int(payload.get("base_size_bytes"), "base_size_bytes")
    output_sha = _sha256(payload.get("expected_materialized_sha256"), "expected_materialized_sha256")
    if base_sha == output_sha:
        raise ValueError("expected materialized SHA must differ from repair base SHA")

    if payload.get("repair_protocol") != "ARR-1.0":
        raise ValueError("repair_protocol must be ARR-1.0")
    _nonempty(payload.get("repair_plan_path"), "repair_plan_path")
    _git_sha(payload.get("repair_plan_blob_sha"), "repair_plan_blob_sha")
    _git_sha(payload.get("repair_engine_blob_sha"), "repair_engine_blob_sha")
    _git_sha(payload.get("repair_engine_commit_sha"), "repair_engine_commit_sha")

    replicas = payload.get("base_replicas")
    if not isinstance(replicas, list) or not replicas:
        raise ValueError("base_replicas must be a non-empty list")
    seen: set[tuple[str, str]] = set()
    for idx, replica in enumerate(replicas):
        if not isinstance(replica, Mapping):
            raise ValueError("base_replicas must contain mapping rows")
        provider = _nonempty(replica.get("provider"), f"base_replicas[{idx}].provider")
        if provider not in _ALLOWED_PROVIDER:
            raise ValueError(f"unsupported durable provider: {provider}")
        file_id = _nonempty(replica.get("file_id"), f"base_replicas[{idx}].file_id")
        size = _strict_positive_int(replica.get("size_bytes"), f"base_replicas[{idx}].size_bytes")
        if size != base_size:
            raise ValueError("base replica size differs from base_size_bytes")
        key = (provider, file_id)
        if key in seen:
            raise ValueError("duplicate base replica reference")
        seen.add(key)

    proof = payload.get("materialization_proof")
    if not isinstance(proof, Mapping):
        raise ValueError("materialization_proof must be a mapping")
    proof_sha = _sha256(proof.get("output_sha256"), "materialization_proof.output_sha256")
    if proof_sha != output_sha:
        raise ValueError("materialization proof SHA does not match expected output")
    if str(proof.get("integrity_check", "")).lower() != "ok":
        raise ValueError("materialization proof integrity_check must be ok")
    if _strict_nonnegative_int(
        proof.get("foreign_key_violations"), "materialization_proof.foreign_key_violations"
    ) != 0:
        raise ValueError("materialization proof has foreign key violations")
    _strict_positive_int(proof.get("physical_rows"), "materialization_proof.physical_rows")
    _strict_nonnegative_int(proof.get("alias_rows"), "materialization_proof.alias_rows")
    _strict_nonnegative_int(proof.get("superseded_rows"), "materialization_proof.superseded_rows")
    if proof.get("idempotency_replay") != "PASS":
        raise ValueError("materialization proof idempotency_replay must be PASS")

    if payload.get("active_denominator") is not None:
        raise ValueError("CCP must not pre-authorize an active denominator")
    if payload.get("active_denominator_state") != "RECONCILE_REQUIRED_CROSS_PLANE":
        raise ValueError("active_denominator_state must remain RECONCILE_REQUIRED_CROSS_PLANE")
    if payload.get("authority_advanced") is not False:
        raise ValueError("CCP cannot advance authority")
    if payload.get("canonical_id_allocations") != 0 or isinstance(payload.get("canonical_id_allocations"), bool):
        raise ValueError("CCP cannot allocate canonical IDs")
    if payload.get("outbound_opened") is not False:
        raise ValueError("CCP cannot open outbound")
    if payload.get("send_allowed") != 0 or isinstance(payload.get("send_allowed"), bool):
        raise ValueError("CCP send_allowed must be integer 0")

    return {
        "schema_version": "CCP_VALIDATION_V1",
        "valid": True,
        "representation_state": "DURABLE_MATERIALIZABLE_CONSTRAINED_PARENT",
        "base_sha256": base_sha,
        "expected_materialized_sha256": output_sha,
        "base_replica_count": len(replicas),
        "authority_eligible": False,
        "active_denominator": None,
        "active_denominator_state": "RECONCILE_REQUIRED_CROSS_PLANE",
        "authority_advanced": False,
        "canonical_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }


def verify_materialized_sqlite(path: str | Path, manifest: Mapping[str, object]) -> dict[str, object]:
    """Verify one materialization against CCP without mutating any plane."""

    validated = validate_composite_parent(manifest)
    db_path = Path(path)
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    actual_sha = sha256_file(db_path)
    if actual_sha != validated["expected_materialized_sha256"]:
        raise ValueError("materialized SQLite SHA-256 mismatch")

    with sqlite3.connect(db_path) as conn:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        fk_violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    if integrity.lower() != "ok":
        raise ValueError("materialized SQLite failed integrity_check")
    if fk_violations != 0:
        raise ValueError("materialized SQLite has foreign key violations")

    return {
        "schema_version": "CCP_MATERIALIZATION_VERIFY_V1",
        "materialization_state": "EXACT",
        "output_sha256": actual_sha,
        "integrity_check": integrity,
        "foreign_key_violations": fk_violations,
        "authority_eligible": False,
        "active_denominator": None,
        "active_denominator_state": "RECONCILE_REQUIRED_CROSS_PLANE",
        "authority_advanced": False,
        "canonical_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.composite_constrained_parent")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest")
    verify = sub.add_parser("verify")
    verify.add_argument("manifest")
    verify.add_argument("sqlite")
    args = parser.parse_args(argv)

    raw = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("manifest JSON must be an object")
    if args.command == "validate":
        result = validate_composite_parent(raw)
    else:
        result = verify_materialized_sqlite(args.sqlite, raw)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
