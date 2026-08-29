# GRAPH REFACTOR V2 — ADVERSARIAL GAUNTLET

Version: **GRV2-GAUNTLET-1.0**  
Status: **FOUNDATION ASSURANCE CONTRACT**  
Owner: Adversarial Reviewer / QA Governance / CISO  
Last updated: 2026-08-30

## Result vocabulary

```text
PASS
FAIL
SKIPPED
CANCELLED
NOT_RUN
NOT_APPLICABLE
```

No state may be collapsed into PASS.

## Foundation gates

| Gate | Assertion | Foundation evidence |
|---|---|---|
| G00 North Star | Architecture cannot replace offer outcome with graph/CI metrics | architecture + L19 projection |
| G01 Authority | V2 artifact cannot advance domain authority | manifest hard fields |
| G02 Identity | node/event/session/claim IDs unique and validated | kernel tests |
| G03 Event | duplicate, altered, out-of-order or broken-chain event rejected | ledger tests |
| G04 Graph | missing endpoint, duplicate ID and hard dependency cycle rejected | graph tests |
| G05 Hyperedge | at least two distinct participants and explicit roles | graph tests |
| G06 Session | globally unique lifecycle; closed session cannot mutate | coordination tests |
| G07 Claim | overlapping write collides; non-overlap remains parallel | claim tests |
| G08 Lease | expiry/takeover issues newer fencing token | lease tests |
| G09 Fence | stale holder rejected after takeover | fencing tests |
| G10 Context | moved SHA/watermark/projection invalidates pack | ContextPack tests |
| G11 Secret | public ContextPack redacts key/value patterns | security tests |
| G12 Assurance | critical nodes owned/tested; P0/P1 evidence PASS | assurance tests |
| G13 Compiler | tasks/checkpoints complete and acyclic | compiler tests |
| G14 COS | L0–L19 explicit; unused dimension N/A/deferred | registry tests |
| G15 Recovery | bundle has manifest and source digests | integration test |
| G16 Agent death | simulation packet contains required recovery fields | build artifact; physical drill pending |
| G17 Loop guard | duplicate create suppressed; repeated strategy terminates | regression test |
| G18 Public boundary | no operational binaries, credentials or PII | repository guard |
| G19 Outbound | V2 build cannot authorize outbound | manifest/invariant |
| G20 Migration | architecture merge changes no operational authority | PR scope/manifest |

## Escaped-bug corpus

### BUG-V2-001 — repeated issue-create mutation

```text
Observed bug
→ tool-selection loop invoked create_issue repeatedly
Root cause
→ irreversible mutation lacked durable idempotency preflight and strategy budget
Broken invariant
→ one semantic object maps to at most one successful irreversible create
Why process missed it
→ procedural instruction existed without kernel-level suppressor
Permanent fix
→ MutationLoopGuard + idempotency key + max identical attempts
Regression tests
→ duplicate successful create suppressed
→ placeholder key rejected
→ repeated no-progress strategy changes then enters STUCK_LOOP
Adjacent family
→ duplicate PR, Drive file, calendar event, message or application
```

### BUG-V2-002 — structurally valid, semantically wrong alias

```text
Root cause
→ PK/FK validity did not prove real-world identity equivalence
Invariant
→ alias/target require stable semantic identity evidence
Coverage
→ ASR-1.0 remains independent of graph validity
Adjacent family
→ wrong source record mapped to a valid but unrelated H-ID
```

### BUG-V2-003 — canary presented as authority

```text
Root cause
→ physical validity conflated with cross-plane promotion
Invariant
→ authority ceiling + complete WOP receipts
Adjacent family
→ CI artifact, ContextPack or projection treated as live state
```

### BUG-V2-004 — page position used as identity

```text
Root cause
→ cache/locale epochs reorder directory pages
Invariant
→ frozen source-record key; page is observation metadata only
Adjacent family
→ array offset or spreadsheet row used as entity identity
```

## Adversarial campaigns

### Correctness

- duplicate event ID;
- valid hash with wrong predecessor;
- altered payload;
- future/missing causation;
- duplicate/missing graph element;
- hard dependency cycle;
- invalid temporal interval;
- non-finite JSON value;
- stale ContextPack;
- graph digest mismatch;
- `SKIPPED/CANCELLED/NOT_RUN` mislabeled PASS.

### Security

