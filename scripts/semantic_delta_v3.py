#!/usr/bin/env python3
"""Incremental vector compiler for SWISS-OS semantic runtime.

Reuses a prior validated vector iff point id, embedding input hash, and pinned
model digest match. Payload/COS20 are always refreshed from the current scan.
The merged output must exactly cover the current corpus.
"""
from __future__ import annotations
import argparse, gzip, hashlib, io, json, math, uuid
from collections import Counter
from pathlib import Path

MODEL_DIGEST="ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d"


def sha(b: bytes)->str: return hashlib.sha256(b).hexdigest()

def rows(path: Path):
    op=gzip.open if path.suffix=='.gz' else open
    with op(path,'rt',encoding='utf-8') as f:
        for line in f:
            if line.strip(): yield json.loads(line)

def write(path: Path, iterable):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.suffix=='.gz':
        with path.open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz, io.TextIOWrapper(gz,encoding='utf-8') as f:
            for x in iterable: f.write(json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n')
    else:
        with path.open('w',encoding='utf-8') as f:
            for x in iterable: f.write(json.dumps(x,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n')

def dump(path:Path,x):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n')

def check(v,n):
    if not isinstance(v,list) or len(v)!=n or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in v):
        raise ValueError(f'INVALID_VECTOR_{n}')

def current_map(path:Path):
    out={}
    for r in rows(path):
        i=r.get('id')
        if not i or i in out: raise ValueError('CURRENT_DUPLICATE_OR_EMPTY_ID')
        if r.get('payload',{}).get('input_sha256')!=sha(str(r.get('embedding_input','')).encode()): raise ValueError('CURRENT_INPUT_HASH_MISMATCH')
        out[i]=r
    return out

def plan(chunks:Path,baseline:Path,out:Path):
    cur=current_map(chunks); cd=sha(chunks.read_bytes()); seen=set(); reused=set(); removed=[]; sources=Counter(); baseline_n=0
    reuse_path=out/'reuse-vectors.jsonl.gz'; todo_path=out/'todo.jsonl'; out.mkdir(parents=True,exist_ok=True)
    def gen():
        nonlocal baseline_n
        for old in rows(baseline):
            baseline_n+=1; i=old.get('id')
            if not i or i in seen: raise ValueError('BASELINE_DUPLICATE_OR_EMPTY_ID')
            seen.add(i); now=cur.get(i)
            if now is None: removed.append(i); continue
            if old.get('model_digest')!=MODEL_DIGEST: continue
            sem=old.get('vector',{}).get('semantic'); check(sem,1024)
            ih=now['payload']['input_sha256']
            if old.get('input_sha256')!=ih or old.get('payload',{}).get('input_sha256')!=ih: continue
            cos=now['payload'].get('cos20'); check(cos,20)
            if any(cos[17:]): raise ValueError('RESERVED_COS_DIMENSION_NONZERO')
            src=str(old.get('payload',{}).get('git_sha','UNKNOWN')); sources[src]+=1; reused.add(i)
            yield {'id':i,'vector':{'semantic':sem,'cos20':cos},'payload':now['payload'],'input_sha256':ih,'chunks_sha256':cd,'model_digest':MODEL_DIGEST,'producer_shard':'REUSED','reused_from_source_commit':src}
    write(reuse_path,gen())
    todo=[cur[i] for i in sorted(set(cur)-reused)]; write(todo_path,todo); removed.sort(); dump(out/'removed.json',removed)
    rec={'schema':'SWISS-SEMANTIC-DELTA-PLAN-1.0','authority':'NON_AUTHORITATIVE','current_count':len(cur),'baseline_count':baseline_n,'reused':len(reused),'todo':len(todo),'removed':len(removed),'reuse_ratio':len(reused)/len(cur) if cur else 1.0,'chunks_sha256':cd,'baseline_vectors_sha256':sha(baseline.read_bytes()),'model_digest':MODEL_DIGEST,'reuse_source_commits':dict(sorted(sources.items())),'reuse_vectors_sha256':sha(reuse_path.read_bytes()),'todo_sha256':sha(todo_path.read_bytes())}
    dump(out/'delta-receipt.json',rec); print(json.dumps(rec,sort_keys=True))

def merge(package:Path,parts:Path,out:Path,shards:int):
    exp=current_map(package/'chunks.jsonl'); manifest=json.loads((package/'manifest.json').read_text()); cd=sha((package/'chunks.jsonl').read_bytes())
    if manifest.get('chunks_sha256')!=cd: raise ValueError('MANIFEST_HASH_MISMATCH')
    d=package/'delta'; planrec=json.loads((d/'delta-receipt.json').read_text())
    if planrec.get('chunks_sha256')!=cd or planrec.get('model_digest')!=MODEL_DIGEST: raise ValueError('DELTA_PLAN_MISMATCH')
    got={}
    for r in rows(d/'reuse-vectors.jsonl.gz'):
        i=r['id']; now=exp.get(i)
        if not now or i in got or r.get('payload')!=now['payload'] or r.get('input_sha256')!=now['payload']['input_sha256']: raise ValueError('REUSE_PROVENANCE_MISMATCH')
        check(r['vector']['semantic'],1024); check(r['vector']['cos20'],20); got[i]=r
    todo={r['id']:r for r in rows(d/'todo.jsonl')}; td=sha((d/'todo.jsonl').read_bytes()); embedded=0; receipts=[]
    for s in range(shards):
        rp=list(parts.rglob(f'receipt-{s}.json')); vp=list(parts.rglob(f'vectors-{s}.jsonl.gz'))
        if len(rp)!=1 or len(vp)!=1: raise ValueError(f'MISSING_OR_DUPLICATE_SHARD:{s}')
        rr=json.loads(rp[0].read_text())
        if rr.get('status')!='COMPLETE' or rr.get('chunks_sha256')!=td or rr.get('model_digest')!=MODEL_DIGEST or sha(vp[0].read_bytes())!=rr.get('file_sha256'): raise ValueError(f'SHARD_CONTRACT_MISMATCH:{s}')
        batch=list(rows(vp[0]))
        if len(batch)!=rr.get('count'): raise ValueError('SHARD_COUNT_MISMATCH')
        for r in batch:
            i=r['id']; now=exp.get(i)
            if not now or i in got or i not in todo or int(uuid.UUID(i))%shards!=s or r.get('payload')!=now['payload'] or r.get('input_sha256')!=now['payload']['input_sha256']: raise ValueError('EMBED_PROVENANCE_OR_ROUTING_MISMATCH')
            check(r['vector']['semantic'],1024); check(r['vector']['cos20'],20); got[i]=r; embedded+=1
        receipts.append(rr)
    if set(got)!=set(exp) or embedded!=len(todo): raise ValueError('INCOMPLETE_CURRENT_CORPUS')
    out.mkdir(parents=True,exist_ok=True); final=out/'vectors.jsonl.gz'; write(final,(got[i] for i in sorted(got)))
    rec={'schema':'SWISS-SEMANTIC-MERGE-3.0','status':'COMPLETE','authority':'NON_AUTHORITATIVE','source_commit':manifest['source_commit'],'source_tree':manifest['source_tree'],'count':len(got),'expected':len(exp),'reused':planrec['reused'],'embedded':embedded,'removed_from_baseline':planrec['removed'],'reuse_ratio':planrec['reuse_ratio'],'chunks_sha256':cd,'model_digest':MODEL_DIGEST,'shards':receipts,'vectors_sha256':sha(final.read_bytes())}
    dump(out/'merge-receipt.json',rec); print(json.dumps(rec,sort_keys=True))

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('plan'); p.add_argument('--chunks',type=Path,required=True); p.add_argument('--baseline',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('merge'); p.add_argument('--package',type=Path,required=True); p.add_argument('--parts',type=Path,required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--shards',type=int,default=8)
    a=ap.parse_args(); plan(a.chunks,a.baseline,a.out) if a.cmd=='plan' else merge(a.package,a.parts,a.out,a.shards)
if __name__=='__main__': main()
