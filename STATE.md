# STATE — LIVE HANDOFF POINTER

Latest Meta Execution reconciliation: **2026-08-28T20:08:00+02:00**.  
Latest reconstructed GitHub `main`: **`377744d9860e89861f0c80d045d774dcb58eb03b`**.  
Latest physically verified constrained parent: **`OPERATIONAL_DB_SHADOW_MANIFEST_V13`**.  
Latest semantic-authority gate: **ASR-1.0 / issue #89 = RECONCILE_REQUIRED**.  
Latest repair artifact: **ASR_REPAIR_CANARY_2026-08-28_V1**.

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

Do **not** infer an authoritative `690 active` merely by deleting the four edges. `690` exists only as a repair-canary candidate until DB → HOTELS_MASTER → Intelligence → Operational Graph → observability/recovery reconcile atomically and ASR-1.0 returns `EXACT`.

## 2. P0 #89 — semantic alias identity corruption

Persisted edges in V13 / HOTELS_MASTER:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

Physical identities prove those edges join unrelated hotels:

```text
H-0610  Hôtel Alpe Fleurie — Villars-sur-Ollon
H-0656  Hotel Murtenhof & Krone — Murten

H-0624  Hôtel Le Mont Paisible — Crans-Montana
H-0639  Hotel Alpbach — Meiringen

H-0629  Stiftung Lilienberg Unternehmerforum — Ermatingen
H-0638  Jugendherberge Seelisberg — Seelisberg

H-0630  Strandhotel Iseltwald — Iseltwald
H-0640  Hotel Central Luzern — Luzern
```

`ENTITY_RESOLUTION:ER-CP0650-001..004` identifies the *target* properties as duplicate candidates but its notes attach the unrelated source H-IDs as superseded rows. Historical HOTELS_MASTER revision `464` proves both sides existed simultaneously as distinct current canonical hotels before the supersession run. Each target name+city occurs exactly once in V13, so there is no target-name physical duplicate row to supersede.

Root class:

```text
candidate / H-ID lineage drift
→ research duplicate was correctly anti-joinable to an existing target
→ unrelated physical H-ID was incorrectly marked superseded
```

Issue: `#89`.

## 3. ASR-1.0 now merged

PR `#90` merged as:

```text
377744d9860e89861f0c80d045d774dcb58eb03b
```

Contract:

`docs/operations/ALIAS_SEMANTIC_RECONCILIATION.md`

Executable validator:

`src/swiss_os/alias_semantics.py`

ASR-1.0 adds the invariant that every persisted alias edge must prove semantic identity, not merely PK/FK validity. It fails closed on missing/ambiguous evidence, mismatched physical identity, target mismatch, self-aliases, or unproved real-world equivalence. A stronger stable-identity override requires an allowed basis plus a durable evidence reference; a bare boolean cannot bypass the gate.

Repository CI and adversarial regression tests include the exact four issue-#89 mappings.

## 4. Repair canary V1 — non-authoritative

A disposable copy of V13 was repaired without creating, deleting, reusing or renumbering any H-ID.

```text
file                          switzerland_job_os_operational_shadow_v14_alias_repair_canary.sqlite
canary SHA-256                70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
physical rows                 690
candidate active if promoted  690 — CANARY ONLY
hotel_aliases after repair      0
superseded hotel rows after     0
SQLite integrity_check        ok
FK violations                   0
idempotency replay            PASS / 0 additional updates / 0 deletes
```

Logical differences from V13 are exactly:

```text
hotels         4 state restorations
hotel_aliases  4 invalid edge removals
all other DB tables 0 logical differences
```

Canary state restorations:

```text
H-0610 → CANONICAL_CURRENT_RECONCILED
H-0624 → CANONICAL_CURRENT_RECONCILED
H-0629 → CANONICAL_CURRENT_RECONCILED
H-0630 → CANONICAL_CURRENT_RECONCILED
```

Drive durable canary report:

`ASR_REPAIR_CANARY_2026-08-28_V1` — Google Doc ID `1AACvFVJx7WvgEnme9nibCqQgebSYZ_qDrwkg43aAdAY`, stored under `11_OPERATIONAL_DB_SNAPSHOTS`.

The local SQLite canary itself could not be connector-egressed from the execution sandbox; its SHA and fully deterministic two-statement repair recipe are persisted in the Drive report. V13 remains the durable immutable parent.

## 5. Exact cross-plane repair required

Before any authority promotion, the same bounded recovery wave must reconcile:

```text
constrained DB
→ HOTELS_V2 four PK-keyed state corrections
→ HOTEL_INTELLIGENCE_V1 four identity reactivations
→ GRAPH_NODES_V2 eight node-state corrections
→ GRAPH_EDGES_V2 four invalid ALIASES_TO removals/tombstones
→ restore four HOTEL→INTEL edge semantics
→ append four corrective STATE_TRANSITIONS
→ preserve ER-CP0650-001..004 as research anti-join evidence, not physical supersession evidence
→ recompute active denominator
→ recompute Intelligence / Graph denominators
→ scheduler / checkpoint / metrics / SLO reconciliation
→ recovery + replay + idempotency
→ ASR-1.0 EXACT
```

Current live mirrors confirm the corruption is materialized consistently across HOTELS_V2, HOTEL_INTELLIGENCE_V1, GRAPH_NODES_V2, GRAPH_EDGES_V2 and STATE_TRANSITIONS. That consistency does not make it correct; it defines the atomic repair surface.

## 6. Source-universe work remains valid but is temporarily lower priority

The pre-authority CRM pipeline already on `main` remains available:

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

The previous full live directory canary acquired all `172/172` pages and `2061` unique detail URLs but was diagnostic because MDC-1.0 reversed city/name fields. MDC-1.1 fixed that parser. `discover.swiss` remains unavailable without `DISCOVER_SWISS_SUBSCRIPTION_KEY`.

Open PR `#88` remains **unmerged** because its HSLCA→PCF live canary has not yet produced the required green live-source qualification. Do not merge it merely because repository CI passes.

Source acquisition is not the current highest-value route while the authority parent itself is semantically unsafe.

## 7. Runtime capability

```text
GitHub read/write/CI                         AVAILABLE
web research                                 AVAILABLE
authenticated Drive read                     AVAILABLE
Drive/Docs durable writes                    AVAILABLE
native HOTELS_MASTER in-place Sheets write   AVAILABLE
V13 raw parent recovery                      AVAILABLE / SHA verified
Library durable write                        not proven in this activation
```

Do not claim Library synchronization unless a real write actuator succeeds.

## 8. Current MEP route

Highest-value safe route:

```text
ALIAS_SEMANTIC_ATOMIC_RECOVERY_PREFLIGHT
→ reconstruct exact affected PKs across every live plane
→ create rollback/recovery snapshot
→ fresh ancestry + V13 parent verification
→ bounded repair transaction only if every precondition passes
→ ASR-1.0 EXACT
→ exact cross-plane reconciliation
→ only then resume CRM source-universe frontier
```

If any required authority plane or rollback primitive cannot be proven, remain in `RECOVERY_RECONCILE / DEGRADED_CANARY` and continue non-destructive lineage/QA work rather than partially repairing live authority.

## 9. Durable NEXT

Canonical machine-readable pointer: `docs/state/NEXT.json`.

Permissions remain:

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
```

## 10. North-star continuation

After #89 is fully and atomically reconciled:

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
