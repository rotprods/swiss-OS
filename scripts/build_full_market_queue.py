#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ENGINE_SPEC = [
    ("discovery_engine", "", "P0"),
    ("entity_resolution_engine", "discovery_engine", "P0"),
    ("evidence_engine", "entity_resolution_engine", "P0"),
    ("intelligence_engine", "entity_resolution_engine|evidence_engine", "P0"),
    ("vacancy_engine", "intelligence_engine", "P0"),
    ("housing_engine", "intelligence_engine", "P0"),
    ("people_engine", "intelligence_engine", "P0"),
    ("channel_engine", "people_engine|intelligence_engine", "P0"),
    ("group_engine", "entity_resolution_engine|intelligence_engine", "P0"),
    ("social_engine", "intelligence_engine", "P1"),
    ("digital_audit_engine", "intelligence_engine", "P1"),
    ("creative_audit_engine", "intelligence_engine", "P1"),
    ("tech_engine", "intelligence_engine", "P1"),
    ("opportunity_engine", "vacancy_engine|channel_engine|digital_audit_engine|creative_audit_engine|tech_engine", "P1"),
    ("scoring_engine", "opportunity_engine", "P1"),
    ("personalization_engine", "scoring_engine|evidence_engine", "P1"),
    ("message_engine", "personalization_engine|channel_engine", "P1"),
    ("qa_engine", "message_engine|evidence_engine|ttl_engine", "P0"),
    ("graph_engine", "discovery_engine", "P0"),
    ("ttl_engine", "discovery_engine", "P0"),
    ("export_engine", "discovery_engine", "P1"),
    ("governance_engine", "", "P0"),
]


def task_id(entity_id: str, engine: str) -> str:
    return "FMQ-" + hashlib.sha1(f"{entity_id}|{engine}".encode()).hexdigest()[:20]


def routing_state(row: dict[str, str], engine: str) -> str:
    resolution = row.get("entity_resolution_state", "PENDING_CANONICAL_ANTIJOIN")
    if engine == "discovery_engine": return "COMPLETE_DISCOVERED_T1"
    if engine == "governance_engine": return "OUTBOUND_CLOSED"
    if engine == "ttl_engine": return "READY_LISTING_TTL"
    if engine == "export_engine": return "READY_DISCOVERY_EXPORT"
    if engine == "graph_engine": return "READY_DISCOVERY_GRAPH_NODE"
    if engine == "entity_resolution_engine":
        return {
            "MATCHED_EXISTING_CANONICAL": "COMPLETE_MATCHED_CANONICAL",
            "NEW_ENTITY_CANDIDATE": "READY_EXACT_DETAIL_VALIDATION",
            "ALIAS_OR_DUPLICATE_REVIEW": "BLOCKED_IDENTITY_REVIEW",
            "QUARANTINED": "QUARANTINED",
        }.get(resolution, "READY_CANONICAL_ANTIJOIN")
    if resolution == "MATCHED_EXISTING_CANONICAL":
        if engine == "evidence_engine": return "READY_REFRESH_OR_REUSE_CANONICAL_EVIDENCE"
        if engine == "intelligence_engine": return "READY_CANONICAL_ROUTE"
        return "WAITING_INTELLIGENCE_DEPENDENCIES"
    if resolution == "NEW_ENTITY_CANDIDATE":
        return "WAITING_CANONICAL_PROMOTION_GATE"
    if resolution == "ALIAS_OR_DUPLICATE_REVIEW":
        return "BLOCKED_IDENTITY_REVIEW"
    if resolution == "QUARANTINED":
        return "QUARANTINED"
    return "WAITING_ENTITY_RESOLUTION"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--discovery", required=True); ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = list(csv.DictReader(Path(args.discovery).open(encoding="utf-8")))
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    queue_fields = ["task_id","discovery_id","engine","state","depends_on","priority","canonical_safe","outbound_allowed"]
    states = Counter(); by_engine = Counter(); queue_count = 0
    with (out / "engine_queue.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=queue_fields); w.writeheader()
        for row in rows:
            entity = row["discovery_id"]
            for engine, deps, priority in ENGINE_SPEC:
                state = routing_state(row, engine)
                w.writerow({"task_id":task_id(entity,engine),"discovery_id":entity,"engine":engine,"state":state,"depends_on":deps,"priority":priority,"canonical_safe":"TRUE","outbound_allowed":"FALSE"})
                states[state] += 1; by_engine[engine] += 1; queue_count += 1

    with (out / "discovery_graph_nodes.csv").open("w", newline="", encoding="utf-8") as f:
        fields=["node_id","node_type","entity_id","label","state"]; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for row in rows:
            w.writerow({"node_id":"DISCOVERY:"+row["discovery_id"],"node_type":"DISCOVERY_ENTITY","entity_id":row["discovery_id"],"label":row.get("canonical_name_candidate",""),"state":row.get("entity_resolution_state","DISCOVERED_T1_LISTING")})
        for engine,*_ in ENGINE_SPEC:
            w.writerow({"node_id":"ENGINE:"+engine,"node_type":"ENGINE","entity_id":"","label":engine,"state":"ACTIVE_CONTRACT"})

    edge_count=0
    with (out / "discovery_graph_edges.csv").open("w", newline="", encoding="utf-8") as f:
        fields=["edge_id","from_node","to_node","edge_type","state"]; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for row in rows:
            for engine,*_ in ENGINE_SPEC:
                entity=row["discovery_id"]
                w.writerow({"edge_id":"EDGE:"+task_id(entity,engine),"from_node":"DISCOVERY:"+entity,"to_node":"ENGINE:"+engine,"edge_type":"REQUIRES_ENGINE","state":"ACTIVE"}); edge_count+=1

    manifest={"schema":"SWISS_OS_FULL_MARKET_ENGINE_QUEUE_V1_1","discovery_entities":len(rows),"engines_per_entity":len(ENGINE_SPEC),"engine_tasks":queue_count,"graph_entity_nodes":len(rows),"graph_engine_nodes":len(ENGINE_SPEC),"graph_edges":edge_count,"task_state_counts":dict(states),"tasks_per_engine":dict(by_engine),"canonical_graph_untouched":True,"outbound":"CLOSED"}
    (out/"engine_queue_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
