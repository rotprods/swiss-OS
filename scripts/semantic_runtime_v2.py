#!/usr/bin/env python3
"""Deterministic, project-scoped semantic artifact compiler and shard producer.

Artifacts are derived retrieval state, never authority. No provider writes,
credential access, source mutation, or implicit truncation are performed.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict, replace
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.request import Request, urlopen
import uuid
from swiss_os.repo_semantics import chunk_repository, graphify_chunks, write_graph_jsonl
from swiss_os.cos_graph import cos20_for_chunk

REPO = 'rotprods/swiss-OS'
MODEL = 'qwen3-embedding:0.6b'
MODEL_DIGEST = 'ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d'
SCHEMA = 'SWISS-SEMANTIC-ARTIFACT-2.0'
MAX_CHARS = 2400
NAMESPACE = uuid.UUID('3a3ace3e-6288-4e16-a684-77daa848cde0')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + '\n')
    temp.replace(path)


def api(path: str, data: dict | None = None) -> dict:
    base = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    req = Request(base + path, data=None if data is None else json.dumps(data, allow_nan=False).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=240) as response:
        return json.load(response)


def sensitive(path: str) -> bool:
    p = Path(path)
    name = p.name.lower()
    return (any(x in {'secrets', 'credentials', '.ssh', '.aws', 'candidate_private', 'contacts_private', 'raw_evidence', 'private_exports'} for x in p.parts)
            or (name.startswith('.env') and name != '.env.example')
            or name in {'id_rsa', 'id_ed25519', 'credentials.json', 'secrets.json', '.netrc'}
            or p.suffix.lower() in {'.key', '.pem', '.p12'})


def valid_vector(vector: list, dimension: int) -> None:
    if not isinstance(vector, list) or len(vector) != dimension:
        raise ValueError('VECTOR_DIMENSION_MISMATCH')
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in vector):
        raise ValueError('NONFINITE_OR_NONNUMERIC_VECTOR')
    norm = math.sqrt(sum(x*x for x in vector))
    if not 0.99 <= norm <= 1.01:
        raise ValueError('VECTOR_NOT_NORMALIZED')


def read_rows(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def scan(root: Path, out: Path) -> None:
    started = time.perf_counter()
    root = root.resolve()
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip()
    if dirty:
        raise ValueError('SOURCE_CHECKOUT_MUST_BE_CLEAN')
    out.mkdir(parents=True, exist_ok=True)
    chunks, stats = chunk_repository(root, max_chars=MAX_CHARS, overlap_lines=2)
    safe_chunks, records, occurrences = [], [], Counter()
    for chunk in chunks:
        if sensitive(chunk.path) or (root / chunk.path).is_symlink():
            continue
        fragments = [chunk.text[i:i+MAX_CHARS] for i in range(0, len(chunk.text), MAX_CHARS)]
        for index, text in enumerate(fragments):
            if not text.strip():
                continue
            key = '\0'.join([REPO, chunk.path, chunk.kind, chunk.symbol or '', sha(text.encode())])
            duplicate = occurrences[key]
            occurrences[key] += 1
            cid = 'CHUNK-' + sha((key + '\0' + str(duplicate)).encode())[:32]
            current = replace(chunk, text=text, chunk_id=cid, content_sha256=sha(text.encode()))
            embedding_input = current.embedding_text()
            if len(embedding_input) > 3500:
                raise ValueError('UNBOUNDED_EMBEDDING_METADATA')
            cos = list(cos20_for_chunk(current).vector)
            valid_vector(cos, 20)
            assert cos[17:] == [0.0, 0.0, 0.0]
            payload = current.payload(repo=REPO, git_sha=commit, cos20=cos)
            payload.update(project='swiss-os', authority='NON_AUTHORITATIVE', embedding_model=MODEL,
                           embedding_model_digest=MODEL_DIGEST, embedding_schema=SCHEMA,
                           input_sha256=sha(embedding_input.encode()), fragment_index=index,
                           fragment_count=len(fragments), parent_chunk_id=chunk.chunk_id,
                           fragment_char_start=index*MAX_CHARS, fragment_char_end=index*MAX_CHARS+len(text))
            records.append({'id': str(uuid.uuid5(NAMESPACE, REPO + '\0' + cid)), 'embedding_input': embedding_input, 'payload': payload})
            safe_chunks.append(current)
    records.sort(key=lambda r: r['id'])
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('DUPLICATE_CHUNK_ID')
    with (out / 'chunks.jsonl').open('w') as stream:
        for row in records:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')
    nodes, edges = graphify_chunks(safe_chunks)
    write_graph_jsonl(out / 'graph.jsonl', nodes, edges)
    tracked = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')
    indexed = {r['payload']['path'] for r in records}
    inventory = [{'path': p, 'status': 'INDEXED' if p in indexed else 'EXCLUDED_OR_EMPTY',
                  'file_sha256': sha((root/p).read_bytes()) if (root/p).is_file() and not (root/p).is_symlink() else None}
                 for p in sorted(filter(None, tracked))]
    dump(out / 'inventory.json', inventory)
    manifest = {'schema': SCHEMA, 'repo': REPO, 'project': 'swiss-os', 'source_commit': commit,
                'source_tree': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD^{tree}'], text=True).strip(),
                'producer_commit': os.environ.get('GITHUB_SHA'), 'model': MODEL, 'model_digest': MODEL_DIGEST,
                'semantic_dimension': 1024, 'cos_dimension': 20, 'chunk_count': len(records),
                'indexed_files': len(indexed), 'tracked_files': len(inventory), 'base_scan_stats': asdict(stats),
                'graph_nodes': len(nodes), 'graph_edges': len(edges), 'max_chars': MAX_CHARS, 'overlap_lines': 2,
                'chunks_sha256': sha((out/'chunks.jsonl').read_bytes()), 'graph_sha256': sha((out/'graph.jsonl').read_bytes()),
                'scan_seconds': time.perf_counter()-started, 'authority': 'NON_AUTHORITATIVE'}
    dump(out / 'manifest.json', manifest)
    print(json.dumps(manifest), flush=True)


def embed(chunks_path: Path, out: Path, shard: int, shards: int) -> None:
    if not 0 <= shard < shards:
        raise ValueError('INVALID_SHARD')
    models = api('/api/tags').get('models', [])
    if not any(m.get('name') == MODEL and m.get('digest') == MODEL_DIGEST for m in models):
        raise ValueError('MODEL_DIGEST_MISMATCH')
    version = api('/api/version').get('version')
    if version != '0.33.2':
        raise ValueError(f'OLLAMA_VERSION_MISMATCH:{version}')
    all_rows = read_rows(chunks_path)
    rows = [r for r in all_rows if int(uuid.UUID(r['id'])) % shards == shard]
    out.mkdir(parents=True, exist_ok=True)
    target = out / f'vectors-{shard}.jsonl.gz'
    started = time.perf_counter()
    input_digest = sha(chunks_path.read_bytes())
    tokens = 0
    with gzip.open(target, 'wt', encoding='utf-8') as stream:
        for offset in range(0, len(rows), 8):
            batch = rows[offset:offset+8]
            response = api('/api/embed', {'model': MODEL, 'input': [r['embedding_input'] for r in batch],
                           'truncate': False, 'keep_alive': '30m',
                           'options': {'num_thread': 4, 'num_ctx': 4096, 'num_batch': 512}})
            vectors = response.get('embeddings', [])
            if len(vectors) != len(batch):
                raise ValueError('EMBEDDING_CARDINALITY_MISMATCH')
            tokens += response.get('prompt_eval_count', 0)
            for row, vector in zip(batch, vectors):
                valid_vector(vector, 1024)
                item = {'id': row['id'], 'vector': {'semantic': vector, 'cos20': row['payload']['cos20']},
                        'payload': row['payload'], 'input_sha256': row['payload']['input_sha256'],
                        'chunks_sha256': input_digest, 'model_digest': MODEL_DIGEST, 'producer_shard': shard}
                stream.write(json.dumps(item, sort_keys=True, allow_nan=False) + '\n')
            if offset % 64 == 0:
                print(json.dumps({'shard': shard, 'done': min(offset+8, len(rows)), 'total': len(rows), 'seconds': time.perf_counter()-started}), flush=True)
    dump(out / f'receipt-{shard}.json', {'schema': SCHEMA, 'repo': REPO, 'shard': shard, 'shards': shards,
         'count': len(rows), 'chunks_sha256': input_digest, 'model_digest': MODEL_DIGEST, 'ollama_version': version,
         'file_sha256': sha(target.read_bytes()), 'seconds': time.perf_counter()-started, 'prompt_eval_count': tokens,
         'run_id': os.environ.get('GITHUB_RUN_ID'), 'status': 'COMPLETE', 'authority': 'NON_AUTHORITATIVE'})


def merge(package: Path, parts: Path, out: Path, shards: int) -> None:
    expected = {r['id']: r for r in read_rows(package/'chunks.jsonl')}
    manifest = json.loads((package/'manifest.json').read_text())
    digest = sha((package/'chunks.jsonl').read_bytes())
    if digest != manifest['chunks_sha256']:
        raise ValueError('MANIFEST_HASH_MISMATCH')
    result, receipts = {}, []
    for shard in range(shards):
        receipt_paths = list(parts.rglob(f'receipt-{shard}.json'))
        vector_paths = list(parts.rglob(f'vectors-{shard}.jsonl.gz'))
        if len(receipt_paths) != 1 or len(vector_paths) != 1:
            raise ValueError('MISSING_OR_DUPLICATE_SHARD')
        receipt = json.loads(receipt_paths[0].read_text())
        if receipt['status'] != 'COMPLETE' or receipt['chunks_sha256'] != digest or receipt['model_digest'] != MODEL_DIGEST:
            raise ValueError('SHARD_CONTRACT_MISMATCH')
        if sha(vector_paths[0].read_bytes()) != receipt['file_sha256']:
            raise ValueError('SHARD_FILE_HASH_MISMATCH')
        rows = read_rows(vector_paths[0])
        if len(rows) != receipt['count']:
            raise ValueError('SHARD_COUNT_MISMATCH')
        for row in rows:
            ident = row['id']
            if ident in result or ident not in expected or int(uuid.UUID(ident)) % shards != shard:
                raise ValueError('DUPLICATE_UNKNOWN_OR_MISROUTED_POINT')
            original = expected[ident]
            if row['payload'] != original['payload'] or row['chunks_sha256'] != digest or row['model_digest'] != MODEL_DIGEST:
                raise ValueError('POINT_PROVENANCE_MISMATCH')
            if row['input_sha256'] != sha(original['embedding_input'].encode()):
                raise ValueError('EMBEDDING_INPUT_HASH_MISMATCH')
            valid_vector(row['vector']['semantic'], 1024)
            valid_vector(row['vector']['cos20'], 20)
            if row['vector']['cos20'] != original['payload']['cos20'] or any(row['vector']['cos20'][17:]):
                raise ValueError('COS_VECTOR_MISMATCH')
            result[ident] = row
        receipts.append(receipt)
    if set(result) != set(expected):
        raise ValueError('INCOMPLETE_CORPUS')
    out.mkdir(parents=True, exist_ok=True)
    with gzip.open(out/'vectors.jsonl.gz', 'wt', encoding='utf-8') as stream:
        for ident in sorted(result):
            stream.write(json.dumps(result[ident], sort_keys=True, allow_nan=False) + '\n')
    dump(out/'merge-receipt.json', {'status': 'COMPLETE', 'authority': 'NON_AUTHORITATIVE',
         'source_commit': manifest['source_commit'], 'count': len(result), 'expected': len(expected),
         'chunks_sha256': digest, 'model_digest': MODEL_DIGEST, 'shards': receipts,
         'vectors_sha256': sha((out/'vectors.jsonl.gz').read_bytes())})
    print(f'COMPLETE: {len(result)} / {len(expected)} vectors', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('scan'); p.add_argument('--repo', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('embed'); p.add_argument('--chunks', type=Path, required=True); p.add_argument('--out', type=Path, required=True); p.add_argument('--shard', type=int, required=True); p.add_argument('--shards', type=int, default=8)
    p = sub.add_parser('merge'); p.add_argument('--package', type=Path, required=True); p.add_argument('--parts', type=Path, required=True); p.add_argument('--out', type=Path, required=True); p.add_argument('--shards', type=int, default=8)
    args = parser.parse_args()
    if args.command == 'scan': scan(args.repo, args.out)
    elif args.command == 'embed': embed(args.chunks, args.out, args.shard, args.shards)
    elif args.command == 'merge': merge(args.package, args.parts, args.out, args.shards)


if __name__ == '__main__':
    main()
