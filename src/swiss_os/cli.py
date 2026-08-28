from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .crm_universe import CRMUniverseMetrics, inspect_crm_snapshot, validate_crm_universe_gate
from .db import connect, foreign_key_violations, initialize, integrity_check
from .discover_swiss import DiscoverSwissConfig, DiscoverSwissError, fetch_hotelleriesuisse_snapshot, resolve_subscription_key, write_snapshot_manifest
from .ingest_scheduler import enqueue_ingest_work
from .invariants import run_manifest_invariants
from .manifest import OperationalManifest
from .mass_ingest import classify_batch, stage_decisions, staging_metrics
from .snapshot_freeze import SnapshotFreezeCandidate, SnapshotSourceRecord, validate_snapshot_freeze

def cmd_manifest_validate(path: str) -> int:
    manifest = OperationalManifest.load(path)
    results = run_manifest_invariants(manifest)
    payload = {"manifest": manifest.public_summary(), "invariants": [r.__dict__ for r in results], "pass": all(r.passed for r in results)}
    print(json.dumps(payload, indent=2, sort_keys=True)); return 0 if payload["pass"] else 2

def cmd_db_init(path: str) -> int:
    target=Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    with connect(target) as conn: initialize(conn)
    print(json.dumps({"db":str(target),"initialized":True})); return 0

def cmd_db_check(path: str) -> int:
    with connect(path) as conn: integrity=integrity_check(conn); fk=foreign_key_violations(conn)
    payload={"db":path,"integrity_check":integrity,"foreign_key_violations":len(fk),"pass":integrity.lower()=="ok" and not fk}
    print(json.dumps(payload,indent=2,sort_keys=True)); return 0 if payload["pass"] else 2

def cmd_crm_universe_validate(path: str) -> int:
    p=json.loads(Path(path).read_text(encoding="utf-8"))
    m=CRMUniverseMetrics(snapshot_id=str(p.get("snapshot_id","")),snapshot_state=str(p.get("snapshot_state","")),snapshot_raw_records=int(p.get("snapshot_raw_records",0)),active_canonical_mappings=int(p.get("active_canonical_mappings",0)),alias_to_canonical_mappings=int(p.get("alias_to_canonical_mappings",0)),excluded_with_reason_mappings=int(p.get("excluded_with_reason_mappings",0)),reconcile_required=int(p.get("reconcile_required",0)),unmapped_records=int(p.get("unmapped_records",0)),unresolved_duplicate_conflicts=int(p.get("unresolved_duplicate_conflicts",0)),invalid_alias_targets=int(p.get("invalid_alias_targets",0)),constrained_active_canonical=int(p.get("constrained_active_canonical",0)),sheets_active_canonical=int(p.get("sheets_active_canonical",0)),graph_active_canonical=int(p.get("graph_active_canonical",0)),intelligence_active_canonical=int(p.get("intelligence_active_canonical",0)),db_sheets_exact=bool(p.get("db_sheets_exact",False)),graph_exact=bool(p.get("graph_exact",False)),intelligence_exact=bool(p.get("intelligence_exact",False)),coverage_snapshot_ids=tuple(p.get("coverage_snapshot_ids",())))
    r=validate_crm_universe_gate(m); out={"snapshot_id":m.snapshot_id,"snapshot_state":m.snapshot_state,"crm_universe_complete":r.complete,**r.as_dict()}
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if r.complete else 2

def cmd_crm_universe_inspect_db(db_path: str, snapshot_id: str) -> int:
    with connect(db_path) as conn: stats=inspect_crm_snapshot(conn,snapshot_id)
    print(json.dumps(stats.as_dict(),indent=2,sort_keys=True)); return 0

def cmd_crm_snapshot_freeze_validate(path: str) -> int:
    p=json.loads(Path(path).read_text(encoding="utf-8")); c=SnapshotFreezeCandidate(snapshot_id=str(p.get("snapshot_id","")),locale=str(p.get("locale","")),source_url=str(p.get("source_url","")),expected_pages=int(p.get("expected_pages",0)),observed_pages=int(p.get("observed_pages",0)),declared_raw_records=int(p.get("declared_raw_records",0)),materialized_records=int(p.get("materialized_records",0)),duplicate_source_record_keys=int(p.get("duplicate_source_record_keys",0)),unresolved_snapshot_conflicts=int(p.get("unresolved_snapshot_conflicts",0)),missing_record_identity=int(p.get("missing_record_identity",0)))
    r=validate_snapshot_freeze(c); print(json.dumps({"snapshot_id":c.snapshot_id,"freeze_eligible":r.eligible,**r.as_dict()},indent=2,sort_keys=True)); return 0 if r.eligible else 2

