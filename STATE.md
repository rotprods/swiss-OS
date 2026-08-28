# STATE — LIVE HANDOFF POINTER

Latest Meta Execution reconciliation: **2026-08-28T20:25:00+02:00**.  
Latest reconstructed GitHub `main`: **`60606dc36bf88883d6a2eb9e1c7903e03dc29bc8`**.  
Latest physically verified constrained parent: **`OPERATIONAL_DB_SHADOW_MANIFEST_V13`**.  
Latest semantic-authority gate: **ASR-1.0 / issue #89 = RECONCILE_REQUIRED**.  
Latest deterministic recovery capability: **ARR-1.0**.  
Latest exact repair evidence: **ASR_REPAIR_CANARY_2026-08-28_V1 + issue-89 public-safe repair/write-set plans**.

## 1. Authority posture — fail closed

The V13 parent remains the latest physically verified synchronized recovery parent, but its four persisted H-ID alias/supersession edges are semantically corrupt. Structural SQLite integrity is not enough to make the prior active denominator safe.

```text
entity epoch                    HS_ENTITY_EPOCH_2026-08-25_E4
constrained recovery parent     OPERATIONAL_DB_SHADOW_MANIFEST_V13
constrained parent SHA-256      0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
physical HOTELS rows            690
persisted H-ID alias edges        4
alias semantics                 RECONCILE_REQUIRED
prior reported active           686 — NOT SAFE TO ADVANCE FROM
safe current active denominator RECONCILE_REQUIRED / no numeric promotion claim
canonical H-ID allocation       FORBIDDEN
CRM authority promotion         FORBIDDEN
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Do **not** infer an authoritative `690 active` merely by removing four alias edges. A repaired DB or Sheets canary is not authority until DB → HOTELS_MASTER → Intelligence → Operational Graph → observability/recovery reconcile atomically and ASR-1.0 returns `EXACT`.

## 2. P0 #89 — semantic alias identity corruption

Persisted invalid edges:

```text
H-0610 Hôtel Alpe Fleurie — Villars-sur-Ollon
→ H-0656 Hotel Murtenhof & Krone — Murten

H-0624 Hôtel Le Mont Paisible — Crans-Montana
→ H-0639 Hotel Alpbach — Meiringen

H-0629 Stiftung Lilienberg Unternehmerforum — Ermatingen
→ H-0638 Jugendherberge Seelisberg — Seelisberg

H-0630 Strandhotel Iseltwald — Iseltwald
→ H-0640 Hotel Central Luzern — Luzern
```

`ENTITY_RESOLUTION:ER-CP0650-001..004` correctly identifies the target names/cities as duplicate discovery candidates anti-joinable to existing canonical targets, but the notes incorrectly attached unrelated physical H-IDs as superseded rows.

Historical HOTELS_MASTER revision `464` (`2026-08-23T18:40:27.970Z`) proves all four source-side H-IDs were distinct `CANONICAL_CURRENT_RECONCILED` hotels before the supersession run. It also proves their Intelligence seed state was `L1 / CANONICAL_INDEXED_RECONCILE_SEED` and their HOTEL→INTEL edges existed as ordinary `HAS_INTELLIGENCE` relations.

Root class:

```text
candidate / H-ID lineage drift
→ duplicate discovery candidate correctly resolves to existing target
→ unrelated physical H-ID incorrectly receives supersession mutation
```

Issue: `#89`.

## 3. ASR-1.0 semantic gate

ASR-1.0 merged previously in PR `#90` as:

```text
377744d9860e89861f0c80d045d774dcb58eb03b
```

Contract: `docs/operations/ALIAS_SEMANTIC_RECONCILIATION.md`.  
Validator: `src/swiss_os/alias_semantics.py`.

ASR requires every persisted alias edge to prove semantic identity, not merely PK/FK validity. It fails closed on missing/ambiguous evidence, mismatched physical identity, target mismatch, self-aliases or unproved real-world equivalence.

## 4. ARR-1.0 deterministic repair replay

PR `#92` passed repository guards, stable-contract guard, unit tests and manifest canary, then merged as:

```text
60606dc36bf88883d6a2eb9e1c7903e03dc29bc8
```

