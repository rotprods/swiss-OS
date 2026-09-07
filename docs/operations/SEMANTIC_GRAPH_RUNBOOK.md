# SEMANTIC GRAPH RUNBOOK — `/graphify` + `/cos-graph-engine`

Version: **SGR-1.0**  
Scope: local developer/agent repository retrieval only.

## Bootstrap on the Mac mini

From repository root:

```bash
./scripts/bootstrap_semantic_graph.sh
```

The bootstrap:

1. starts pinned Qdrant `v1.19.0` via Docker Compose;
2. verifies/starts native local Ollama;
3. pulls `qwen3-embedding:0.6b` unless overridden;
4. chunks and graphifies the full Git checkout;
5. indexes both named vectors into Qdrant;
6. verifies exact repository point cardinality;
7. runs an isolated benchmark collection and retrieval QA;
8. prints final health/count status.

No operational hotel authority is mutated.

## Manual commands

Pure graph compile, no network:

```bash
PYTHONPATH=src python -m swiss_os.semantic_graph_cli graphify scan --repo .
```

Full semantic index:

```bash
PYTHONPATH=src python -m swiss_os.semantic_graph_cli graphify index --repo .
```

Benchmark:

```bash
PYTHONPATH=src python -m swiss_os.semantic_graph_cli graphify benchmark --repo . --enforce-quality
```

Inspect 20D mapping:

```bash
PYTHONPATH=src python -m swiss_os.semantic_graph_cli cos-graph-engine explain \
  "agent claim fencing workflow retry GraphRAG"
```

Hybrid query:

```bash
PYTHONPATH=src python -m swiss_os.semantic_graph_cli cos-graph-engine query \
  "where is stale writer fencing enforced?" \
  --space hybrid --limit 8
```

Status:

```bash
PYTHONPATH=src python -m swiss_os.semantic_graph_cli cos-graph-engine status
```

After package installation the equivalent console commands are:

```bash
graphify scan
graphify index
graphify benchmark --enforce-quality
cos-graph-engine query "..."
```

## Configuration

```text
SWISS_OS_OLLAMA_URL          default http://127.0.0.1:11434
SWISS_OS_EMBED_MODEL         default qwen3-embedding:0.6b
SWISS_OS_QDRANT_URL          default http://127.0.0.1:6333
SWISS_OS_QDRANT_COLLECTION   default swiss_os_repo_semantic
SWISS_OS_REPO_ID             default rotprods/swiss-OS
SWISS_OS_CHUNK_CHARS         default 6000
SWISS_OS_CHUNK_OVERLAP_LINES default 8
SWISS_OS_MAX_FILE_BYTES      default 4000000
SWISS_OS_EMBED_BATCH_SIZE    default 24
SWISS_OS_SEMANTIC_TIMEOUT    default 120
```

## Model ladder

Use the smallest model that meets retrieval QA on the actual corpus:

```text
qwen3-embedding:0.6b  -> default throughput/cost baseline
qwen3-embedding:4b    -> quality escalation
qwen3-embedding:8b    -> highest local quality candidate if hardware/latency justify it
```

Changing to a model with a different output dimension requires explicit derived collection recreation:

```bash
graphify index --recreate-collection
```

Do this only when the collection contains no irreplaceable data. The index is designed to be fully rebuildable.

## Benchmark interpretation

The report is written to:

```text
.swiss-os/benchmarks/semantic-graph.json
```

Review:

- `index.chunks_per_second`;
- `index.embedding_seconds` vs `index.upsert_seconds`;
- `latency.*.p50_seconds` / `p95_seconds`;
- `quality.hybrid_expected_hit_rate`;
- `cos20.reserved_dimensions_nonzero` (must be 0);
- post-index exact point count.

A benchmark collection is deleted automatically after the run unless `--keep-benchmark-collection` is set.

## Recovery

The index is disposable:

```bash
docker compose -f docker-compose.semantic.yml down
# optional destructive reset of derived Qdrant storage only:
docker compose -f docker-compose.semantic.yml down -v
./scripts/bootstrap_semantic_graph.sh
```

Never restore the Qdrant collection as operational authority. Rebuild it from the exact Git SHA instead.
