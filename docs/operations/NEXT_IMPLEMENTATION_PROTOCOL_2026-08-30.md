# NEXT IMPLEMENTATION PROTOCOL — 2026-08-30

**Authority:** execution protocol; not hotel operational authority  
**Scope:** CRM universe closure → bounded authority promotion → full Intelligence/L9 program  
**Live basis:** main `5fb3e30bbbfa496126769fa57ac378c48e4b0fb9`, E4 authority, snapshot `HS-MEMBER-DE-33206402141`  
**Verify live truth before every mutation.**

## 1. North Star

The program optimizes for a real, truthful, legal and economically viable Swiss employment offer accepted by Roberto. CRM completeness, canonical counts, enrichment and outreach readiness are supporting constraints.

## 2. Live entry state

```text
active canonical                         690
next H-ID                                H-0691 UNALLOCATED
source records                           2061
ECV exact-current                        1438/1438
terminal source mappings                  658
RECONCILE_REQUIRED                       1403
reverse authority gaps                     34
>=0.60 identity queue                    20/20 reviewed
0.50-0.599999 effective queue            10/46 reviewed
0.50-0.599999 remaining                     36
NEW_CANONICAL preauth-ready                 29
relationship/granularity unresolved          2
CRM_UNIVERSE_COMPLETE                    FALSE
OUTBOUND                                 CLOSED
send_allowed                                  0
```

## 3. Hard laws

1. No H-ID allocation or reservation from staging/review.
2. Similarity only reduces review space; it never proves identity.
3. `NEW_CANONICAL` remains `RECONCILE_REQUIRED` until an authority transaction.
4. Same-property / alias / component relations require independent evidence.
5. Every source record must end terminally accounted before CRM universe completion.
6. Authority promotion is DB-first and cross-plane; Sheets-first is forbidden.
7. Outbound remains closed until CRM universe, candidate, evidence/freshness, channel, suppression/idempotency and explicit-authorization gates all pass independently.
8. Active claims/fencing are checked before writing overlapping state scopes.

## 4. Critical path

```text
P0 LIVE BARRIER
  ↓
P1 CLOSE 0.50–0.599999 IDENTITY BAND (36)
  ↓
P2 CLOSE LOWER-SIMILARITY REVIEW TAIL (49)
  ↓
P3 RECONCILE RELATIONSHIP/GRANULARITY + RAGR 34
  ↓
P4 FREEZE PREAUTHORITY SOURCE-RESOLUTION PLANE
  ↓
P5 AUTHORITY CANARY 10
  ↓
P6 BOUNDED AUTHORITY SCALE 25 → 50
  ↓
P7 2061/2061 TERMINAL + CRM_UNIVERSE_COMPLETE
  ↓
P8 CANONICAL→INTELLIGENCE/GRAPH EXACT PARITY
  ↓
P9 L4→L9 FACTORY
  ↓
P10 CANDIDATE/OUTBOUND GATES
  ↓
APPLICATION → RESPONSE → INTERVIEW → OFFER → FINANCIAL MODEL → ACCEPTANCE
```

## 5. Phase P1 — close the remaining 36 records

### Workset derivation

Authoritative review workset is:

`SRET_SIMILARITY_RISK_QUEUE_050_059` minus:
- already-terminal `FIVE Zürich - EAST WING`;
- source keys already typed by `SRR_CURRENT_IDENTITY_EVIDENCE_500599_WAVE1`.

Expected cardinality: **36**.

### Batch topology

Use deterministic source-key order and four bounded review waves:

```text
P1-B01  10 records
P1-B02  10 records
P1-B03  10 records
P1-B04   6 records
```

Do not reorder by desired outcome. Prioritize only when a documented collision-risk rule requires it.

### Per-record state machine

```text
EVIDENCE_CAPTURED
  ↓
COMPARE source identity against every suggested canonical comparator
  ├─ independently same property → MATCH_EXISTING / ALIAS_EXISTING / typed relationship
  ├─ independently distinct      → NEW_CANONICAL (preauthority only)
  └─ insufficient/conflicting    → UNRESOLVED
```

### Evidence minimum

For a distinctness decision require current source identity evidence plus current comparator evidence sufficient to distinguish legal/property identity. Provider page alone cannot auto-bind. Domain/name similarity alone cannot decide.

### Batch DoD

- exact input keys and SHA persisted;
- every input gets exactly one typed review result;
- no source key appears twice;
- no H-ID allocation/reservation;
- terminal mapping delta only for evidence-backed existing/alias relations;
- `NEW_CANONICAL` leaves mapping state `RECONCILE_REQUIRED`;
- conservation arithmetic passes;
- repo guard + contract guard + unit tests pass;
- state/handoff updated only from executed evidence;
- outbound locks unchanged.

## 6. Phase P2 — lower-similarity 49

Do not process as one undifferentiated batch. Partition by collision risk:

