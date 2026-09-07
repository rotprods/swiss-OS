# SEMANTIC GRAPH INDEX — OLLAMA + QDRANT + COS 20D

Version: **SGI-1.0**  
Status: **DERIVED RETRIEVAL INDEX / NON-AUTHORITATIVE**  
Engine ownership: **E12 Operational Graph Engine + E13 Project Memory Meta Graph Engine**  
Authority effect: **NONE**

## 1. Decision

SWISS-OS now has an optional local repository semantic index for code/document archaeology, zero-context recovery, GraphRAG and cross-file retrieval.

This is **not a new domain engine, operational authority plane, coordination authority plane, database of record or outbound capability**. It is a disposable derived index. Deleting Qdrant must never change project truth; `graphify` can rebuild it from a Git checkout.

This contract narrowly refines the earlier V2 statement that a vector database was not justified at the then-observed workload. The new workload is explicit: semantic chunk retrieval over the complete repository. Qdrant is permitted only for this derived retrieval workload and remains optional for correctness.

## 2. Topology

```text
Git checkout @ SHA
  └─ graphify
      ├─ text/binary/privacy filter
      ├─ semantic chunk compiler
      │   ├─ Python AST symbols
      │   ├─ Markdown heading sections
      │   └─ bounded generic text chunks
      ├─ structural graph projection
      │   └─ .swiss-os/graphify/graph.jsonl
      ├─ Ollama /api/embed
      │   └─ named vector: semantic (native model dimension)
      └─ COS L0-L19 classifier
          └─ named vector: cos20 (exactly 20 dimensions)
                    │
                    ▼
              Qdrant collection
        swiss_os_repo_semantic
```

The collection uses cosine distance for both named vectors. Qdrant supports multiple named vectors with independent dimensions in one point, so the native embedding is not degraded merely to satisfy the conceptual COS 20D model.

## 3. Embedding model

Default:

```text
qwen3-embedding:0.6b
```

Rationale: local, multilingual, code-retrieval capable, 639 MB Ollama artifact, 32K context, and materially cheaper to index iteratively than the 4B/8B variants. The dimension is **auto-discovered at runtime** from the first `/api/embed` response; no model dimension is hard-coded into SWISS-OS.

Operators may switch models with:

```bash
export SWISS_OS_EMBED_MODEL=qwen3-embedding:4b
```

A semantic-dimension mismatch against an existing collection fails closed. Recreate the derived collection explicitly only when safe.

## 4. Qdrant collection contract

Collection default:

```text
swiss_os_repo_semantic
```

Named vectors:

| name | size | distance | purpose |
|---|---:|---|---|
| `semantic` | auto-discovered | Cosine | full Ollama semantic/code retrieval |
| `cos20` | 20 | Cosine | canonical COS L0-L19 architecture similarity |

Every point is one semantic chunk and carries:

- stable UUID derived from deterministic `chunk_id`;
- repository + Git SHA;
- path/language/chunk kind/symbol;
- line range + chunk ordinal;
- content/file SHA-256;
- embedding model + semantic dimension;
- exact COS active dimensions;
- explicit `DERIVED_NON_AUTHORITATIVE_RETRIEVAL_INDEX` authority label.

A full index run deletes only prior points for the same repository before upsert. It does not silently destroy unrelated repos that may share the collection.

## 5. COS 20D semantics

`cos20` is **not** a random 20-dimensional compression of the semantic embedding. Its coordinates map directly to the canonical V2 model:

```text
L0 Visual
L1 Execution
L2 State
L3 Dependency
L4 Call
L5 Control
L6 DataFlow
L7 Compute
L8 Knowledge
L9 Semantic
L10 Similarity
L11 GraphRAG
L12 Memory
L13 Agent
L14 Tool
L15 Workflow
L16 Network
L17 Reserved / NOT_APPLICABLE
L18 Reserved / NOT_APPLICABLE
L19 Reserved / NOT_APPLICABLE
```

L17-L19 remain exactly zero until the canonical graph model gives them domain-specific meaning. The classifier is deterministic, explainable and revisionable; it uses path/kind structure plus bounded lexical signals.

## 6. Retrieval modes

`cos-graph-engine query` supports:

- `semantic` — native Ollama vector only;
- `cos20` — architecture/COS layer similarity only;
- `hybrid` — semantic + COS20 reciprocal-rank fusion (default).

Similarity is review/retrieval evidence only. It never resolves hotel identity, alias authority, candidate truth or send authorization.

## 7. Graphify output

`graphify` emits a disposable local JSONL structural graph containing:

- `File` nodes;
- `Chunk` nodes;
- `Symbol` nodes when statically resolvable;
- `CONTAINS`, `DEFINES`, `IMPLEMENTED_BY`, `PRECEDES` edges.

Generated output lives under `.swiss-os/` and is Git-ignored. It is reproducible from a checkout and therefore is not committed as canonical truth.

## 8. Failure and security rules

Fail closed when:

- Ollama returns empty/inconsistent embedding dimensions;
- collection named-vector dimensions differ from the active model;
- post-index repo point count differs from generated chunk count;
- input exceeds the model context (`truncate=false` prevents silent clipping);
- network requests exhaust bounded retry attempts.

The scanner excludes repository-designated private/generated directories, binary formats and database files. Secrets remain governed by repo guard; the vector index must be treated as local derived data and must not be published.

## 9. Keep/discard benchmark gate

The integration is retained only while it improves repository retrieval without weakening protected metrics. Required evidence:

```text
semantic_graph_unit_tests = PASS
python_compileall = PASS
full_repository_graphify = PASS
qdrant_repo_point_count == generated_chunk_count
COS_reserved_L17_L19_nonzero = 0
live retrieval benchmark = PASS or explicitly OBSERVE_ONLY
repo_guard = PASS
system_contract_guard = PASS
full_unittest_suite = PASS
```

The live benchmark records indexing throughput, embedding/upsert time, query p50/p95, four repository retrieval probes and an optional >=0.75 hybrid expected-hit gate.
