#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DETAIL_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS detail_facts (
  discovery_id TEXT PRIMARY KEY REFERENCES discovery_entities(discovery_id) ON DELETE CASCADE,
  detail_fetch_state TEXT NOT NULL,
  http_status TEXT NOT NULL DEFAULT '',
  detail_observed_at TEXT NOT NULL DEFAULT '',
  detail_name TEXT NOT NULL DEFAULT '',
  detail_city TEXT NOT NULL DEFAULT '',
  detail_region TEXT NOT NULL DEFAULT '',
  detail_country TEXT NOT NULL DEFAULT '',
  country_scope_detail TEXT NOT NULL DEFAULT '',
  membership_state_detail TEXT NOT NULL DEFAULT '',
  classification_detail TEXT NOT NULL DEFAULT '',
  classification_basis_detail TEXT NOT NULL DEFAULT '',
  rooms_detail TEXT NOT NULL DEFAULT '',
  rooms_basis_detail TEXT NOT NULL DEFAULT '',
  specialisations_detail TEXT NOT NULL DEFAULT '',
  official_website_candidate_detail TEXT NOT NULL DEFAULT '',
  website_basis_detail TEXT NOT NULL DEFAULT '',
  applied_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_detail_scope ON detail_facts(country_scope_detail);
CREATE INDEX IF NOT EXISTS idx_detail_membership ON detail_facts(membership_state_detail);
CREATE INDEX IF NOT EXISTS idx_detail_classification ON detail_facts(classification_detail);
CREATE INDEX IF NOT EXISTS idx_detail_fetch_state ON detail_facts(detail_fetch_state);

CREATE VIEW IF NOT EXISTS v_detail_resolution AS
SELECT detail_fetch_state, country_scope_detail, membership_state_detail,
       classification_detail, COUNT(*) AS entities
