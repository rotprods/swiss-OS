from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DetailEnrichmentGauntletTests(unittest.TestCase):
    def test_merge_shards_and_apply_to_full_market_db(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            discovery = td / 'discovery.csv'
            discovery_fields = ['discovery_id','canonical_name_candidate','city_candidate']
            with discovery.open('w', newline='', encoding='utf-8') as f:
                w=csv.DictWriter(f, fieldnames=discovery_fields); w.writeheader()
                w.writerows([
                    {'discovery_id':'U-0000000000000001','canonical_name_candidate':'Existing','city_candidate':'Zürich'},
                    {'discovery_id':'U-0000000000000002','canonical_name_candidate':'New','city_candidate':'Basel'},
                ])

            shard_fields = [
                'discovery_id','detail_fetch_state','http_status','detail_observed_at','detail_name','detail_city',
                'detail_region','detail_country','country_scope_detail','membership_state_detail','classification_detail',
                'classification_basis_detail','rooms_detail','rooms_basis_detail','specialisations_detail',
                'official_website_candidate_detail','website_basis_detail'
            ]
            shard_rows = [
                {'discovery_id':'U-0000000000000001','detail_fetch_state':'PARSED_T1_DETAIL','http_status':'200','detail_observed_at':'now','detail_name':'Existing','detail_city':'Zürich','detail_region':'Zürich','detail_country':'Switzerland','country_scope_detail':'SWITZERLAND_VERIFIED','membership_state_detail':'MEMBER_CURRENT_VERIFIED','classification_detail':'4 STAR','classification_basis_detail':'DETAIL_TEXT_REGEX','rooms_detail':'50','rooms_basis_detail':'DETAIL_TEXT_REGEX','specialisations_detail':'Business','official_website_candidate_detail':'https://existing.example','website_basis_detail':'EXTERNAL_WEBSITE_LABEL'},
                {'discovery_id':'U-0000000000000002','detail_fetch_state':'HTTP_404','http_status':'404','detail_observed_at':'now','detail_name':'','detail_city':'','detail_region':'','detail_country':'','country_scope_detail':'','membership_state_detail':'UNKNOWN_NOT_FETCHED','classification_detail':'','classification_basis_detail':'','rooms_detail':'','rooms_basis_detail':'','specialisations_detail':'','official_website_candidate_detail':'','website_basis_detail':''},
            ]
            shards = td/'shards'; shards.mkdir()
            for i,row in enumerate(shard_rows):
                p=shards/f'detail_enrichment_shard_{i:02d}.csv'
                with p.open('w', newline='', encoding='utf-8') as f:
                    w=csv.DictWriter(f, fieldnames=shard_fields); w.writeheader(); w.writerow(row)

            merged = td/'merged.csv'
            subprocess.run([
                sys.executable, str(ROOT/'scripts/merge_detail_enrichment.py'),
                '--discovery', str(discovery), '--shards', str(shards/'detail_enrichment_shard_*.csv'),
                '--out', str(merged),
            ], check=True, capture_output=True, text=True)
            mm=json.loads(merged.with_suffix('.manifest.json').read_text())
            self.assertEqual(mm['merged_rows'],2)
            self.assertEqual(mm['coverage_ratio'],1.0)
            self.assertEqual(mm['errors'],[])

            db=td/'full_market.sqlite'
            con=sqlite3.connect(db)
            con.executescript('''
            PRAGMA foreign_keys=ON;
            CREATE TABLE discovery_entities(
              discovery_id TEXT PRIMARY KEY,
              entity_resolution_state TEXT NOT NULL
            );
            CREATE TABLE engine_tasks(
              task_id TEXT PRIMARY KEY,
              discovery_id TEXT NOT NULL REFERENCES discovery_entities(discovery_id),
              engine TEXT NOT NULL,
              state TEXT NOT NULL,
              updated_at TEXT NOT NULL DEFAULT '',
              outbound_allowed INTEGER NOT NULL DEFAULT 0,
              UNIQUE(discovery_id,engine)
            );
            ''')
            con.executemany('INSERT INTO discovery_entities VALUES (?,?)',[
                ('U-0000000000000001','MATCHED_EXISTING_CANONICAL'),
                ('U-0000000000000002','NEW_ENTITY_CANDIDATE'),
            ])
            for did in ('U-0000000000000001','U-0000000000000002'):
                for engine in ('entity_resolution_engine','evidence_engine','intelligence_engine'):
                    con.execute('INSERT INTO engine_tasks(task_id,discovery_id,engine,state) VALUES (?,?,?,?)',(did+'|'+engine,did,engine,'OLD'))
            con.commit(); con.close()

            subprocess.run([
                sys.executable, str(ROOT/'scripts/apply_detail_enrichment.py'),
                '--db',str(db),'--details',str(merged)
            ],check=True,capture_output=True,text=True)
            dm=json.loads(db.with_suffix('.detail.manifest.json').read_text())
            self.assertEqual(dm['detail_facts'],2)
            self.assertEqual(dm['integrity_check'],'ok')
            self.assertEqual(dm['foreign_key_violations'],0)
            self.assertEqual(dm['outbound_allowed_true'],0)
            self.assertEqual(dm['errors'],[])

            con=sqlite3.connect(db)
            self.assertEqual(con.execute("SELECT state FROM engine_tasks WHERE discovery_id='U-0000000000000001' AND engine='evidence_engine'").fetchone()[0],'DETAIL_T1_AVAILABLE')
            self.assertEqual(con.execute("SELECT state FROM engine_tasks WHERE discovery_id='U-0000000000000001' AND engine='intelligence_engine'").fetchone()[0],'READY_CANONICAL_ROUTE_DETAIL_ENRICHED')
            self.assertEqual(con.execute("SELECT state FROM engine_tasks WHERE discovery_id='U-0000000000000002' AND engine='evidence_engine'").fetchone()[0],'DETAIL_FETCH_RETRY_OR_SEARCH_PROOF_REQUIRED')
            self.assertEqual(con.execute("SELECT state FROM engine_tasks WHERE discovery_id='U-0000000000000002' AND engine='entity_resolution_engine'").fetchone()[0],'READY_EXACT_DETAIL_VALIDATION')
            self.assertEqual(con.execute('SELECT COUNT(*) FROM engine_tasks WHERE outbound_allowed=1').fetchone()[0],0)
            con.close()


if __name__ == '__main__':
    unittest.main()