- secret in key name or prose;
- provider prompt injection;
- path traversal;
- `file://` or credential-bearing URL;
- shell metacharacters in source values;
- PII copied into public graph;
- event authority escalation;
- duplicate irreversible action after retry;
- stale fencing token;
- issue/PR comment poisoning.

### Coordination/distributed semantics

- agent dies with active claim;
- lease expires during work;
- successor takeover;
- old writer resumes;
- overlapping and non-overlapping writers;
- delayed event after projection revision;
- event replay after restart;
- main changes after CI;
- ContextPack assembled from mixed revisions.

### Product

- architecture passes while CRM progress stops;
- graph density rewarded instead of terminal mapping;
- checkpoint closes on count alone;
- test name overclaims runtime qualification;
- automation creates administrative work rather than reducing bottleneck.

## Ranked gap/risk matrix

Priority uses:

```text
Impact × Probability × BlastRadius × StrategicImportance ÷ Cost
```

P0/P1 receive hard overrides.

| Gap | Sev | Probability | Blast | Detection | Mitigation | Target fix | Owner | Evidence | Phase |
|---|---:|---:|---:|---|---|---|---|---|---|
| Projection becomes hidden authority | P0 | 2 | 5 | authority gate | ceiling | retain cross-plane promotion gate | Authority Engine | TEST-V2-AUTHORITY | Foundation |
| Stale writer after takeover | P0 | 3 | 5 | fence assertion | lease/token | physical writer drill | Wave Engine | TEST-V2-FENCING | CP9 |
| Repeated irreversible create loop | P1 | 3 | 3 | mutation ledger | idempotency/budget | integrate into tool gateway | Wave Engine | TEST-V2-LOOP-GUARD | CP9 |
| Stale ContextPack | P1 | 4 | 4 | SHA/watermark | reject stale | all bootstraps use pack | Meta Graph | TEST-V2-CONTEXT | CP13 |
| Graph/state drift | P1 | 3 | 5 | digest reconciliation | rebuild fail-closed | live CRM shadow parity | Graph Engine | E2E artifact | CP11/13 |
| Legacy history incomplete | P2 | 4 | 3 | historical gaps | `HISTORICAL_UNKNOWN` | evidence-bounded backfill | Migration | historical audit | CP2/13 |
| Recovery SLO unqualified | P2 | 3 | 4 | timed drill | deterministic bundle | three independent drills | Recovery | duration evidence | CP7/12 |
| Provider ID changes | P2 | 3 | 4 | source diff | stable source evidence | drift policy | Data | diff corpus | CP12 |
| JSONL growth | P3 | 2 | 2 | size/replay | snapshots | trigger-based compaction | Reliability | benchmark | Deferred |
| Graph query performance | P3 | 2 | 2 | benchmark | projections | graph DB only on breach | Performance | benchmark | Deferred |

Foundation target: open P0=0 and open P1=0. P2/P3 remain explicit and checkpoint-owned.

## COS 20D attack questions

- L0: Which node is overloaded or orphaned?
- L1: Can every task reach evidence/checkpoint?
- L2: Which transition is impossible or missing?
- L3: What is the articulation point/blast radius?
- L4: Which function violates a boundary?
- L5: Which fallback becomes fail-open?
- L6: Where can provenance disappear?
- L7: Which computation is repeated/unbounded?
- L8: Which fact/decision lacks evidence?
- L9: Which term collides semantically?
- L10: Could similarity become identity authority?
- L11: Can zero-context retrieval recover why/state/evidence/NEXT?
- L12: What memory expires or becomes historical?
- L13: Which agents collide or retain stale claims?
- L14: Which tool is unavailable, untrusted or overprivileged?
- L15: Which workflow lacks retry/compensation/idempotency?
- L16: Is network infrastructure needed? Current answer: no.
- L17: Does this increase expected viable-offer economics?
- L18: Where can PII escape purpose/retention?
- L19: Can a vanity metric be gamed while North Star stays zero?

## Foundation acceptance

```text
kernel imports/compiles
all V2 tests PASS
compiler emits 20 projections
system graph has no integrity error/cycle
critical owner gaps = 0
critical test gaps = 0
invariant failures = 0
open P0 = 0
open P1 = 0
build manifest binds exact SHA
operational_authority_mutated = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
public-repository guard PASS
```

This is not CP14. Physical recovery, death, concurrency, security, E2E, qualification and migration remain checkpoint-gated.