Contract: `docs/operations/ALIAS_REPAIR_REPLAY.md`.  
Executable: `src/swiss_os/alias_repair.py`.

ARR-1.0 provides a portable copy-on-write repair path with:

```text
exact parent SHA lock
+ expected alias identity
+ expected target identity
+ expected persisted target/state
+ mutation cardinality gates
+ integrity/FK pre/post checks
+ atomic temp → replace publication
+ no overwrite / no in-place mutation
+ idempotent replay
```

ARR deliberately does **not** infer the post-repair active denominator:

```text
candidate_active_canonical = null
active_denominator_state   = RECONCILE_REQUIRED_CROSS_PLANE
authority_advanced         = false
h_id_allocations           = 0
outbound_opened            = false
send_allowed               = 0
```

Public-safe deterministic plan: `docs/state/ISSUE_89_ASR_REPAIR_PLAN.json`.  
Public-safe cross-plane plan: `docs/state/ISSUE_89_CROSS_PLANE_WRITESET.json`.

## 5. Exact V13 replay evidence — non-authoritative

V13 was reread from Drive by exact file ID and reverified in this activation:

```text
Drive file ID                 1rIL6x_bmBoCbxVSAGFvdjoKnUqSX3YnT
SHA-256                       0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
SQLite integrity_check       ok
FK violations                  0
physical rows                690
invalid alias rows             4
```

Deterministic repair of those exact bytes reproduces the prior canary artifact exactly:

```text
repaired SHA-256              70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
physical rows                 690
hotel_aliases after repair      0
superseded rows after repair    0
SQLite integrity_check        ok
FK violations                   0
idempotency replay            PASS / 0 additional logical mutations
active denominator            NOT INFERRED
```

Logical SQLite differences remain exactly four state restorations plus four invalid `hotel_aliases` removals. No H-ID is created, deleted, reused or renumbered.

## 6. Live HOTELS_MASTER recovery preflight

The native Google Sheet is reachable and writable:

```text
spreadsheet ID                 1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w
latest observed revision       488
```

A full rollback copy was created **before any live mutation**:

```text
HOTELS_MASTER_ROLLBACK_PRE_ASR_2026-08-28_2011
Drive ID 1bu1SjxxG4fF4yx7H2rshOiw-tnJZMcHxIL3S8ipyQKk
```

No live repair mutation has been performed.

Exact affected live surfaces have been reconstructed by stable keys:

```text
HOTELS_V2
  H-0610 / H-0624 / H-0629 / H-0630

HOTEL_INTELLIGENCE_V1
  H-0610 / H-0624 / H-0629 / H-0630

GRAPH_NODES_V2
  HOTEL:<four IDs>
  INTEL:<four IDs>

GRAPH_EDGES_V2
  four invalid EDGE:ALIAS:* relations
  four HOTEL→INTEL relations currently marked SUPERSEDED_ALIAS

ENTITY_RESOLUTION
  ER-CP0650-001..004 retained as research anti-join evidence

STATE_TRANSITIONS
  TR-20260825-H0610-SUPERSEDE
  TR-20260825-H0624-SUPERSEDE
  TR-20260825-H0629-SUPERSEDE
  TR-20260825-H0630-SUPERSEDE
  preserved; repair requires append-only corrective transitions
```

Drive durable preflight: `ASR_ATOMIC_RECOVERY_PREFLIGHT_2026-08-28_V2`, Doc ID `13G_a1kj3uhu_XmH5xK253d0DBPeUiLl-dwkOiHHdLZU`.

## 7. Current atomic-promotion blocker

This runtime can read the exact V13 binary and construct the exact repaired SQLite, but the Google Drive connector rejects egress of the newly generated SQLite with:

```text
BLOCKED_FILE_REFERENCE
```

Therefore the system MUST NOT mutate HOTELS_V2/Intelligence/Graph alone. That would create a forbidden cross-plane partial authority state.

Current durable strategy:

```text
immutable V13 Drive parent
+ ARR-1.0 deterministic replay
+ exact parent SHA
+ exact expected repaired SHA observation
+ public-safe repair plan
+ public-safe cross-plane write set
+ HOTELS_MASTER rollback copy
+ Drive preflight report
```

