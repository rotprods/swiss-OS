# GRAPH REFACTOR V2 — ADVERSARIAL GAUNTLET

Version: **GRV2-GAUNTLET-1.0**  
Status: **FOUNDATION ASSURANCE CONTRACT**  
Owner: Adversarial Reviewer / QA Governance / CISO  
Last updated: 2026-08-30

## 1. Assurance result vocabulary

```text
PASS
FAIL
SKIPPED
CANCELLED
NOT_RUN
NOT_APPLICABLE
```

No state may be collapsed into PASS.

## 2. Foundation gates

| Gate | Assertion | Foundation evidence |
|---|---|---|
| G00 North Star | Architecture cannot replace offer outcome with graph/CI metrics | architecture + product projection |
| G01 Authority | V2 artifact cannot advance domain authority | manifest hard fields + test |
| G02 Identity | node/event/session/claim IDs are unique and validated | kernel tests |
| G03 Event | duplicate, altered, out-of-order or broken-chain event rejected | ledger tests |
| G04 Graph | missing endpoint, duplicate ID and hard dependency cycle rejected | graph tests |
| G05 Hyperedge | at least two distinct participants and explicit roles | graph tests |
| G06 Session | globally unique lifecycle; closed session cannot mutate | coordination tests |
| G07 Claim | overlapping write scope collides; safe non-overlap remains parallel | coordination tests |
| G08 Lease | expiry and takeover issue newer fencing token | coordination tests |
| G09 Fence | stale holder cannot write after takeover | coordination tests |
| G10 Context | moved SHA/watermark/projection invalidates ContextPack | ContextPack tests |
| G11 Secret | public ContextPack redacts key/value secret patterns | security tests |
| G12 Assurance | critical nodes have owners/tests; P0/P1 evidence must PASS | assurance tests |
| G13 Compiler | tasks/checkpoints are complete and acyclic | compiler tests |
| G14 COS | L0–L19 all explicit; unused dimension marked N/A/deferred | registry tests |
| G15 Recovery | generated bundle has manifest and source digests | compiler integration |
| G16 Agent death | foundation simulation emits complete recovery fields | build artifact; physical drill pending |
| G17 Loop guard | repeated create/external mutation suppresses duplicate and reaches STUCK_LOOP | regression test |
| G18 Public boundary | no operational binaries, credentials or PII | existing repo guard |
| G19 Outbound | V2 build cannot authorize outbound | manifest + invariant |
| G20 Migration | architecture merge changes no hotel/source/H-ID authority | PR scope + manifest |

## 3. Escaped-bug corpus

### BUG-V2-001 — repeated issue-create mutation

```text
Observed bug
→ tool-selection loop invoked create_issue repeatedly
Root cause
→ irreversible mutation lacked durable idempotency preflight and per-strategy budget
Broken invariant
→ one semantic object must map to at most one successful irreversible create
Why process missed it
→ procedural instruction existed but no kernel-level suppressor
Permanent fix
→ MutationLoopGuard + idempotency key + max identical strategy attempts
Regression tests
→ duplicate successful create suppressed
→ placeholder key rejected
→ third repeated no-progress strategy forces change; later attempt STUCK_LOOP
Adjacent family
→ duplicate PR, Drive file, calendar event, message send, external application
```

### BUG-V2-002 — structurally valid but semantically wrong alias

```text
Root cause
→ FK/PK checks did not prove real-world identity equivalence
Invariant
→ alias and target require stable semantic identity evidence
Permanent coverage
→ ASR-1.0 remains independent of V2 graph validity
Adjacent family
→ wrong source record mapped to valid H-ID; graph edge points to valid but wrong node
```

### BUG-V2-003 — canary count presented as authority

```text
Root cause
→ physical validity was conflated with cross-plane promotion
Invariant
→ authority ceiling + complete WOP promotion receipts
Adjacent family
→ CI artifact, ContextPack or graph projection treated as live state
```

### BUG-V2-004 — page position treated as source identity

```text
Root cause
→ cache/locale epochs reorder directory pages
Invariant
→ frozen source-record key; page is observation metadata only
Adjacent family
→ array offset, spreadsheet row or pagination token used as entity identity
```

## 4. Adversarial campaigns

### Correctness

- duplicate event ID;
- valid hash with wrong predecessor;
- altered event payload;
- causation references a future/missing event;
- duplicate node/edge/hyperedge;
- missing endpoint or participant;
- hard dependency cycle;
- invalid temporal interval;
- non-finite JSON value;
- stale ContextPack;
- graph digest mismatch;
- result state SKIPPED/CANCELLED/NOT_RUN mislabeled PASS.

### Security