FROM detail_facts
GROUP BY detail_fetch_state, country_scope_detail, membership_state_detail, classification_detail;
'''

FIELDS = [
    'detail_fetch_state','http_status','detail_observed_at','detail_name','detail_city',
    'detail_region','detail_country','country_scope_detail','membership_state_detail',
    'classification_detail','classification_basis_detail','rooms_detail','rooms_basis_detail',
    'specialisations_detail','official_website_candidate_detail','website_basis_detail',
]


def engine_state(resolution: str, parsed: bool, engine: str) -> str | None:
    if engine == 'evidence_engine':
        return 'DETAIL_T1_AVAILABLE' if parsed else 'DETAIL_FETCH_RETRY_OR_SEARCH_PROOF_REQUIRED'
    if engine == 'entity_resolution_engine':
        if resolution == 'MATCHED_EXISTING_CANONICAL': return 'COMPLETE_MATCHED_CANONICAL'
        if resolution == 'NEW_ENTITY_CANDIDATE': return 'READY_CANONICAL_REVIEW' if parsed else 'READY_EXACT_DETAIL_VALIDATION'
        if resolution == 'ALIAS_OR_DUPLICATE_REVIEW': return 'BLOCKED_IDENTITY_REVIEW'
        if resolution == 'QUARANTINED': return 'QUARANTINED'
        return 'READY_CANONICAL_ANTIJOIN'
    if engine == 'intelligence_engine':
        if resolution == 'MATCHED_EXISTING_CANONICAL':
            return 'READY_CANONICAL_ROUTE_DETAIL_ENRICHED' if parsed else 'READY_CANONICAL_ROUTE'
        if resolution == 'NEW_ENTITY_CANDIDATE': return 'WAITING_CANONICAL_PROMOTION_GATE'
        if resolution == 'ALIAS_OR_DUPLICATE_REVIEW': return 'BLOCKED_IDENTITY_REVIEW'
        if resolution == 'QUARANTINED': return 'QUARANTINED'
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--details', required=True)
    args = ap.parse_args()
    db = Path(args.db)
    rows = list(csv.DictReader(Path(args.details).open(encoding='utf-8')))
    now = datetime.now(timezone.utc).isoformat()

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.executescript(DETAIL_SCHEMA)
    expected = con.execute('SELECT COUNT(*) FROM discovery_entities').fetchone()[0]
    ids = {r['discovery_id'] for r in rows}
    known = {r[0] for r in con.execute('SELECT discovery_id FROM discovery_entities')}
    missing = known - ids
    extra = ids - known
    duplicate_count = len(rows) - len(ids)
    errors = []
    if missing: errors.append(f'missing details={len(missing)}')
    if extra: errors.append(f'extra details={len(extra)}')
    if duplicate_count: errors.append(f'duplicate detail rows={duplicate_count}')
    if errors:
        con.close()
        print(json.dumps({'schema':'SWISS_OS_DETAIL_APPLY_V1','errors':errors}, indent=2))
        return 1

    counts = Counter()
    with con:
        for r in rows:
            vals = [r.get(k, '') for k in FIELDS]
            con.execute('''
              INSERT INTO detail_facts(
                discovery_id, detail_fetch_state, http_status, detail_observed_at, detail_name,
                detail_city, detail_region, detail_country, country_scope_detail,
                membership_state_detail, classification_detail, classification_basis_detail,
                rooms_detail, rooms_basis_detail, specialisations_detail,
                official_website_candidate_detail, website_basis_detail, applied_at
              ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(discovery_id) DO UPDATE SET
                detail_fetch_state=excluded.detail_fetch_state,
                http_status=excluded.http_status,
                detail_observed_at=excluded.detail_observed_at,
                detail_name=excluded.detail_name,
                detail_city=excluded.detail_city,
                detail_region=excluded.detail_region,
                detail_country=excluded.detail_country,
                country_scope_detail=excluded.country_scope_detail,
                membership_state_detail=excluded.membership_state_detail,
                classification_detail=excluded.classification_detail,
                classification_basis_detail=excluded.classification_basis_detail,
                rooms_detail=excluded.rooms_detail,
                rooms_basis_detail=excluded.rooms_basis_detail,
                specialisations_detail=excluded.specialisations_detail,
                official_website_candidate_detail=excluded.official_website_candidate_detail,
                website_basis_detail=excluded.website_basis_detail,
                applied_at=excluded.applied_at
            ''', [r['discovery_id'], *vals, now])
            resolution = con.execute('SELECT entity_resolution_state FROM discovery_entities WHERE discovery_id=?', (r['discovery_id'],)).fetchone()[0]
            parsed = r.get('detail_fetch_state') == 'PARSED_T1_DETAIL'
            for engine in ('entity_resolution_engine','evidence_engine','intelligence_engine'):
                state = engine_state(resolution, parsed, engine)
                if state:
                    con.execute('UPDATE engine_tasks SET state=?, updated_at=? WHERE discovery_id=? AND engine=?', (state, now, r['discovery_id'], engine))
            counts[r.get('detail_fetch_state','UNKNOWN')] += 1

    integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
    fk = len(con.execute('PRAGMA foreign_key_check').fetchall())
    detail_count = con.execute('SELECT COUNT(*) FROM detail_facts').fetchone()[0]
    outbound_true = con.execute('SELECT COUNT(*) FROM engine_tasks WHERE outbound_allowed=1').fetchone()[0]
    duplicate_tasks = con.execute('SELECT COUNT(*) - COUNT(DISTINCT discovery_id || "|" || engine) FROM engine_tasks').fetchone()[0]
    con.close()

    if integrity != 'ok': errors.append(f'integrity={integrity}')
    if fk: errors.append(f'fk={fk}')
    if detail_count != expected: errors.append(f'detail_count={detail_count} expected={expected}')
    if outbound_true: errors.append(f'outbound_allowed_true={outbound_true}')
    if duplicate_tasks: errors.append(f'duplicate_engine_tasks={duplicate_tasks}')

    manifest = {
        'schema':'SWISS_OS_DETAIL_APPLY_V1',
        'discovery_entities': expected,
        'detail_facts': detail_count,
        'fetch_state_counts': dict(counts),
        'integrity_check': integrity,
        'foreign_key_violations': fk,
        'outbound_allowed_true': outbound_true,
        'duplicate_engine_tasks': duplicate_tasks,
        'errors': errors,
        'outbound':'CLOSED',
    }
    db.with_suffix('.detail.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
