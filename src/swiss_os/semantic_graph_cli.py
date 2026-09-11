from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any, Sequence

from .cos_graph import COS_DIMENSIONS, cos20_features, cos20_for_chunk
from .repo_semantics import chunk_repository, graphify_chunks, write_graph_jsonl
from .semantic_index import (
    COS20_VECTOR_NAME,
    SEMANTIC_VECTOR_NAME,
    OllamaEmbeddingClient,
    QdrantRepoIndex,
    SemanticGraphEngine,
    SemanticIndexError,
)


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen3-embedding:0.6b"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "swiss_os_repo_semantic"
DEFAULT_REPO_ID = "rotprods/swiss-OS"
DEFAULT_GRAPH_OUT = ".swiss-os/graphify/graph.jsonl"
DEFAULT_MANIFEST_OUT = ".swiss-os/graphify/manifest.json"

_BENCH_QUERIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("North Star verified viable Swiss job offer relocation", ("GOAL.md",)),
    ("agent session claim fencing token stale writer", ("AGENTS.md", "V2_ARCHITECTURE.md", "v2_coordination.py")),
    ("COS 20D GraphRAG similarity retrieval layers", ("V2_GRAPH_MODEL.md",)),
    ("wave transaction fail closed authority outbound", ("WAVE_OPERATING_PROTOCOL.md", "META_EXECUTION_PROTOCOL.md", "AGENTS.md")),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