1. same city + same operator/brand;
2. same city + lexical overlap;
3. cross-city same brand;
4. low-overlap independent properties.

Run 10-record canaries first. Similarity remains a scheduler hint only.

Exit: every one of the 49 has a typed evidence-review state; unresolved cases have explicit blocker/review owner.

## 7. Phase P3 — relationship/granularity + reverse gaps

Two current relationship/granularity cases and 34 reverse authority gaps are independent gates.

For each reverse gap classify exactly one:

```text
IN_SCOPE_NO_SOURCE_MATCH
OUT_OF_SNAPSHOT_SCOPE
SUPERSEDED/RENAMED WITH EVIDENCE
COMPONENT/GROUP GRANULARITY
DATA DEFECT
UNRESOLVED
```

No canonical deletion/deactivation occurs from review alone.

Exit: reverse-gap count either zero or every residual gap is an evidence-backed exclusion/scope decision accepted by the authority contract.

## 8. Phase P4 — preauthority freeze

Produce a single immutable resolution manifest over all 2061 source records.

Required conservation:

```text
ACTIVE/EXISTING TERMINAL
+ ALIAS TERMINAL
+ EXCLUDED_WITH_REASON
+ NEW_CANONICAL AUTHORITY WORKSET
+ explicit unresolved blockers
= 2061
```

Authority canary cannot begin while any identity decision needed for the canary is unresolved.

## 9. Phase P5 — authority canary

Select 10 `NEW_CANONICAL` proposals using deterministic ordering after exclusion/relationship review.

Transaction:

```text
PROPOSE
→ STAGE
→ CANARY
→ validate evidence/current scope
→ allocate H-ID inside transaction only
→ DB commit
→ HOTELS_MASTER PK mirror
→ Intelligence admission
→ Operational Graph admission
→ metrics/checkpoints
→ integrity/FK/orphan/parity checks
→ restore/replay
→ COMMIT or ROLLBACK
```

Exit requires exact DB↔Sheets↔Intelligence↔Graph parity and replay equivalence.

## 10. Phase P6 — bounded scale

- default batch 25;
- after three consecutive clean batches + restore equivalence, eligible for 50;
- conflict-heavy batches remain 10;
- stop immediately on conservation, ID, FK, mirror, graph, restore or authority-revision failure.

## 11. Phase P7 — CRM universe completion

`CRM_UNIVERSE_COMPLETE=TRUE` only when one frozen snapshot is fully terminally accounted and all active canonical planes share the same denominator/lineage.

No numeric approximation, max-H-ID inference or historical denominator may satisfy this gate.

## 12. Phase P8/P9 — Intelligence and L9 factory

For every canonical entity:

```text
L1 identity
→ L4 vacancy/housing/people/channels
→ L5 social/digital/creative/tech audits
→ L6 lane opportunities + 0–100 heuristic scores
→ L7 evidence-backed personalized proposition
→ L8 channel-policy-aware message bundle
→ L9 QA + provenance + TTL + suppression + idempotency
```

Unknowns remain typed; `UNKNOWN_AFTER_SEARCH` requires Search Proof.

## 13. Concurrency protocol

Before every wave:

1. reread live main;
2. read `docs/state/v2/active-claims.json`;
3. reject overlapping active resource/semantic scopes unless explicitly shared;
4. require fencing token greater than superseded writer for takeover;
5. create unique session/correlation/idempotency identities;
6. pin base ancestry and relevant-scope revision;
7. execute only within authority ceiling.

ContextPack 1.1 is acceleration, not authority. Unrelated descendant commits are allowed only when base ancestry remains valid and relevant scopes did not drift.

## 14. Test matrix

Every material wave runs, as applicable:

- repo guard;
- stable contract guard;
- V2 coordination guard;
- unit tests;
- source-key conservation;
- duplicate/ambiguous identity tests;
- H-ID reservation/allocation safety locks;
- SQLite integrity/FK;
- DB↔Sheets parity;
- Graph orphan/endpoints;
- Intelligence parity;
- replay/idempotency;
- restore equivalence;
- outbound/suppression locks.

## 15. Stop conditions

`SUCCESS`: checkpoint DoD objectively passes.  
`BLOCKED`: external evidence/provider/tool dependency prevents justified progress.  
`AUTHORITY_BLOCK`: irreversible mutation lacks authority.  
`STUCK_LOOP`: same failed strategy attempted three times; change strategy.  

Never stop because a plan exists.

## 16. Immediate executable frontier

1. Materialize the exact remaining-36 workset deterministically.
2. Split 10/10/10/6 with stable batch IDs and hashes.
3. Reuse captured PIE evidence where available; obtain independent comparator evidence where required.
4. Execute P1-B01 and persist typed decisions.
5. Run gauntlet and update state only if the evidence-backed result passes.
6. Continue B02/B03/B04 without allocating H-IDs.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
