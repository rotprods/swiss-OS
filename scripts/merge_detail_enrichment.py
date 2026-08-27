#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--discovery', required=True)
    ap.add_argument('--shards', required=True, help='Glob for detail shard CSV files')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    discovery = list(csv.DictReader(Path(args.discovery).open(encoding='utf-8')))
    expected = {r['discovery_id'] for r in discovery}
    if len(expected) != len(discovery):
        raise SystemExit('discovery input contains duplicate discovery_id')

    shard_paths = [Path(p) for p in sorted(glob.glob(args.shards))]
    if not shard_paths:
        raise SystemExit('no shard CSVs matched')

    merged: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    fetch_states = Counter()
    for path in shard_paths:
        for row in csv.DictReader(path.open(encoding='utf-8')):
            did = row.get('discovery_id', '')
            if not did:
                raise SystemExit(f'missing discovery_id in {path}')
            if did in merged:
                duplicates.append(did)
                continue
            merged[did] = row
            fetch_states[row.get('detail_fetch_state', 'UNKNOWN')] += 1

    actual = set(merged)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    errors = []
    if duplicates:
        errors.append(f'duplicate detail ids={len(set(duplicates))}')
    if missing:
        errors.append(f'missing detail ids={len(missing)}')
    if extra:
        errors.append(f'extra detail ids={len(extra)}')

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({k for row in merged.values() for k in row.keys()})
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in discovery:
            did = r['discovery_id']
            if did in merged:
                w.writerow(merged[did])

    parsed = fetch_states.get('PARSED_T1_DETAIL', 0)
    manifest = {
        'schema': 'SWISS_OS_DETAIL_MERGE_V1',
        'discovery_entities': len(discovery),
        'shards': [p.name for p in shard_paths],
        'merged_rows': len(merged),
        'parsed_t1_detail': parsed,
        'detail_fetch_state_counts': dict(fetch_states),
        'missing_ids': missing[:100],
        'extra_ids': extra[:100],
        'duplicate_ids': sorted(set(duplicates))[:100],
        'coverage_ratio': len(actual & expected) / len(expected) if expected else 1.0,
        'errors': errors,
        'listing_truth_immutable': True,
        'outbound': 'CLOSED',
    }
    out.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