- secret in key name;
- secret token embedded in prose;
- provider payload containing prompt instructions;
- path traversal in artifact target;
- `file://` or credential-bearing URL;
- shell metacharacters in source fields;
- PII copied to public graph;
- authority ceiling escalated in event payload;
- duplicate external action after retry;
- stale fencing token;
- issue/PR comment poisoning.

### Coordination/distributed semantics

- agent dies with active claim;
- lease expires during work;
- successor takeover;
- old writer resumes;
- two overlapping writers;
- two non-overlapping writers;
- delayed event arrives after projection revision;
- event replay after restart;
- main moves after CI;
- ContextPack assembled from mixed revisions.

### Product

- architecture passes while CRM progress stops;
- graph density rewarded instead of terminal source mapping;
- checkpoint closes on count alone;
- test name overclaims physical runtime qualification;
- automation loops create administrative work rather than reduce bottleneck.

## 5. Ranked gap/risk matrix

Priority formula:

```text
Impact × Probability × BlastRadius × StrategicImportance ÷ Cost
```

P0/P1 receive hard overrides.

| Gap | Sev | Probability | Blast | Detection | Mitigation | Target fix | Owner | Test/evidence | Phase |
|---|---:|---:|---:|---|---|---|---|---|---|
| Projection becomes hidden authority | P0 | 2 | 5 | authority manifest/gate | authority ceiling | retain cross-plane promotion gate | Authority Engine | TEST-V2-AUTHORITY | Foundation |
| Stale writer after takeover | P0 | 3 | 5 | fencing assertion | lease/token | physical concurrent writer drill | Agentic Architect | TEST-V2-FENCING | CP9 |
| Repeated irreversible create loop | P1 | 3 | 3 | mutation ledger | idempotency + budget | integrate guard into tool gateway | Wave Engine | TEST-V2-LOOP-GUARD | CP9 |
| Stale ContextPack | P1 | 4 | 4 | SHA/watermark/revision | freshness rejection | use in all agent bootstraps | Memory Engineer | TEST-V2-CONTEXT | CP13 |
| Graph/state drift | P1 | 3 | 5 | digest reconciliation | rebuild fail-closed | shadow parity on live CRM path | Graph Engineer | E2E parity artifact | CP11/13 |
| Legacy history incomplete | P2 | 4 | 3 | historical graph gaps | `HISTORICAL_UNKNOWN` | evidence-bounded backfill | Migration Architect | historical audit | CP2/13 |
| Recovery SLO unqualified | P2 | 3 | 4 | timed drill | deterministic bundle | three independent death drills | Recovery Engineer | duration evidence | CP7/12 |
| Provider identifier changes | P2 | 3 | 4 | source diff | stable source evidence | empirical drift policy | Data Architect | provider diff corpus | CP12 |
| JSONL growth/compaction | P3 | 2 | 2 | file size/replay time | snapshots | trigger-based compaction | Reliability | benchmark | Deferred |
| Specialized graph query performance | P3 | 2 | 2 | query benchmark | projections | graph DB trigger only if SLO breached | Performance | benchmark | Deferred |

Foundation target: open P0 = 0, open P1 = 0. P2/P3 remain explicit and checkpoint-owned.

## 6. COS 20D adversarial questions

- L0: Which node is overloaded or orphaned?
- L1: Can every task reach evidence and a checkpoint?
- L2: Which transition is impossible or missing?
- L3: What is the articulation point and transitive blast radius?
- L4: Which function/module violates its boundary?
- L5: Which fallback escalates authority or turns fail-open?
- L6: Where can provenance disappear?
- L7: Which computation is repeated or unbounded?
- L8: Which fact/decision lacks evidence?
- L9: Which term is overloaded or duplicated?
- L10: Could similarity be mistaken for identity authority?
- L11: Can a zero-context agent retrieve why, state, evidence and NEXT?
- L12: What memory expires, invalidates or becomes historical?
- L13: Which agents collide, idle or retain stale claims?
- L14: Which tool is unavailable, untrusted or overprivileged?
- L15: Which workflow lacks retry, compensation or idempotency?
- L16: Is network infrastructure actually needed? Current answer: no.
- L17: Does work increase expected viable-offer economics?
- L18: Where can PII escape purpose/retention boundaries?
- L19: Can a vanity metric be gamed while North Star remains zero?

## 7. Foundation acceptance

The V2 foundation may merge only when:

```text
kernel imports and compiles
all V2 tests PASS
compiler emits 20 dimension projections
system graph has no integrity errors or hard dependency cycles
critical owner gaps = 0
critical test gaps = 0
invariant failures = 0
open P0 = 0
open P1 = 0
build manifest binds exact commit SHA
operational_authority_mutated = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
repo public-boundary guard PASS
```

This is not CP14 Production Authority. Physical recovery, agent-death, concurrency, security, E2E, empirical qualification and migration remain explicit checkpoints.
