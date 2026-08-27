#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = r'''
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS discovery_entities (
  discovery_id TEXT PRIMARY KEY,
  canonical_name_candidate TEXT NOT NULL,
  city_candidate TEXT NOT NULL DEFAULT '',
  detail_url TEXT NOT NULL UNIQUE,
  directory_page INTEGER NOT NULL CHECK(directory_page > 0),
  source_tier TEXT NOT NULL,
  membership_state TEXT NOT NULL,
  entity_resolution_state TEXT NOT NULL,
  country_scope TEXT NOT NULL,
  accommodation_type_hint TEXT NOT NULL,
  classification_basis TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  canonical_match_id TEXT NOT NULL DEFAULT '',
  resolution_reason TEXT NOT NULL DEFAULT '',
  resolution_confidence REAL,
  CHECK(discovery_id GLOB 'U-[0-9a-f]*'),
  CHECK(source_tier='T1_OFFICIAL_DIRECTORY_LISTING')
);

CREATE INDEX IF NOT EXISTS idx_discovery_name_city
ON discovery_entities(canonical_name_candidate, city_candidate);
CREATE INDEX IF NOT EXISTS idx_discovery_resolution
ON discovery_entities(entity_resolution_state);
CREATE INDEX IF NOT EXISTS idx_discovery_scope
ON discovery_entities(country_scope);
CREATE INDEX IF NOT EXISTS idx_discovery_type
ON discovery_entities(accommodation_type_hint);

