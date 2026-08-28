# STATE — LIVE HANDOFF POINTER

Latest Meta Execution reconciliation: **2026-08-28T21:53:40+02:00**.  
Reconstructed GitHub parent before this state wave: **`1676bb22b5407f590de7fe47cd1e369ec5a7d7b0`**.  
Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**.  
Authority parent: **issue-89 CCP/ARR materializable repaired constrained parent**.  
Latest live HOTELS_MASTER revision after reconciliation: **497**.

## 1. Authority — issue #89 recovered

The four persisted alias/supersession edges identified by issue #89 were semantic row/H-ID drift, not duplicate physical hotel identities. Recovery was performed by stable H-ID/PK and reconciled across constrained DB materialization, HOTELS_MASTER, Intelligence, Operational Graph and control-plane surfaces.

```text
entity epoch                    HS_ENTITY_EPOCH_2026-08-25_E4
immutable constrained base      OPERATIONAL_DB_SHADOW_MANIFEST_V13
base SHA-256                    0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
repair protocol                 ARR-1.0
constrained-parent protocol     CCP-1.0
semantic alias gate             ASR-1.0 = EXACT
repaired materialization SHA    70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
HOTEL_INTELLIGENCE_V1           690 / 690
Graph HOTEL nodes               690 / 690
Graph INTEL nodes               690 / 690
HAS_INTELLIGENCE edges          690 / 690
L4                              105 / 690
CP-0750                         690 / 750
next physical ID                H-0691
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

No new H-ID was allocated by the repair. The four affected physical identities were restored to their prior canonical state and their historical Intelligence depth only: `L1 / CANONICAL_INDEXED_RECONCILE_SEED`. Four corrective `STATE_TRANSITIONS` preserve the bad supersession lineage rather than deleting history.

## 2. Deterministic constrained-parent recovery

The immutable V13 base remains preserved in Drive. `ARR-1.0` deterministically materializes the repaired constrained parent from that exact base and the pinned issue-89 repair plan. The materialization was rerun in this activation and reproduced the precommitted digest exactly:

```text
expected repaired SHA-256       70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
observed repaired SHA-256       70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
SQLite integrity_check          ok
foreign-key violations            0
hotel rows                      690
alias rows                        0
superseded rows                   0
second replay mutations           0
idempotency                     PASS
```

Canonical public-safe recovery artifacts:

- `docs/state/ISSUE_89_ASR_REPAIR_PLAN.json`
- `docs/state/ISSUE_89_CROSS_PLANE_WRITESET.json`
- `docs/state/ISSUE_89_COMPOSITE_CONSTRAINED_PARENT.json`
- `docs/operations/ALIAS_SEMANTIC_RECONCILIATION.md`
- `docs/operations/ALIAS_REPAIR_REPLAY.md`
- `docs/operations/COMPOSITE_CONSTRAINED_PARENT.md`

## 3. HOTELS_MASTER cross-plane transaction

Native Sheets mutation is available and was used only after a fresh rollback copy existed.

```text
HOTELS_MASTER ID                 1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w
pre-wave revision               489
post-reconciliation revision    497
rollback copy ID                1KPaM2gIA3C_CNulDPSI7KRFHIem50Thx-2q4BJXdrgk
rollback title                  HOTELS_MASTER_ROLLBACK_PRE_ASR_RECOVERY_2026-08-28_2137
```

Readback after reconciliation proves:

```text
HOTELS_V2 H-ID rows                         690
HOTELS_V2 SUPERSEDED_DUPLICATE                0
HOTEL_INTELLIGENCE_V1 H-ID rows             690
GRAPH_NODES_V2 HOTEL:H-*                    690
GRAPH_NODES_V2 INTEL:H-*                    690
GRAPH_EDGES_V2 HAS_INTELLIGENCE             690
GRAPH_EDGES_V2 ALIASES_TO                     0
```

Control-plane readback now reports `690` consistently in active E4 rows for `ENGINE_METRICS`, `GOAL_STATE`, `CHECKPOINT_REGISTRY`, `SOURCE_SNAPSHOTS`, `ENGINE_HEALTH`, `SLO_REGISTRY` and `EXECUTION_SCHEDULER_V2`. Historical rows remain immutable history and may still describe the old 686/4-alias state.

Run ledger: `RUN-2026-08-28-2148-ASR-ISSUE89-AUTHORITY-RECOVERY`.  
Decision ledger: `DEC-0102`.  
System issue mirror: `ISS-055 = RESOLVED_ASR_CROSS_PLANE_PASS`; prior `ISS-051` is retained but corrected by issue #89.

## 4. Safety invariants after recovery

Issue #89 authority recovery does **not** complete the CRM source universe and does not authorize outbound.

```text
canonical IDs from staging          FORBIDDEN
cache/canary authority promotion    FORBIDDEN
CRM_UNIVERSE_COMPLETE               FALSE
OUTBOUND                            CLOSED
send_allowed                          0
```

Future alias/supersession writes must pass ASR-1.0 semantic equivalence using stable identity evidence. Row position or candidate ordering is never authority.

## 5. Current CRM-universe frontier

The pre-authority source pipeline remains:

```text
HSLCA-R1.0 / MDC-1.1
→ HPCB-1.0 provenance bridge when needed
→ PCF-1.0 if provider aggregate count is absent
→ MDM
→ CMI
→ CWP
→ ECV
→ SMC
→ SRR-1.1
→ terminal source mappings
```

`discover.swiss` remains unavailable without `DISCOVER_SWISS_SUBSCRIPTION_KEY`, so the current high-value fallback is a fresh coherent HotellerieSuisse member-directory capture. PR #88 contains HPCB/HSLCA→PCF work but is based on stale ancestry and must not be merged as-is. Its live-source acceptance criteria remain useful and should be ported/requalified from fresh `main` if the source path is selected.

Existing read-only evidence work is still non-authoritative: exact-current batches reduce evidence debt but do not reserve H-IDs or advance authority.

## 6. Runtime capability

```text
GitHub read/write/CI                         AVAILABLE
web research                                 AVAILABLE
authenticated Drive read                     AVAILABLE
Drive/Docs durable writes                    AVAILABLE
native HOTELS_MASTER in-place Sheets write   AVAILABLE
V13 raw parent recovery                      AVAILABLE / SHA verified
ARR repaired SQLite local materialization    AVAILABLE / deterministic
Library durable write                        not required for authority claim in this wave
```

The prior repaired-binary egress blocker is no longer an authority blocker because CCP-1.0 defines a durable content-addressed materializable constrained parent, and this activation reproduced its exact expected digest before cross-plane reconciliation.

## 7. Current MEP route

Issue #89 no longer blocks productive source-universe work. Highest-value next route:

```text
FRESH_HSLCA_COHERENT_CAPTURE
→ HPCB / PCF if count-less
→ MDM coverage_complete=true
→ CMI candidate export
→ CWP / ECV / SMC / SRR
```

Fallback lattice:

```text
if discover.swiss credential becomes available
→ STRUCTURED_SOURCE_CAPTURE → SSR

else if fresh HSLCA coherent capture can execute
→ HSLCA → HPCB/PCF → MDM

else
→ EXACT_CURRENT_REFRESH / entity-resolution evidence debt reduction
```

Any source failure is a route change, not permission to allocate canonical IDs from staging.

## 8. Durable NEXT

Canonical machine-readable continuation pointer: `docs/state/NEXT.json`.

Permissions remain fail-closed for the next pre-authority source wave:

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
```

## 9. North-star continuation

```text
fresh coherent source universe
→ MDM coverage_complete=true
→ source-scope reconciliation
→ CMI → CWP → ECV → SMC → SRR
→ every frozen source record terminally maps to ACTIVE_CANONICAL | ALIAS_TO_CANONICAL | EXCLUDED_WITH_REASON
→ unmapped = 0
→ RECONCILE_REQUIRED = 0
→ authoritative DB / HOTELS_MASTER / Intelligence / Graph reconciliation
→ CRM_UNIVERSE_COMPLETE = TRUE only when every independent gate passes
```

Even after CRM completion, outbound remains a separate explicit-authorization gate.
