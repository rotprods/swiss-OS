#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ENGINE_SPEC = [
    ("discovery_engine", "COMPLETE", "", "P0"),
    ("entity_resolution_engine", "READY", "discovery_engine", "P0"),
    ("evidence_engine", "WAITING_DEPENDENCY", "entity_resolution_engine", "P0"),
    ("intelligence_engine", "WAITING_DEPENDENCY", "entity_resolution_engine|evidence_engine", "P0"),
    ("vacancy_engine", "WAITING_DEPENDENCY", "intelligence_engine", "P0"),
    ("housing_engine", "WAITING_DEPENDENCY", "intelligence_engine", "P0"),
    ("people_engine", "WAITING_DEPENDENCY", "intelligence_engine", "P0"),
    ("channel_engine", "WAITING_DEPENDENCY", "people_engine|intelligence_engine", "P0"),
    ("group_engine", "WAITING_DEPENDENCY", "entity_resolution_engine|intelligence_engine", "P0"),
    ("social_engine", "WAITING_DEPENDENCY", "intelligence_engine", "P1"),
    ("digital_audit_engine", "WAITING_DEPENDENCY", "intelligence_engine", "P1"),
    ("creative_audit_engine", "WAITING_DEPENDENCY", "intelligence_engine", "P1"),
    ("tech_engine", "WAITING_DEPENDENCY", "intelligence_engine", "P1"),
    ("opportunity_engine", "WAITING_DEPENDENCY", "vacancy_engine|channel_engine|digital_audit_engine|creative_audit_engine|tech_engine", "P1"),
    ("scoring_engine", "WAITING_DEPENDENCY", "opportunity_engine", "P1"),
    ("personalization_engine", "WAITING_DEPENDENCY", "scoring_engine|evidence_engine", "P1"),
    ("message_engine", "WAITING_DEPENDENCY", "personalization_engine|channel_engine", "P1"),
    ("qa_engine", "WAITING_DEPENDENCY", "message_engine|evidence_engine|ttl_engine", "P0"),
    ("graph_engine", "READY_DISCOVERY_GRAPH_NODE", "discovery_engine", "P0"),
    ("ttl_engine", "READY_LISTING_TTL", "discovery_engine", "P0"),
    ("export_engine", "READY_DISCOVERY_EXPORT", "discovery_engine", "P1"),
    ("governance_engine", "OUTBOUND_CLOSED", "", "P0"),
]


def task_id(entity_id: str, engine: str) -> str:
    raw = f"{entity_id}|{engine}".encode()
    return "FMQ-" + hashlib.sha1(raw).hexdigest()[:20]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discovery", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = list(csv.DictReader(Path(args.discovery).open(encoding="utf-8")))
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    queue_fields = ["task_id", "discovery_id", "engine", "state", "depends_on", "priority", "canonical_safe", "outbound_allowed"]
    queue_count = 0
    states = Counter()
    with (out / "engine_queue.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=queue_fields); w.writeheader()
        for row in rows:
            entity = row["discovery_id"]
            for engine, state, deps, priority in ENGINE_SPEC:
                w.writerow({
                    "task_id": task_id(entity, engine),
                    "discovery_id": entity,
                    "engine": engine,
                    "state": state,
                    "depends_on": deps,
                    "priority": priority,
                    "canonical_safe": "TRUE",
                    "outbound_allowed": "FALSE",
                })
                queue_count += 1; states[state] += 1

    with (out / "discovery_graph_nodes.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["node_id", "node_type", "entity_id", "label", "state"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for row in rows:
            w.writerow({"node_id": "DISCOVERY:" + row["discovery_id"], "node_type": "DISCOVERY_ENTITY", "entity_id": row["discovery_id"], "label": row.get("canonical_name_candidate", ""), "state": "DISCOVERED_T1_LISTING"})
        for engine, *_ in ENGINE_SPEC:
            w.writerow({"node_id": "ENGINE:" + engine, "node_type": "ENGINE", "entity_id": "", "label": engine, "state": "ACTIVE_CONTRACT"})

    edge_count = 0
    with (out / "discovery_graph_edges.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["edge_id", "from_node", "to_node", "edge_type", "state"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for row in rows:
            for engine, *_ in ENGINE_SPEC:
                entity = row["discovery_id"]
                w.writerow({
                    "edge_id": "EDGE:" + task_id(entity, engine),
                    "from_node": "DISCOVERY:" + entity,
                    "to_node": "ENGINE:" + engine,
                    "edge_type": "REQUIRES_ENGINE",
                    "state": "ACTIVE",
                })
                edge_count += 1

    manifest = {
        "schema": "SWISS_OS_FULL_MARKET_ENGINE_QUEUE_V1",
        "discovery_entities": len(rows),
        "engines_per_entity": len(ENGINE_SPEC),
        "engine_tasks": queue_count,
        "graph_entity_nodes": len(rows),
        "graph_engine_nodes": len(ENGINE_SPEC),
        "graph_edges": edge_count,
        "task_state_counts": dict(states),
        "canonical_graph_untouched": True,
        "outbound": "CLOSED",
    }
    (out / "engine_queue_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