def _git_sha(root: str | Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(Path(root).resolve()), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "UNRESOLVED_LOCAL_GIT_SHA"


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _clients(args: argparse.Namespace, *, collection: str | None = None) -> tuple[OllamaEmbeddingClient, QdrantRepoIndex, SemanticGraphEngine]:
    embedder = OllamaEmbeddingClient(
        base_url=args.ollama_url,
        model=args.model,
        timeout=args.timeout,
    )
    qdrant = QdrantRepoIndex(
        base_url=args.qdrant_url,
        collection=collection or args.collection,
        timeout=args.timeout,
    )
    return embedder, qdrant, SemanticGraphEngine(embedder, qdrant)


def _chunk_and_graph(args: argparse.Namespace):
    t0 = time.perf_counter()
    chunks, chunk_stats = chunk_repository(
        args.repo,
        max_chars=args.chunk_chars,
        overlap_lines=args.overlap_lines,
        max_file_bytes=args.max_file_bytes,
    )
    chunk_seconds = time.perf_counter() - t0
    t1 = time.perf_counter()
    nodes, edges = graphify_chunks(chunks)
    graph_seconds = time.perf_counter() - t1
    return chunks, chunk_stats, nodes, edges, chunk_seconds, graph_seconds


def _cos_coverage(chunks) -> dict[str, Any]:
    counts = {f"{code}:{name}": 0 for code, name in COS_DIMENSIONS}
    all_zero = 0
    for chunk in chunks:
        result = cos20_for_chunk(chunk)
        if not any(result.vector):
            all_zero += 1
        for label in result.active_dimensions:
            counts[label] += 1
    return {
        "chunks": len(chunks),
        "all_zero_vectors": all_zero,
        "dimension_chunk_counts": counts,
        "reserved_dimensions_nonzero": sum(counts[f"L{i}:Reserved"] for i in (17, 18, 19)),
    }


def cmd_scan(args: argparse.Namespace) -> int:
    chunks, stats, nodes, edges, chunk_seconds, graph_seconds = _chunk_and_graph(args)
    write_graph_jsonl(args.graph_out, nodes, edges)
    payload = {
        "schema_version": "SWISS-GRAPHIFY-MANIFEST-1.0",
        "generated_at": _utc_now(),
        "repo": args.repo_id,
        "repo_root": str(Path(args.repo).resolve()),
        "git_sha": _git_sha(args.repo),
        "authority": "DERIVED_NON_AUTHORITATIVE_REPOSITORY_INDEX",
        "chunking": asdict(stats),
        "chunk_seconds": chunk_seconds,
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "graph_seconds": graph_seconds,
        "cos20": _cos_coverage(chunks),
        "graph_out": args.graph_out,
    }
    _write_json(args.manifest_out, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    chunks, stats, nodes, edges, chunk_seconds, graph_seconds = _chunk_and_graph(args)
    if not chunks:
        print(json.dumps({"indexed": False, "error": "no indexable repository chunks"}), file=sys.stderr)
        return 2
    write_graph_jsonl(args.graph_out, nodes, edges)
    embedder, qdrant, engine = _clients(args)
    try:
        embedder.health()
        qdrant.health()
        index_stats = engine.index(
            chunks,
            repo=args.repo_id,
            git_sha=_git_sha(args.repo),
            batch_size=args.batch_size,
            recreate_collection=args.recreate_collection,
            replace_repo=not args.no_replace_repo,
        )
    except (SemanticIndexError, ValueError) as exc:
        print(json.dumps({"indexed": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    payload = {
        "schema_version": "SWISS-GRAPHIFY-MANIFEST-1.0",
        "generated_at": _utc_now(),
        "repo": args.repo_id,
        "repo_root": str(Path(args.repo).resolve()),
        "git_sha": _git_sha(args.repo),
        "authority": "DERIVED_NON_AUTHORITATIVE_RETRIEVAL_INDEX",
        "ollama": {"url": args.ollama_url, "model": args.model},
        "qdrant": {"url": args.qdrant_url, "collection": args.collection, "named_vectors": [SEMANTIC_VECTOR_NAME, COS20_VECTOR_NAME]},
        "chunking": asdict(stats),
        "chunk_seconds": chunk_seconds,
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "graph_seconds": graph_seconds,
        "cos20": _cos_coverage(chunks),
        "index": index_stats.as_dict(),
        "graph_out": args.graph_out,
    }
    _write_json(args.manifest_out, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    lower = int(pos)
    upper = min(lower + 1, len(ordered) - 1)
    frac = pos - lower
    return ordered[lower] * (1 - frac) + ordered[upper] * frac


def cmd_benchmark(args: argparse.Namespace) -> int:
    chunks, stats, nodes, edges, chunk_seconds, graph_seconds = _chunk_and_graph(args)
    if args.max_chunks and len(chunks) > args.max_chunks:
        chunks = chunks[: args.max_chunks]
    if not chunks:
        print(json.dumps({"benchmark": False, "error": "no chunks"}), file=sys.stderr)
        return 2
    bench_collection = f"{args.collection}__bench_{int(time.time() * 1000)}"
    embedder, qdrant, engine = _clients(args, collection=bench_collection)
    report: dict[str, Any] = {
        "schema_version": "SWISS-SEMANTIC-BENCH-1.0",
        "generated_at": _utc_now(),
        "repo": args.repo_id,
        "git_sha": _git_sha(args.repo),
        "model": args.model,
        "bench_collection": bench_collection,
        "sample_chunks": len(chunks),
        "full_scan_chunks": stats.chunks,
        "chunk_seconds": chunk_seconds,
        "graph_seconds": graph_seconds,
        "cos20": _cos_coverage(chunks),
    }
    exit_code = 0
    try:
        embedder.health()
        qdrant.health()
        index_stats = engine.index(
            chunks,
            repo=args.repo_id,
            git_sha=report["git_sha"],
            batch_size=args.batch_size,
            recreate_collection=True,
            replace_repo=False,
        )
        report["index"] = index_stats.as_dict()
        query_rows: list[dict[str, Any]] = []
        latencies: dict[str, list[float]] = {"semantic": [], "cos20": [], "hybrid": []}
        quality_hits = 0
        for query, expected in _BENCH_QUERIES:
            row: dict[str, Any] = {"query": query, "expected_path_fragments": list(expected), "spaces": {}}
            for space in ("semantic", "cos20", "hybrid"):
                started = time.perf_counter()
                hits = engine.search(query, repo=args.repo_id, limit=args.top_k, space=space)
                elapsed = time.perf_counter() - started
                latencies[space].append(elapsed)
                paths = [str(hit.payload.get("path", "")) for hit in hits]
                row["spaces"][space] = {
                    "latency_seconds": elapsed,
                    "top_paths": paths,
                    "scores": [hit.score for hit in hits],
                }
            hybrid_paths = row["spaces"]["hybrid"]["top_paths"]
            matched = any(any(fragment in path for fragment in expected) for path in hybrid_paths)
            row["hybrid_expected_hit"] = matched
            quality_hits += int(matched)
            query_rows.append(row)
        report["queries"] = query_rows
        report["quality"] = {
            "hybrid_expected_hits": quality_hits,
            "query_count": len(_BENCH_QUERIES),
            "hybrid_expected_hit_rate": quality_hits / len(_BENCH_QUERIES),
        }
        report["latency"] = {
            space: {
                "p50_seconds": statistics.median(values) if values else 0.0,
                "p95_seconds": _percentile(values, 0.95),
                "max_seconds": max(values) if values else 0.0,
            }
            for space, values in latencies.items()
        }
        if args.enforce_quality and report["quality"]["hybrid_expected_hit_rate"] < args.min_hit_rate:
            report["quality_gate"] = "FAIL"
            exit_code = 3
        else:
            report["quality_gate"] = "PASS" if args.enforce_quality else "OBSERVE_ONLY"
    except (SemanticIndexError, ValueError) as exc:
        report["error"] = str(exc)
        report["quality_gate"] = "BLOCKED"
        exit_code = 2
    finally:
        if not args.keep_benchmark_collection:
            try:
                qdrant.delete_collection()
                report["bench_collection_deleted"] = True
            except Exception as exc:  # cleanup should not hide benchmark result
                report["bench_collection_deleted"] = False
                report["cleanup_error"] = str(exc)
    _write_json(args.out, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


def cmd_explain(args: argparse.Namespace) -> int:
    result = cos20_features(args.text, path=args.path or "")
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    embedder, qdrant, engine = _clients(args)
    try:
        if args.space != COS20_VECTOR_NAME:
            embedder.health()
        qdrant.health()
        hits = engine.search(args.text, repo=args.repo_id if args.repo_filter else None, limit=args.limit, space=args.space)
    except (SemanticIndexError, ValueError) as exc:
        print(json.dumps({"query_ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    payload = {
        "query": args.text,
        "space": args.space,
        "repo_filter": args.repo_id if args.repo_filter else None,
        "hits": [hit.as_dict() for hit in hits],
    }
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    embedder, qdrant, _ = _clients(args)
    payload: dict[str, Any] = {
        "ollama_url": args.ollama_url,
        "model": args.model,
        "qdrant_url": args.qdrant_url,
        "collection": args.collection,
        "repo": args.repo_id,
    }
    try:
        payload["ollama"] = "OK"
        embedder.health()
    except SemanticIndexError as exc:
        payload["ollama"] = f"ERROR: {exc}"
    try:
        qdrant.health()
        collection = qdrant.get_collection()
        payload["qdrant"] = "OK"
        payload["collection_exists"] = collection is not None
        payload["repo_points"] = qdrant.count(repo=args.repo_id) if collection else 0
    except SemanticIndexError as exc:
        payload["qdrant"] = f"ERROR: {exc}"
        payload["collection_exists"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ollama") == "OK" and payload.get("qdrant") == "OK" else 2


def _add_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ollama-url", default=_env("SWISS_OS_OLLAMA_URL", DEFAULT_OLLAMA_URL))
    parser.add_argument("--model", default=_env("SWISS_OS_EMBED_MODEL", DEFAULT_OLLAMA_MODEL))
    parser.add_argument("--qdrant-url", default=_env("SWISS_OS_QDRANT_URL", DEFAULT_QDRANT_URL))
    parser.add_argument("--collection", default=_env("SWISS_OS_QDRANT_COLLECTION", DEFAULT_COLLECTION))
    parser.add_argument("--repo-id", default=_env("SWISS_OS_REPO_ID", DEFAULT_REPO_ID))
    parser.add_argument("--timeout", type=float, default=float(_env("SWISS_OS_SEMANTIC_TIMEOUT", "120")))


def _add_repo_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=".")
    parser.add_argument("--repo-id", default=_env("SWISS_OS_REPO_ID", DEFAULT_REPO_ID))
    parser.add_argument("--chunk-chars", type=int, default=int(_env("SWISS_OS_CHUNK_CHARS", "6000")))
    parser.add_argument("--overlap-lines", type=int, default=int(_env("SWISS_OS_CHUNK_OVERLAP_LINES", "8")))
    parser.add_argument("--max-file-bytes", type=int, default=int(_env("SWISS_OS_MAX_FILE_BYTES", "4000000")))
    parser.add_argument("--graph-out", default=DEFAULT_GRAPH_OUT)
    parser.add_argument("--manifest-out", default=DEFAULT_MANIFEST_OUT)


def graphify_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="graphify", description="Semantic repository graph compiler for SWISS-OS")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Chunk and graphify the repository without network services")
    _add_repo_args(scan)

    index = sub.add_parser("index", help="Chunk the full repository and index semantic + COS20 vectors in Qdrant")
    _add_repo_args(index)
    _add_connection_args_without_repo_id(index)
    index.add_argument("--batch-size", type=int, default=int(_env("SWISS_OS_EMBED_BATCH_SIZE", "24")))
    index.add_argument("--recreate-collection", action="store_true")
    index.add_argument("--no-replace-repo", action="store_true")

    bench = sub.add_parser("benchmark", help="Run an isolated live Ollama/Qdrant benchmark and retrieval QA")
    _add_repo_args(bench)
    _add_connection_args_without_repo_id(bench)
    bench.add_argument("--batch-size", type=int, default=int(_env("SWISS_OS_EMBED_BATCH_SIZE", "24")))
    bench.add_argument("--max-chunks", type=int, default=240)
    bench.add_argument("--top-k", type=int, default=5)
    bench.add_argument("--out", default=".swiss-os/benchmarks/semantic-graph.json")
    bench.add_argument("--keep-benchmark-collection", action="store_true")
    bench.add_argument("--enforce-quality", action="store_true")
    bench.add_argument("--min-hit-rate", type=float, default=0.75)
    return parser


def _add_connection_args_without_repo_id(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ollama-url", default=_env("SWISS_OS_OLLAMA_URL", DEFAULT_OLLAMA_URL))
    parser.add_argument("--model", default=_env("SWISS_OS_EMBED_MODEL", DEFAULT_OLLAMA_MODEL))
    parser.add_argument("--qdrant-url", default=_env("SWISS_OS_QDRANT_URL", DEFAULT_QDRANT_URL))
    parser.add_argument("--collection", default=_env("SWISS_OS_QDRANT_COLLECTION", DEFAULT_COLLECTION))
    parser.add_argument("--timeout", type=float, default=float(_env("SWISS_OS_SEMANTIC_TIMEOUT", "120")))


def cos_graph_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cos-graph-engine", description="Query SWISS-OS semantic + COS 20D repository graph")
    sub = parser.add_subparsers(dest="command", required=True)

    explain = sub.add_parser("explain", help="Explain the exact COS L0-L19 vector for text")
    explain.add_argument("text")
    explain.add_argument("--path")

    query = sub.add_parser("query", help="Query semantic, COS20, or hybrid retrieval")
    query.add_argument("text")
    query.add_argument("--space", choices=[SEMANTIC_VECTOR_NAME, COS20_VECTOR_NAME, "hybrid"], default="hybrid")
    query.add_argument("--limit", type=int, default=10)
    query.add_argument("--repo-filter", action=argparse.BooleanOptionalAction, default=True)
    _add_connection_args(query)

    status = sub.add_parser("status", help="Check Ollama, Qdrant, collection and repository point count")
    _add_connection_args(status)
    return parser


def graphify_main(argv: Sequence[str] | None = None) -> int:
    args = graphify_parser().parse_args(argv)
    if args.command == "scan":
        return cmd_scan(args)
    if args.command == "index":
        return cmd_index(args)
    if args.command == "benchmark":
        return cmd_benchmark(args)
    return 2


def cos_graph_main(argv: Sequence[str] | None = None) -> int:
    args = cos_graph_parser().parse_args(argv)
    if args.command == "explain":
        return cmd_explain(args)
    if args.command == "query":
        return cmd_query(args)
    if args.command == "status":
        return cmd_status(args)
    return 2


if __name__ == "__main__":
    # Developer convenience: python -m swiss_os.semantic_graph_cli graphify|cos ...
    argv = sys.argv[1:]
    if not argv:
        raise SystemExit("expected graphify or cos-graph-engine")
    mode, rest = argv[0], argv[1:]
    if mode == "graphify":
        raise SystemExit(graphify_main(rest))
    if mode in {"cos", "cos-graph-engine"}:
        raise SystemExit(cos_graph_main(rest))
    raise SystemExit(f"unknown mode: {mode}")