def cmd_discover_swiss_snapshot(args: argparse.Namespace) -> int:
    config=DiscoverSwissConfig(project=args.project,language=args.language,top=args.top,timeout_seconds=args.timeout,subscription_key_env=args.key_env)
    try:
        key=resolve_subscription_key(config); manifest=fetch_hotelleriesuisse_snapshot(config,key); write_snapshot_manifest(args.out,manifest)
    except (DiscoverSwissError,ValueError) as exc:
        print(json.dumps({"capture_valid":False,"error":str(exc),"output_written":False},sort_keys=True),file=sys.stderr); return 2
    summary={"snapshot_id":manifest["snapshot_id"],"capture_valid":manifest["capture_valid"],"reported_count":manifest["reported_count"],"records_count":manifest["records_count"],"api_pages":manifest["api_pages"],"records_sha256":manifest["records_sha256"],"scope_state":manifest["scope_state"],"member_directory_scope_reconciled":manifest["member_directory_scope_reconciled"],"crm_freeze_eligible":manifest["crm_freeze_eligible"],"out":str(args.out),"capture_violations":manifest["capture_violations"]}
    print(json.dumps(summary,indent=2,sort_keys=True)); return 0 if manifest["capture_valid"] else 2

def cmd_crm_ingest_stage(db_path: str, snapshot_id: str, records_path: str, observed_at: str) -> int:
    payload=json.loads(Path(records_path).read_text(encoding="utf-8"))
    if not isinstance(payload,list): raise ValueError("records payload must be a JSON array")
    records=[SnapshotSourceRecord(source_url=str(i.get("source_url","")),raw_name=str(i.get("raw_name","")),raw_city=str(i.get("raw_city","")),detail_url=str(i.get("detail_url","")),provider_record_key=str(i.get("provider_record_key",""))) for i in payload]
    with connect(db_path) as conn:
        decisions=classify_batch(conn,snapshot_id,records); stage_decisions(conn,decisions,observed_at); scheduler=enqueue_ingest_work(conn,decisions)
    print(json.dumps({"snapshot_id":snapshot_id,"authority_advanced":False,"h_id_allocations":0,"metrics":staging_metrics(decisions),"scheduler":scheduler,"decisions":[d.as_dict() for d in decisions]},indent=2,sort_keys=True)); return 0

def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="swiss-os"); sub=parser.add_subparsers(dest="command",required=True)
    manifest=sub.add_parser("manifest",help="Validate a public-safe operational manifest"); ms=manifest.add_subparsers(dest="manifest_command",required=True); v=ms.add_parser("validate"); v.add_argument("path")
    db=sub.add_parser("db",help="Initialize/check a constrained SQLite database"); ds=db.add_subparsers(dest="db_command",required=True); i=ds.add_parser("init"); i.add_argument("path"); c=ds.add_parser("check"); c.add_argument("path")
    crm=sub.add_parser("crm-universe",help="Inspect and evaluate the CUP-1.0 CRM universe contract"); cs=crm.add_subparsers(dest="crm_command",required=True); cv=cs.add_parser("validate"); cv.add_argument("path"); ci=cs.add_parser("inspect-db"); ci.add_argument("db_path"); ci.add_argument("snapshot_id")
    snapshot=sub.add_parser("crm-snapshot",help="Validate coherent snapshot freeze candidates"); ss=snapshot.add_subparsers(dest="snapshot_command",required=True); fv=ss.add_parser("freeze-validate"); fv.add_argument("path")
    discover=sub.add_parser("discover-swiss",help="Acquire structured HotellerieSuisse source data from discover.swiss"); dsub=discover.add_subparsers(dest="discover_command",required=True); dsp=dsub.add_parser("snapshot"); dsp.add_argument("--out",required=True); dsp.add_argument("--project",default="dsod-hs"); dsp.add_argument("--language",default="de"); dsp.add_argument("--top",type=int,default=-1); dsp.add_argument("--key-env",default="DISCOVER_SWISS_SUBSCRIPTION_KEY"); dsp.add_argument("--timeout",type=float,default=30.0)
    ingest=sub.add_parser("crm-ingest",help="Classify and persist non-authoritative CRM staging"); ins=ingest.add_subparsers(dest="ingest_command",required=True); stage=ins.add_parser("stage"); stage.add_argument("db_path"); stage.add_argument("snapshot_id"); stage.add_argument("records_path"); stage.add_argument("--observed-at",required=True)
    return parser

def main(argv: list[str] | None=None) -> int:
    a=build_parser().parse_args(argv)
    if a.command=="manifest" and a.manifest_command=="validate": return cmd_manifest_validate(a.path)
    if a.command=="db" and a.db_command=="init": return cmd_db_init(a.path)
    if a.command=="db" and a.db_command=="check": return cmd_db_check(a.path)
    if a.command=="crm-universe" and a.crm_command=="validate": return cmd_crm_universe_validate(a.path)
    if a.command=="crm-universe" and a.crm_command=="inspect-db": return cmd_crm_universe_inspect_db(a.db_path,a.snapshot_id)
    if a.command=="crm-snapshot" and a.snapshot_command=="freeze-validate": return cmd_crm_snapshot_freeze_validate(a.path)
    if a.command=="discover-swiss" and a.discover_command=="snapshot": return cmd_discover_swiss_snapshot(a)
    if a.command=="crm-ingest" and a.ingest_command=="stage": return cmd_crm_ingest_stage(a.db_path,a.snapshot_id,a.records_path,a.observed_at)
    return 2

if __name__=="__main__": sys.exit(main())