CREATE TABLE IF NOT EXISTS engine_tasks (
  task_id TEXT PRIMARY KEY,
  discovery_id TEXT NOT NULL REFERENCES discovery_entities(discovery_id) ON DELETE CASCADE,
  engine TEXT NOT NULL,
  state TEXT NOT NULL,
  depends_on TEXT NOT NULL DEFAULT '',
  priority TEXT NOT NULL,
  canonical_safe INTEGER NOT NULL CHECK(canonical_safe IN (0,1)),
  outbound_allowed INTEGER NOT NULL CHECK(outbound_allowed IN (0,1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(discovery_id, engine)
);
CREATE INDEX IF NOT EXISTS idx_engine_tasks_engine_state
ON engine_tasks(engine, state, priority);

CREATE TABLE IF NOT EXISTS discovery_graph_nodes (
  node_id TEXT PRIMARY KEY,
  node_type TEXT NOT NULL,
  entity_id TEXT NOT NULL DEFAULT '',
  label TEXT NOT NULL,
  state TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS discovery_graph_edges (
  edge_id TEXT PRIMARY KEY,
  from_node TEXT NOT NULL REFERENCES discovery_graph_nodes(node_id),
  to_node TEXT NOT NULL REFERENCES discovery_graph_nodes(node_id),
  edge_type TEXT NOT NULL,
  state TEXT NOT NULL,
  UNIQUE(from_node, to_node, edge_type)
);
CREATE INDEX IF NOT EXISTS idx_discovery_edges_from ON discovery_graph_edges(from_node);
CREATE INDEX IF NOT EXISTS idx_discovery_edges_to ON discovery_graph_edges(to_node);

CREATE VIEW IF NOT EXISTS v_market_resolution AS
SELECT entity_resolution_state, country_scope, accommodation_type_hint, COUNT(*) AS entities
FROM discovery_entities
GROUP BY entity_resolution_state, country_scope, accommodation_type_hint;

CREATE VIEW IF NOT EXISTS v_engine_backlog AS
SELECT engine, state, priority, COUNT(*) AS tasks
FROM engine_tasks
GROUP BY engine, state, priority;
'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def truthy(v: str) -> int:
    return 1 if str(v).strip().casefold() in {'1','true','yes','y'} else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--discovery', required=True)
    ap.add_argument('--queue', required=True)
    ap.add_argument('--nodes', required=True)
    ap.add_argument('--edges', required=True)
    ap.add_argument('--manifest', required=False)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        out.unlink()
    generated_at = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(str(out))
    con.executescript(SCHEMA)

    discovery = list(csv.DictReader(Path(args.discovery).open(encoding='utf-8')))
    with con:
        for r in discovery:
            con.execute('''
              INSERT INTO discovery_entities(
                discovery_id, canonical_name_candidate, city_candidate, detail_url,
                directory_page, source_tier, membership_state, entity_resolution_state,
                country_scope, accommodation_type_hint, classification_basis, observed_at,
                canonical_match_id, resolution_reason, resolution_confidence
              ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                r['discovery_id'], r['canonical_name_candidate'], r.get('city_candidate',''), r['detail_url'],
                int(r['directory_page']), r['source_tier'], r['membership_state'], r['entity_resolution_state'],
                r['country_scope'], r['accommodation_type_hint'], r['classification_basis'], r['observed_at'],
                r.get('canonical_match_id',''), r.get('resolution_reason',''),
                float(r['resolution_confidence']) if r.get('resolution_confidence') not in ('', None) else None,
            ))

    now = generated_at
    with con:
        for r in csv.DictReader(Path(args.queue).open(encoding='utf-8')):
            con.execute('''
              INSERT INTO engine_tasks(task_id, discovery_id, engine, state, depends_on, priority,
                                       canonical_safe, outbound_allowed, created_at, updated_at)
              VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (
                r['task_id'], r['discovery_id'], r['engine'], r['state'], r.get('depends_on',''), r['priority'],
                truthy(r['canonical_safe']), truthy(r['outbound_allowed']), now, now,
            ))

    with con:
        for r in csv.DictReader(Path(args.nodes).open(encoding='utf-8')):
            con.execute('INSERT INTO discovery_graph_nodes(node_id,node_type,entity_id,label,state) VALUES (?,?,?,?,?)',
                        (r['node_id'], r['node_type'], r.get('entity_id',''), r['label'], r['state']))
        for r in csv.DictReader(Path(args.edges).open(encoding='utf-8')):
            con.execute('INSERT INTO discovery_graph_edges(edge_id,from_node,to_node,edge_type,state) VALUES (?,?,?,?,?)',
                        (r['edge_id'], r['from_node'], r['to_node'], r['edge_type'], r['state']))

    source_manifest = {}
    if args.manifest and Path(args.manifest).exists():
        source_manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    meta = {
        'schema': 'SWISS_OS_FULL_MARKET_DB_V1',
        'generated_at': generated_at,
        'discovery_entities': str(len(discovery)),
        'source_observed_result_count': str(source_manifest.get('observed_result_count','')),
        'outbound': 'CLOSED',
    }
    with con:
        con.executemany('INSERT INTO meta(key,value) VALUES (?,?)', meta.items())

    integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
    fk = len(con.execute('PRAGMA foreign_key_check').fetchall())
    entity_count = con.execute('SELECT COUNT(*) FROM discovery_entities').fetchone()[0]
    task_count = con.execute('SELECT COUNT(*) FROM engine_tasks').fetchone()[0]
    task_unique = con.execute("SELECT COUNT(*) FROM (SELECT discovery_id,engine FROM engine_tasks GROUP BY discovery_id,engine)").fetchone()[0]
    node_count = con.execute('SELECT COUNT(*) FROM discovery_graph_nodes').fetchone()[0]
    edge_count = con.execute('SELECT COUNT(*) FROM discovery_graph_edges').fetchone()[0]
    outbound_true = con.execute('SELECT COUNT(*) FROM engine_tasks WHERE outbound_allowed=1').fetchone()[0]
    expected_tasks = entity_count * 22
    errors = []
    if integrity != 'ok': errors.append(f'integrity={integrity}')
    if fk != 0: errors.append(f'foreign_key_violations={fk}')
    if task_count != task_unique: errors.append('duplicate entity-engine tasks')
    if task_count != expected_tasks: errors.append(f'task_count={task_count} expected={expected_tasks}')
    if outbound_true != 0: errors.append(f'outbound_allowed_true={outbound_true}')
    con.close()

    digest = sha256(out)
    manifest = {
        'schema': 'SWISS_OS_FULL_MARKET_DB_MANIFEST_V1',
        'generated_at': generated_at,
        'sqlite': out.name,
        'sha256': digest,
        'integrity_check': integrity,
        'foreign_key_violations': fk,
        'discovery_entities': entity_count,
        'engine_tasks': task_count,
        'expected_engine_tasks': expected_tasks,
        'graph_nodes': node_count,
        'graph_edges': edge_count,
        'outbound_allowed_true': outbound_true,
        'outbound': 'CLOSED',
        'errors': errors,
    }
    manifest_path = out.with_suffix('.manifest.json')
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
