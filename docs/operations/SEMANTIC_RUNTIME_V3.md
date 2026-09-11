# SWISS-OS Semantic Runtime V3

## Authority

This subsystem is a derived, disposable, non-authoritative retrieval projection. Deleting Qdrant must never change hotel/CRM/candidate truth, H-ID allocation, application state, outbound permission, or GRAPH-REFACTOR-V2 ownership. E12/E13 remain the canonical graph/memory ownership.

## Runtime contract

- Ollama `0.33.2`, CPU-compatible.
- `qwen3-embedding:0.6b`, required digest `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d`.
- Semantic vector: 1024D cosine.
- Structural vector: canonical COS L0-L19, 20D cosine; L17-L19 remain zero while reserved.
- Qdrant reference runtime: `1.19.0`.
- Active alias: `swiss_os_repo_semantic_current`.
- Immutable generations: `swiss_os_repo_semantic_<source-sha8>`.

## Incremental compiler

V3 makes work proportional to changed semantic content rather than total repository size.

1. `semantic_runtime_v2.py scan` compiles the exact clean Git source SHA into chunks, graph and inventory.
2. `semantic_delta_v3.py plan` compares current chunks with the newest validated vector artifact.
3. A vector is reusable only when point ID, embedding input SHA256 and pinned model digest agree.
4. Reused semantic vectors receive the **current** payload and current COS20 vector; stale `git_sha` payloads never propagate.
5. Removed baseline IDs disappear from the next generation.
6. Only `todo.jsonl` is embedded, deterministically partitioned across eight workers.
7. `semantic_delta_v3.py merge` rejects missing, duplicate, stale, misrouted or provenance-mismatched vectors and requires exact current-corpus coverage.
8. If no reusable artifact exists, the workflow falls back to a full rebuild instead of accepting a partial index.

Validated V3 artifacts are deterministic where the runtime controls serialization; gzip reuse artifacts use `mtime=0`.

## Qdrant generation transaction

`scripts/semantic_qdrant_v3.py` imports a complete validated artifact into an isolated generation, checks exact cardinality and `green` health, and only then switches `swiss_os_repo_semantic_current` in one alias transaction. A failed candidate never replaces the last known-good alias target. Previous generations remain rollback candidates until explicit garbage collection.

Qualification sequence:

```text
validated vector artifact
 -> isolated generation import
 -> cardinality/schema/health
 -> semantic benchmark
 -> atomic alias switch
 -> snapshot
 -> process restart
 -> alias/cardinality/health recheck
 -> rollback switch drill
 -> switch forward
```

## Baseline physical evidence

Before the V3 catch-up, the virtual PC physically qualified the validated V2 generation:

- collection `swiss_os_repo_semantic_1072d5cf`;
- 4,383 / 4,383 points;
- semantic=1024D and cos20=20D;
- `green` health;
- alias `swiss_os_repo_semantic_current`;
- initial measured import throughput about 921 points/s;
- Qdrant snapshot about 59.6 MB, checksum `7610137c3f28ecf710b14bb0987a7443c9f60ec6a17f6cf5ea9ae3098b231b6f`;
- restart preserved alias and all 4,383 points;
- runner/local embedding parity approximately cosine 0.9996-0.9997;
- measured Qdrant query p50 about 25.6 ms; CPU query embedding was the dominant latency.

These numbers qualify the baseline only. A current-main generation must produce its own merge/import/recovery receipts.

## Recovery/liveness

The V3 workflow resolves the newest non-expired `swiss-semantic-v3-vectors-validated` artifact. For the first catch-up it can seed from the validated V2 artifact. If neither exists it emits an empty baseline and performs a full rebuild. Artifact loss therefore degrades throughput, not correctness or liveness.

Qdrant is never the sole copy of knowledge: Git + the pinned model can regenerate any generation. Snapshots accelerate recovery but are not authority.

## Definition of done

V3 is complete only when source SHA matches the intended `main`, delta plan is hash-bound, all shard receipts are complete, merge count equals current chunk count exactly, local Qdrant count equals the merge receipt, schemas are 1024D/20D, fixed retrieval probes are plausible, snapshot/restart passes, rollback alias drill passes and forward alias is restored, semantic tests and repository guards pass, and claim/heartbeat/iteration/coordination state is death-safe. `OUTBOUND=CLOSED`, `send_allowed=0`; no H-ID or canonical authority advancement is permitted.
