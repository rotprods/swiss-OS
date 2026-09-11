#!/usr/bin/env python3
"""Local Qdrant generation manager for SWISS-OS semantic artifacts.

Qdrant is disposable DERIVED/NON_AUTHORITATIVE retrieval state. The script
uses versioned collections plus one atomic alias so a failed catch-up cannot
replace the last known-good generation.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
from pathlib import Path
import statistics
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ALIAS = "swiss_os_repo_semantic_current"
REPO = "rotprods/swiss-OS"
PROJECT = "swiss-os"
MODEL = "qwen3-embedding:0.6b"
MODEL_DIGEST = "ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d"


def http_json(base: str, method: str, path: str, data: dict | None = None, timeout: int = 120) -> dict:
    req = Request(base.rstrip("/") + path, data=None if data is None else json.dumps(data, allow_nan=False).encode(), method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP_{exc.code}:{path}:{body[:1000]}") from exc


def qdrant(method: str, path: str, data: dict | None = None) -> dict:
    return http_json(os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"), method, path, data)


def ollama(method: str, path: str, data: dict | None = None) -> dict:
    return http_json(os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434"), method, path, data, timeout=240)


def read_vectors(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def valid_vector(v: list, n: int) -> None:
    if not isinstance(v, list) or len(v) != n:
        raise ValueError(f"VECTOR_DIMENSION_MISMATCH:{len(v) if isinstance(v,list) else 'not-list'}!={n}")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in v):
        raise ValueError("NONFINITE_VECTOR")


def collection_for(source_commit: str, prefix: str = "swiss_os_repo_semantic") -> str:
    if len(source_commit) < 8 or any(c not in "0123456789abcdef" for c in source_commit.lower()):
        raise ValueError("INVALID_SOURCE_COMMIT")
    return f"{prefix}_{source_commit[:8]}"


def get_alias_target(alias: str = ALIAS) -> str | None:
    aliases = qdrant("GET", "/aliases").get("result", {}).get("aliases", [])
    for item in aliases:
        if item.get("alias_name") == alias:
            return item.get("collection_name")
    return None


def collection_info(name: str) -> dict:
    return qdrant("GET", f"/collections/{name}").get("result", {})


def ensure_collection(name: str, replace: bool) -> None:
    exists = False
    try:
        info = collection_info(name); exists = bool(info)
    except RuntimeError as exc:
        if not str(exc).startswith("HTTP_404"): raise
    if exists:
        if not replace: raise ValueError(f"COLLECTION_ALREADY_EXISTS:{name}")
        if get_alias_target() == name: raise ValueError("REFUSE_DELETE_ACTIVE_ALIAS_TARGET")
        qdrant("DELETE", f"/collections/{name}")
    qdrant("PUT", f"/collections/{name}", {"vectors": {"semantic": {"size": 1024, "distance": "Cosine"}, "cos20": {"size": 20, "distance": "Cosine"}}, "on_disk_payload": True})
    for field in ["project", "repo", "git_sha", "path", "language", "kind", "authority", "embedding_model_digest", "embedding_schema"]:
        qdrant("PUT", f"/collections/{name}/index", {"field_name": field, "field_schema": "keyword"})


def switch_alias(target: str, alias: str = ALIAS) -> None:
    old = get_alias_target(alias); actions = []
    if old: actions.append({"delete_alias": {"alias_name": alias}})
    actions.append({"create_alias": {"collection_name": target, "alias_name": alias}})
    qdrant("POST", "/collections/aliases", {"actions": actions})
    if get_alias_target(alias) != target: raise ValueError("ALIAS_SWITCH_DID_NOT_COMMIT")


def import_generation(vectors: Path, receipt: Path, *, replace: bool, batch: int, activate: bool, prefix: str) -> dict:
    merge = json.loads(receipt.read_text())
    if merge.get("status") != "COMPLETE" or merge.get("authority") != "NON_AUTHORITATIVE": raise ValueError("UNQUALIFIED_MERGE_RECEIPT")
    if merge.get("model_digest") != MODEL_DIGEST: raise ValueError("MODEL_DIGEST_MISMATCH")
    source_commit = str(merge.get("source_commit", "")); expected = int(merge.get("count", -1))
    if expected < 0 or expected != int(merge.get("expected", expected)): raise ValueError("INVALID_EXPECTED_COUNT")
    name = collection_for(source_commit, prefix); prior_alias = get_alias_target(); ensure_collection(name, replace=replace)
    started = time.perf_counter(); count = 0; batch_times: list[float] = []; current = []
    try:
        for row in read_vectors(vectors):
            if row.get("model_digest") != MODEL_DIGEST: raise ValueError("POINT_MODEL_DIGEST_MISMATCH")
            payload = row.get("payload", {})
            if payload.get("repo") != REPO or payload.get("project") != PROJECT or payload.get("git_sha") != source_commit: raise ValueError("POINT_SCOPE_OR_SOURCE_MISMATCH")
            semantic = row.get("vector", {}).get("semantic"); cos20 = row.get("vector", {}).get("cos20")
            valid_vector(semantic, 1024); valid_vector(cos20, 20)
            if any(cos20[17:]): raise ValueError("RESERVED_COS_DIMENSION_NONZERO")
            current.append({"id": row["id"], "vector": {"semantic": semantic, "cos20": cos20}, "payload": payload})
            if len(current) >= batch:
                t0 = time.perf_counter(); qdrant("PUT", f"/collections/{name}/points?wait=true", {"points": current}); batch_times.append(time.perf_counter()-t0); count += len(current); current = []
        if current:
            t0 = time.perf_counter(); qdrant("PUT", f"/collections/{name}/points?wait=true", {"points": current}); batch_times.append(time.perf_counter()-t0); count += len(current)
        info = collection_info(name); actual = int(info.get("points_count", -1))
        if count != expected or actual != expected or info.get("status") != "green": raise ValueError(f"POST_IMPORT_CARDINALITY_OR_HEALTH_MISMATCH:{count}:{actual}:{expected}:{info.get('status')}")
        if activate: switch_alias(name)
        total = time.perf_counter() - started
        result = {"status": "PASS", "authority": "NON_AUTHORITATIVE", "collection": name, "alias": ALIAS if activate else None, "previous_alias_target": prior_alias, "source_commit": source_commit, "count": count, "seconds": total, "points_per_second": count / total if total else None, "batch_seconds_p50": statistics.median(batch_times) if batch_times else 0.0, "batch_seconds_max": max(batch_times) if batch_times else 0.0}
        print(json.dumps(result, sort_keys=True)); return result
    except Exception:
        if get_alias_target() != name:
            try: qdrant("DELETE", f"/collections/{name}")
            except Exception: pass
        raise


def embed_query(text: str) -> list[float]:
    tags = ollama("GET", "/api/tags").get("models", [])
    if not any(m.get("name") == MODEL and m.get("digest") == MODEL_DIGEST for m in tags): raise ValueError("LOCAL_MODEL_DIGEST_MISMATCH")
    response = ollama("POST", "/api/embed", {"model": MODEL, "input": [text], "truncate": False, "keep_alive": "30m"})
    vec = response.get("embeddings", [[]])[0]; valid_vector(vec, 1024); return vec


def query_alias(text: str, limit: int) -> dict:
    t0 = time.perf_counter(); vector = embed_query(text); embed_seconds = time.perf_counter() - t0
    t1 = time.perf_counter(); result = qdrant("POST", f"/collections/{ALIAS}/points/query", {"query": vector, "using": "semantic", "limit": limit, "with_payload": True}).get("result", {}); q_seconds = time.perf_counter() - t1
    points = result.get("points", result if isinstance(result, list) else [])
    return {"query": text, "embed_seconds": embed_seconds, "qdrant_seconds": q_seconds, "hits": [{"score": p.get("score"), "path": p.get("payload", {}).get("path"), "kind": p.get("payload", {}).get("kind"), "symbol": p.get("payload", {}).get("symbol")} for p in points]}


def benchmark(out: Path | None) -> dict:
    queries = ["North Star find a job in Switzerland before moving", "fencing token active claim agent runtime coordination", "outbound closed send_allowed authority gate", "entity resolution locality canonical hotel reconciliation", "recovery deterministic rebuild context survival death safe"]
    rows = [query_alias(q, 5) for q in queries]; q_times = [r["qdrant_seconds"] for r in rows]; e_times = [r["embed_seconds"] for r in rows]
    value = {"status": "PASS", "authority": "NON_AUTHORITATIVE", "alias_target": get_alias_target(), "queries": rows, "qdrant_p50_seconds": statistics.median(q_times), "qdrant_max_seconds": max(q_times), "embedding_p50_seconds": statistics.median(e_times), "embedding_max_seconds": max(e_times)}
    if out: out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps(value, sort_keys=True)); return value


def snapshot(name: str) -> dict:
    result = qdrant("POST", f"/collections/{name}/snapshots").get("result", {}); print(json.dumps(result, sort_keys=True)); return result


def status() -> dict:
    target = get_alias_target(); info = collection_info(target) if target else {}
    value = {"alias": ALIAS, "target": target, "status": info.get("status"), "points_count": info.get("points_count"), "vectors_count": info.get("vectors_count")}; print(json.dumps(value, sort_keys=True)); return value


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__); sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("import"); p.add_argument("--vectors", type=Path, required=True); p.add_argument("--receipt", type=Path, required=True); p.add_argument("--batch", type=int, default=128); p.add_argument("--replace", action="store_true"); p.add_argument("--no-activate", action="store_true"); p.add_argument("--prefix", default="swiss_os_repo_semantic")
    p = sub.add_parser("switch"); p.add_argument("--collection", required=True)
    p = sub.add_parser("benchmark"); p.add_argument("--out", type=Path)
    p = sub.add_parser("snapshot"); p.add_argument("--collection")
    sub.add_parser("status")
    args = ap.parse_args()
    if args.command == "import": import_generation(args.vectors, args.receipt, replace=args.replace, batch=args.batch, activate=not args.no_activate, prefix=args.prefix)
    elif args.command == "switch": switch_alias(args.collection); status()
    elif args.command == "benchmark": benchmark(args.out)
    elif args.command == "snapshot": snapshot(args.collection or get_alias_target() or (_ for _ in ()).throw(ValueError("NO_ALIAS_TARGET")))
    elif args.command == "status": status()


if __name__ == "__main__": main()
