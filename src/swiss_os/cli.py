from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .crm_universe import CRMUniverseMetrics, inspect_crm_snapshot, validate_crm_universe_gate
from .db import connect, foreign_key_violations, initialize, integrity_check
from .discover_swiss import (
    DiscoverSwissConfig,
    DiscoverSwissError,
    fetch_hotelleriesuisse_snapshot,
    resolve_subscription_key,
    write_snapshot_manifest,
)
from .ingest_scheduler import enqueue_ingest_work
from .invariants import run_manifest_invariants
from .manifest import OperationalManifest
from .mass_ingest import classify_batch, stage_decisions, staging_metrics
from .member_directory import build_member_directory_manifest, validate_member_directory_manifest
from .meta_execution import MetaCapabilities, choose_meta_route
from .snapshot_freeze import SnapshotFreezeCandidate, SnapshotSourceRecord, validate_snapshot_freeze
from .source_scope import ScopeExplanation, build_candidate_snapshot, reconcile_source_scope


def _read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


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


def cmd_meta_next(path: str) -> int:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("meta capability payload must be a JSON object")
    capabilities = MetaCapabilities.from_mapping(payload)
    decision = choose_meta_route(capabilities)
    out = {
        **decision.as_dict(),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 2 if decision.execution_mode.value == "BLOCKED_P0" else 0


def cmd_member_directory_build(args: argparse.Namespace) -> int:
    payload = _read_json(args.records_json)
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("member-directory records input must be a JSON array of objects")
    manifest = build_member_directory_manifest(
        payload,
        snapshot_id=args.snapshot_id,
        observed_at=args.observed_at,
        locale=args.locale,
        source_url=args.source_url,
        declared_raw_records=args.declared_raw_records,
        expected_pages=args.expected_pages,
        observed_pages=args.observed_pages,
        coverage_complete_requested=args.coverage_complete,
    )
    _write_json(args.out, manifest)
    print(
        json.dumps(
            {
                "snapshot_id": manifest["snapshot_id"],
                "coverage_complete": manifest["coverage_complete"],
                "coverage_violations": manifest["coverage_violations"],
                "materialized_records": manifest["materialized_records"],
                "records_sha256": manifest["records_sha256"],
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound_opened": False,
                "out": args.out,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_member_directory_validate(path: str, require_complete: bool) -> int:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("member-directory manifest must be a JSON object")
    errors = validate_member_directory_manifest(payload)
    complete = payload.get("coverage_complete") is True
    out = {
        "snapshot_id": str(payload.get("snapshot_id", "")),
        "valid": not errors,
        "coverage_complete": complete,
        "errors": list(errors),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors:
        return 2
    if require_complete and not complete:
        return 2
    return 0


def cmd_crm_universe_validate(path: str) -> int:
    p = _read_json(path)
    if not isinstance(p, dict):
        raise ValueError("CRM universe payload must be a JSON object")
    m = CRMUniverseMetrics(
        snapshot_id=str(p.get("snapshot_id", "")),
        snapshot_state=str(p.get("snapshot_state", "")),
        snapshot_raw_records=int(p.get("snapshot_raw_records", 0)),
        active_canonical_mappings=int(p.get("active_canonical_mappings", 0)),
        alias_to_canonical_mappings=int(p.get("alias_to_canonical_mappings", 0)),
        excluded_with_reason_mappings=int(p.get("excluded_with_reason_mappings", 0)),
        reconcile_required=int(p.get("reconcile_required", 0)),
        unmapped_records=int(p.get("unmapped_records", 0)),
        unresolved_duplicate_conflicts=int(p.get("unresolved_duplicate_conflicts", 0)),
        invalid_alias_targets=int(p.get("invalid_alias_targets", 0)),
        constrained_active_canonical=int(p.get("constrained_active_canonical", 0)),
        sheets_active_canonical=int(p.get("sheets_active_canonical", 0)),
        graph_active_canonical=int(p.get("graph_active_canonical", 0)),
        intelligence_active_canonical=int(p.get("intelligence_active_canonical", 0)),
        db_sheets_exact=bool(p.get("db_sheets_exact", False)),
        graph_exact=bool(p.get("graph_exact", False)),
        intelligence_exact=bool(p.get("intelligence_exact", False)),
        coverage_snapshot_ids=tuple(p.get("coverage_snapshot_ids", ())),
    )
    result = validate_crm_universe_gate(m)
    out = {
        "snapshot_id": m.snapshot_id,
        "snapshot_state": m.snapshot_state,
        "crm_universe_complete": result.complete,
        **result.as_dict(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if result.complete else 2


def cmd_crm_universe_inspect_db(db_path: str, snapshot_id: str) -> int:
    with connect(db_path) as conn:
        stats = inspect_crm_snapshot(conn, snapshot_id)
    print(json.dumps(stats.as_dict(), indent=2, sort_keys=True))
    return 0


def cmd_crm_snapshot_freeze_validate(path: str) -> int:
    p = _read_json(path)
    if not isinstance(p, dict):
        raise ValueError("snapshot payload must be a JSON object")
    candidate = SnapshotFreezeCandidate(
        snapshot_id=str(p.get("snapshot_id", "")),
        locale=str(p.get("locale", "")),
        source_url=str(p.get("source_url", "")),
        expected_pages=int(p.get("expected_pages", 0)),
        observed_pages=int(p.get("observed_pages", 0)),
        declared_raw_records=int(p.get("declared_raw_records", 0)),
        materialized_records=int(p.get("materialized_records", 0)),
        duplicate_source_record_keys=int(p.get("duplicate_source_record_keys", 0)),
        unresolved_snapshot_conflicts=int(p.get("unresolved_snapshot_conflicts", 0)),
        missing_record_identity=int(p.get("missing_record_identity", 0)),
    )
    result = validate_snapshot_freeze(candidate)
    print(json.dumps({"snapshot_id": candidate.snapshot_id, "freeze_eligible": result.eligible, **result.as_dict()}, indent=2, sort_keys=True))
    return 0 if result.eligible else 2


def cmd_discover_swiss_snapshot(args: argparse.Namespace) -> int:
    config = DiscoverSwissConfig(
        project=args.project,
        language=args.language,
        top=args.top,
        timeout_seconds=args.timeout,
        subscription_key_env=args.key_env,
    )
    try:
        key = resolve_subscription_key(config)
        manifest = fetch_hotelleriesuisse_snapshot(config, key)
        write_snapshot_manifest(args.out, manifest)
    except (DiscoverSwissError, ValueError) as exc:
        print(json.dumps({"capture_valid": False, "error": str(exc), "output_written": False}, sort_keys=True), file=sys.stderr)
        return 2
    summary = {
        "snapshot_id": manifest["snapshot_id"],
        "capture_valid": manifest["capture_valid"],
        "reported_count": manifest["reported_count"],
        "records_count": manifest["records_count"],
        "api_pages": manifest["api_pages"],
        "records_sha256": manifest["records_sha256"],
        "scope_state": manifest["scope_state"],
        "member_directory_scope_reconciled": manifest["member_directory_scope_reconciled"],
        "crm_freeze_eligible": manifest["crm_freeze_eligible"],
        "out": str(args.out),
        "capture_violations": manifest["capture_violations"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if manifest["capture_valid"] else 2


def cmd_crm_ingest_stage(db_path: str, snapshot_id: str, records_path: str, observed_at: str) -> int:
    payload = _read_json(records_path)
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
        if isinstance(item, dict)
    ]
    if len(records) != len(payload):
        raise ValueError("records payload must contain only JSON objects")
    with connect(db_path) as conn:
        decisions = classify_batch(conn, snapshot_id, records)
        stage_decisions(conn, decisions, observed_at)
        scheduler = enqueue_ingest_work(conn, decisions)
    print(json.dumps({"snapshot_id": snapshot_id, "authority_advanced": False, "h_id_allocations": 0, "metrics": staging_metrics(decisions), "scheduler": scheduler, "decisions": [d.as_dict() for d in decisions]}, indent=2, sort_keys=True))
    return 0


def cmd_crm_scope_reconcile(api_path: str, directory_path: str, explanations_path: str | None, out_path: str) -> int:
    api_manifest = _read_json(api_path)
    directory_manifest = _read_json(directory_path)
    if not isinstance(api_manifest, dict) or not isinstance(directory_manifest, dict):
        raise ValueError("source manifests must be JSON objects")
    explanations: tuple[ScopeExplanation, ...] = ()
    if explanations_path:
        raw = _read_json(explanations_path)
        if not isinstance(raw, list):
            raise ValueError("explanations payload must be a JSON array")
        explanations = tuple(ScopeExplanation.from_mapping(item) for item in raw if isinstance(item, dict))
        if len(explanations) != len(raw):
            raise ValueError("explanations payload must contain only JSON objects")
    result = reconcile_source_scope(api_manifest, directory_manifest, explanations)
    candidate = build_candidate_snapshot(api_manifest, directory_manifest, result, explanations)
    _write_json(out_path, candidate)
    print(json.dumps({
        "candidate_snapshot_id": candidate["candidate_snapshot_id"],
        "source_scope_reconciliation": candidate["source_scope_reconciliation"],
        "member_directory_scope_reconciled": candidate["member_directory_scope_reconciled"],
        "crm_freeze_eligible": candidate["crm_freeze_eligible"],
        "api_count": result.api_count,
        "directory_count": result.directory_count,
        "matched_count": result.matched_count,
        "api_only": len(result.api_only),
        "directory_only": len(result.directory_only),
        "conflicts": len(result.conflicts),
        "explained_api_only": len(result.explained_api_only),
        "explained_directory_only": len(result.explained_directory_only),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "out": out_path,
    }, indent=2, sort_keys=True))
    return 0 if candidate["crm_freeze_eligible"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swiss-os")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="Validate a public-safe operational manifest")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    validate = manifest_sub.add_parser("validate")
    validate.add_argument("path")

    db = sub.add_parser("db", help="Initialize/check a constrained SQLite database")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    db_init = db_sub.add_parser("init")
    db_init.add_argument("path")
    db_check = db_sub.add_parser("check")
    db_check.add_argument("path")

    meta = sub.add_parser("meta", help="Choose the next safe MEP-2.0 route from a capability snapshot")
    meta_sub = meta.add_subparsers(dest="meta_command", required=True)
    meta_next = meta_sub.add_parser("next")
    meta_next.add_argument("capabilities_json")

    member = sub.add_parser("member-directory", help="Build/validate coherent member-directory manifests for SSR-1.0")
    member_sub = member.add_subparsers(dest="member_command", required=True)
    member_build = member_sub.add_parser("build")
    member_build.add_argument("records_json")
    member_build.add_argument("--snapshot-id", required=True)
    member_build.add_argument("--observed-at", required=True)
    member_build.add_argument("--locale", required=True)
    member_build.add_argument("--source-url", required=True)
    member_build.add_argument("--declared-raw-records", type=int, required=True)
    member_build.add_argument("--expected-pages", type=int, required=True)
    member_build.add_argument("--observed-pages", type=int, required=True)
    member_build.add_argument("--coverage-complete", action="store_true")
    member_build.add_argument("--out", required=True)
    member_validate = member_sub.add_parser("validate")
    member_validate.add_argument("manifest_json")
    member_validate.add_argument("--require-complete", action="store_true")

    crm = sub.add_parser("crm-universe", help="Inspect and evaluate the CUP CRM universe contract")
    crm_sub = crm.add_subparsers(dest="crm_command", required=True)
    crm_validate = crm_sub.add_parser("validate")
    crm_validate.add_argument("path")
    crm_inspect = crm_sub.add_parser("inspect-db")
    crm_inspect.add_argument("db_path")
    crm_inspect.add_argument("snapshot_id")

    snapshot = sub.add_parser("crm-snapshot", help="Validate coherent snapshot candidates")
    snapshot_sub = snapshot.add_subparsers(dest="snapshot_command", required=True)
    freeze_validate = snapshot_sub.add_parser("freeze-validate")
    freeze_validate.add_argument("path")

    discover = sub.add_parser("discover-swiss", help="Acquire structured HotellerieSuisse source data from discover.swiss")
    discover_sub = discover.add_subparsers(dest="discover_command", required=True)
    discover_snapshot = discover_sub.add_parser("snapshot")
    discover_snapshot.add_argument("--out", required=True)
    discover_snapshot.add_argument("--project", default="dsod-hs")
    discover_snapshot.add_argument("--language", default="de")
    discover_snapshot.add_argument("--top", type=int, default=-1)
    discover_snapshot.add_argument("--key-env", default="DISCOVER_SWISS_SUBSCRIPTION_KEY")
    discover_snapshot.add_argument("--timeout", type=float, default=30.0)

    ingest = sub.add_parser("crm-ingest", help="Classify and persist non-authoritative CRM staging")
    ingest_sub = ingest.add_subparsers(dest="ingest_command", required=True)
    ingest_stage = ingest_sub.add_parser("stage")
    ingest_stage.add_argument("db_path")
    ingest_stage.add_argument("snapshot_id")
    ingest_stage.add_argument("records_path")
    ingest_stage.add_argument("--observed-at", required=True)

    scope = sub.add_parser("crm-scope", help="Reconcile discover.swiss capture with member-directory evidence")
    scope_sub = scope.add_subparsers(dest="scope_command", required=True)
    reconcile = scope_sub.add_parser("reconcile")
    reconcile.add_argument("api_manifest")
    reconcile.add_argument("directory_manifest")
    reconcile.add_argument("--explanations")
    reconcile.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "manifest" and args.manifest_command == "validate":
        return cmd_manifest_validate(args.path)
    if args.command == "db" and args.db_command == "init":
        return cmd_db_init(args.path)
    if args.command == "db" and args.db_command == "check":
        return cmd_db_check(args.path)
    if args.command == "meta" and args.meta_command == "next":
        return cmd_meta_next(args.capabilities_json)
    if args.command == "member-directory" and args.member_command == "build":
        return cmd_member_directory_build(args)
    if args.command == "member-directory" and args.member_command == "validate":
        return cmd_member_directory_validate(args.manifest_json, args.require_complete)
    if args.command == "crm-universe" and args.crm_command == "validate":
        return cmd_crm_universe_validate(args.path)
    if args.command == "crm-universe" and args.crm_command == "inspect-db":
        return cmd_crm_universe_inspect_db(args.db_path, args.snapshot_id)
    if args.command == "crm-snapshot" and args.snapshot_command == "freeze-validate":
        return cmd_crm_snapshot_freeze_validate(args.path)
    if args.command == "discover-swiss" and args.discover_command == "snapshot":
        return cmd_discover_swiss_snapshot(args)
    if args.command == "crm-ingest" and args.ingest_command == "stage":
        return cmd_crm_ingest_stage(args.db_path, args.snapshot_id, args.records_path, args.observed_at)
    if args.command == "crm-scope" and args.scope_command == "reconcile":
        return cmd_crm_scope_reconcile(args.api_manifest, args.directory_manifest, args.explanations, args.out)
    return 2


if __name__ == "__main__":
    sys.exit(main())
