from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .crm_universe import (
    CRMUniverseMetrics,
    inspect_crm_snapshot,
    validate_crm_universe_gate,
)
from .db import connect, foreign_key_violations, initialize, integrity_check
from .ingest_scheduler import enqueue_ingest_work
from .invariants import run_manifest_invariants
from .manifest import OperationalManifest
from .mass_ingest import classify_batch, stage_decisions, staging_metrics
from .snapshot_freeze import SnapshotFreezeCandidate, SnapshotSourceRecord, validate_snapshot_freeze


def cmd_manifest_validate(path: str) -> int:
    manifest = OperationalManifest.load(path)
    results = run_manifest_invariants(manifest)
    payload = {
        "manifest": manifest.public_summary(),
        "invariants": [r.__dict__ for r in results],
        "pass": all(r.passed for r in results),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["pass"] else 2


def cmd_db_init(path: str) -> int:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect(target) as conn:
        initialize(conn)
    print(json.dumps({"db": str(target), "initialized": True}))
    return 0


def cmd_db_check(path: str) -> int:
    with connect(path) as conn:
        integrity = integrity_check(conn)
        fk = foreign_key_violations(conn)
    payload = {
        "db": path,
        "integrity_check": integrity,
        "foreign_key_violations": len(fk),
        "pass": integrity.lower() == "ok" and not fk,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["pass"] else 2


def cmd_crm_universe_validate(path: str) -> int:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    metrics = CRMUniverseMetrics(
        snapshot_id=str(payload.get("snapshot_id", "")),
        snapshot_state=str(payload.get("snapshot_state", "")),
        snapshot_raw_records=int(payload.get("snapshot_raw_records", 0)),
        active_canonical_mappings=int(payload.get("active_canonical_mappings", 0)),
        alias_to_canonical_mappings=int(payload.get("alias_to_canonical_mappings", 0)),
        excluded_with_reason_mappings=int(payload.get("excluded_with_reason_mappings", 0)),
        reconcile_required=int(payload.get("reconcile_required", 0)),
        unmapped_records=int(payload.get("unmapped_records", 0)),
        unresolved_duplicate_conflicts=int(payload.get("unresolved_duplicate_conflicts", 0)),
        invalid_alias_targets=int(payload.get("invalid_alias_targets", 0)),
        constrained_active_canonical=int(payload.get("constrained_active_canonical", 0)),
        sheets_active_canonical=int(payload.get("sheets_active_canonical", 0)),
        graph_active_canonical=int(payload.get("graph_active_canonical", 0)),
        intelligence_active_canonical=int(payload.get("intelligence_active_canonical", 0)),
        db_sheets_exact=bool(payload.get("db_sheets_exact", False)),
        graph_exact=bool(payload.get("graph_exact", False)),
        intelligence_exact=bool(payload.get("intelligence_exact", False)),
        coverage_snapshot_ids=tuple(payload.get("coverage_snapshot_ids", ())),
    )
    result = validate_crm_universe_gate(metrics)
    output = {
        "snapshot_id": metrics.snapshot_id,
        "snapshot_state": metrics.snapshot_state,
        "crm_universe_complete": result.complete,
        **result.as_dict(),
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if result.complete else 2


def cmd_crm_universe_inspect_db(db_path: str, snapshot_id: str) -> int:
    with connect(db_path) as conn:
        stats = inspect_crm_snapshot(conn, snapshot_id)
    print(json.dumps(stats.as_dict(), indent=2, sort_keys=True))
    return 0


def cmd_crm_snapshot_freeze_validate(path: str) -> int:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    candidate = SnapshotFreezeCandidate(
        snapshot_id=str(payload.get("snapshot_id", "")),
        locale=str(payload.get("locale", "")),
        source_url=str(payload.get("source_url", "")),
        expected_pages=int(payload.get("expected_pages", 0)),
        observed_pages=int(payload.get("observed_pages", 0)),
        declared_raw_records=int(payload.get("declared_raw_records", 0)),
        materialized_records=int(payload.get("materialized_records", 0)),
        duplicate_source_record_keys=int(payload.get("duplicate_source_record_keys", 0)),
        unresolved_snapshot_conflicts=int(payload.get("unresolved_snapshot_conflicts", 0)),
        missing_record_identity=int(payload.get("missing_record_identity", 0)),
    )
    result = validate_snapshot_freeze(candidate)
    output = {
        "snapshot_id": candidate.snapshot_id,
        "freeze_eligible": result.eligible,
        **result.as_dict(),
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if result.eligible else 2


def cmd_crm_ingest_stage(db_path: str, snapshot_id: str, records_path: str, observed_at: str) -> int:
    payload = json.loads(Path(records_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("records payload must be a JSON array")
    records = [
        SnapshotSourceRecord(
            source_url=str(item.get("source_url", "")),
            raw_name=str(item.get("raw_name", "")),
            raw_city=str(item.get("raw_city", "")),
            detail_url=str(item.get("detail_url", "")),
            provider_record_key=str(item.get("provider_record_key", "")),
        )
        for item in payload
    ]
    with connect(db_path) as conn:
        decisions = classify_batch(conn, snapshot_id, records)
        stage_decisions(conn, decisions, observed_at)
        scheduler = enqueue_ingest_work(conn, decisions)
    output = {
        "snapshot_id": snapshot_id,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "metrics": staging_metrics(decisions),
        "scheduler": scheduler,
        "decisions": [d.as_dict() for d in decisions],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swiss-os")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="Validate a public-safe operational manifest")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    validate = manifest_sub.add_parser("validate")
    validate.add_argument("path")

    db = sub.add_parser("db", help="Initialize/check a constrained SQLite database")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    init = db_sub.add_parser("init")
    init.add_argument("path")
    check = db_sub.add_parser("check")
    check.add_argument("path")

    crm = sub.add_parser("crm-universe", help="Inspect and evaluate the CUP-1.0 CRM universe contract")
    crm_sub = crm.add_subparsers(dest="crm_command", required=True)
    crm_validate = crm_sub.add_parser("validate")
    crm_validate.add_argument("path", help="Path to a JSON CRM-universe metrics payload")
    crm_inspect = crm_sub.add_parser("inspect-db")
    crm_inspect.add_argument("db_path", help="Path to the constrained SQLite database")
    crm_inspect.add_argument("snapshot_id", help="CRM snapshot ID to inspect")

    snapshot = sub.add_parser("crm-snapshot", help="Validate coherent snapshot freeze candidates")
    snapshot_sub = snapshot.add_subparsers(dest="snapshot_command", required=True)
    freeze_validate = snapshot_sub.add_parser("freeze-validate")
    freeze_validate.add_argument("path", help="Path to a JSON snapshot candidate payload")

    ingest = sub.add_parser("crm-ingest", help="Classify and persist non-authoritative CRM staging")
    ingest_sub = ingest.add_subparsers(dest="ingest_command", required=True)
    ingest_stage = ingest_sub.add_parser("stage")
    ingest_stage.add_argument("db_path")
    ingest_stage.add_argument("snapshot_id")
    ingest_stage.add_argument("records_path", help="JSON array of source records")
    ingest_stage.add_argument("--observed-at", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "manifest" and args.manifest_command == "validate":
        return cmd_manifest_validate(args.path)
    if args.command == "db" and args.db_command == "init":
        return cmd_db_init(args.path)
    if args.command == "db" and args.db_command == "check":
        return cmd_db_check(args.path)
    if args.command == "crm-universe" and args.crm_command == "validate":
        return cmd_crm_universe_validate(args.path)
    if args.command == "crm-universe" and args.crm_command == "inspect-db":
        return cmd_crm_universe_inspect_db(args.db_path, args.snapshot_id)
    if args.command == "crm-snapshot" and args.snapshot_command == "freeze-validate":
        return cmd_crm_snapshot_freeze_validate(args.path)
    if args.command == "crm-ingest" and args.ingest_command == "stage":
        return cmd_crm_ingest_stage(args.db_path, args.snapshot_id, args.records_path, args.observed_at)
    return 2


if __name__ == "__main__":
    sys.exit(main())