A persistent operator environment that can write the repaired SQLite can reproduce the exact repair without relying on chat context.

## 8. Required bounded recovery transaction

Before authority can move, one recovery wave must execute and reconcile:

```text
fresh Git ancestry + V13 parent check
→ durable ARR repaired constrained DB
→ resolve all Sheet rows again by PK/key
→ HOTELS_V2 four state restorations
→ HOTEL_INTELLIGENCE_V1 restore L1 / CANONICAL_INDEXED_RECONCILE_SEED without inventing enrichment
→ GRAPH_NODES_V2 remove invalid supersession state
→ GRAPH_EDGES_V2 remove invalid ALIASES_TO relations
→ restore four ordinary HAS_INTELLIGENCE edge semantics
→ preserve ER records but remove their interpretation as physical supersession evidence
→ append four corrective STATE_TRANSITIONS
→ derive checkpoint/active denominator only after data-plane reconciliation
→ scheduler / metrics / health / SLO / invariant reconciliation
→ ASR-1.0 EXACT
→ DB ↔ Sheets ↔ Intelligence ↔ Graph exact
→ restore/replay/idempotency gauntlet
→ recovery persistence
```

Any parent/revision/key drift switches the wave back to `RECOVERY_RECONCILE`; no force-write is permitted.

## 9. Source-universe work remains valid but lower priority than #89

The pre-authority CRM pipeline on `main` remains available:

```text
HSLCA-R1.0 / MDC-1.1
→ PCF-1.0 when provider aggregate count is absent
→ MDM
→ CMI
→ CWP
→ ECV
→ SMC
→ SRR-1.1
```

A prior live directory canary acquired `172/172` pages and `2061` unique detail URLs but was diagnostic because MDC-1.0 reversed city/name fields; MDC-1.1 fixed that parser. `discover.swiss` remains unavailable without `DISCOVER_SWISS_SUBSCRIPTION_KEY`.

Open PR `#88` remains unmerged until its required live-source qualification passes. Repository CI alone is insufficient.

Read-only source-universe research may continue while #89 blocks authority/H-ID allocation, but it may not bypass the semantic-authority P0.

## 10. Runtime capability

```text
GitHub read/write/CI                         AVAILABLE
web research                                 AVAILABLE
authenticated Drive read                     AVAILABLE
Drive/Docs durable writes                    AVAILABLE
native HOTELS_MASTER in-place Sheets write   AVAILABLE
V13 raw parent recovery                      AVAILABLE / SHA verified
repaired SQLite local construction           AVAILABLE / deterministic
repaired SQLite connector egress             BLOCKED_FILE_REFERENCE
Library durable write                        not proven in this activation
```

Do not claim Library synchronization unless a real write actuator succeeds.

## 11. Current MEP route

Highest-value route:

```text
ASR_REPAIR_ARTIFACT_EGRESS_OR_PERSISTENT_OPERATOR_REPLAY
```

If durable repaired-DB persistence becomes available:

```text
/wave recover
→ reread main/V13/Sheets revision
→ ARR replay
→ atomic cross-plane write set
→ ASR EXACT
→ gauntlet
→ authority reconciliation
```

If that capability remains unavailable, continue safe work that reduces future execution risk:

```text
repair-plan validation
→ cross-plane precondition validation
→ historical-revision proof
→ source-universe read-only qualification
→ QA/recovery engineering
```

Do not partially repair live mirrors.

## 12. Durable NEXT

Canonical machine-readable pointer: `docs/state/NEXT.json`.

Permissions remain:

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
```

## 13. North-star continuation

After #89 is atomically reconciled:

```text
resume fresh coherent HSLCA capture
→ provider count OR strict PCF materialized denominator
→ MDM coverage_complete=true
→ discover.swiss / SSR when credential exists
→ CMI → CWP → ECV → SMC → SRR
→ all frozen source records terminally mapped
→ unmapped = 0
→ RECONCILE_REQUIRED = 0
→ authoritative DB/Sheets/Intelligence/Graph reconciliation
→ CRM_UNIVERSE_COMPLETE = TRUE only when every independent gate passes
```

`OUTBOUND` remains separately CLOSED and still requires explicit authorization even after CRM completion.
