#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(*args: str) -> None:
    print('+', ' '.join(args), flush=True)
    subprocess.run(args, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--discovery', required=True)
    ap.add_argument('--canonical-db', required=True)
    ap.add_argument('--source-manifest')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    reconcile = out / 'reconcile'; reconcile.mkdir(exist_ok=True)
    queue = out / 'queue'; queue.mkdir(exist_ok=True)

    run(sys.executable, str(root / 'reconcile_discovery.py'),
        '--discovery', args.discovery,
        '--db', args.canonical_db,
        '--out', str(reconcile))

    ordered = out / 'full_market_ordered.csv'
    run(sys.executable, str(root / 'order_full_market.py'),
        '--input', str(reconcile / 'discovery_reconciled.csv'),
        '--out', str(ordered))

    run(sys.executable, str(root / 'build_full_market_queue.py'),
        '--discovery', str(ordered),
        '--out', str(queue))

    sqlite_path = out / 'swiss_full_market_v1.sqlite'
    db_args = [
        sys.executable, str(root / 'build_full_market_db.py'),
        '--discovery', str(ordered),
        '--queue', str(queue / 'engine_queue.csv'),
        '--nodes', str(queue / 'discovery_graph_nodes.csv'),
        '--edges', str(queue / 'discovery_graph_edges.csv'),
        '--out', str(sqlite_path),
    ]
    if args.source_manifest:
        db_args += ['--manifest', args.source_manifest]
    run(*db_args)

    rec_manifest = json.loads((reconcile / 'reconciliation_manifest.json').read_text())
    queue_manifest = json.loads((queue / 'engine_queue_manifest.json').read_text())
    db_manifest = json.loads(sqlite_path.with_suffix('.manifest.json').read_text())
    summary = {
        'schema': 'SWISS_OS_FULL_MARKET_POSTPROCESS_V1',
        'discovery': rec_manifest,
        'queue': queue_manifest,
        'database': db_manifest,
        'canonical_h_ids_unchanged': True,
        'outbound': 'CLOSED',
    }
    (out / 'postprocess_manifest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
