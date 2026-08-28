# ASR Repair Canary — 2026-08-28 V1

Status: **NON-AUTHORITATIVE / SAFE_STOP_CANARY**  
Wave: `WAVE-20260828-ASR-REPAIR-CANARY-01`  
Git parent: `377744d9860e89861f0c80d045d774dcb58eb03b`  
Authority epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`  
Authority parent: `OPERATIONAL_DB_SHADOW_MANIFEST_V13`  
Parent DB SHA-256: `0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5`

## Finding

Issue `#89` is a semantic identity failure that structural SQLite integrity does not detect.

Persisted H-ID aliases:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

The physical identities on the two sides are unrelated hotels. Historical HOTELS_MASTER revision `464` shows all eight identities existed simultaneously as distinct current canonical hotels before the supersession run. `ENTITY_RESOLUTION:ER-CP0650-001..004` identifies the target identities as duplicate research candidates but incorrectly associates unrelated source H-IDs in the supersession notes.

Each target exact `name + city` occurs once in V13, so no target-name duplicate physical hotel exists to supersede.

## Repair canary

A disposable copy of V13 was modified only by:

```sql
UPDATE hotels
SET state='CANONICAL_CURRENT_RECONCILED'
WHERE hotel_id IN ('H-0610','H-0624','H-0629','H-0630');

DELETE FROM hotel_aliases
WHERE alias_hotel_id IN ('H-0610','H-0624','H-0629','H-0630');
```

Result:

```text
canary SHA-256                 70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
physical rows                  690
candidate active if promoted   690 — CANARY ONLY
hotel_aliases after repair       0
superseded hotel rows after      0
SQLite integrity_check         ok
FK violations                    0
logical DB tables changed        2
hotels rows changed               4
hotel_alias rows removed          4
other table differences           0
idempotency replay             PASS / 0 further mutations
H-ID allocations                  0
```

The candidate `690` denominator is not authority. It becomes eligible only after the full cross-plane repair is reconciled and ASR-1.0 returns `EXACT`.

## Required authority-repair surface

A later bounded recovery wave must reconcile in one logical transaction:

- constrained DB four hotel-state restorations + four invalid H-ID alias removals;
- HOTELS_V2 four PK-keyed state restorations;
- HOTEL_INTELLIGENCE_V1 four identity reactivations without invented enrichment;
- GRAPH_NODES_V2 four HOTEL + four INTEL node restorations;
- GRAPH_EDGES_V2 four invalid `ALIASES_TO` removals/tombstones + four `HAS_INTELLIGENCE` edge restorations;
- four corrective STATE_TRANSITIONS appended while preserving prior history;
- ER-CP0650-001..004 preserved as research anti-join evidence without physical-supersession meaning;
- active denominator / Intelligence / Operational Graph / scheduler / checkpoint / metrics recomputation;
- recovery, restore/replay and idempotency gauntlet.

## Promotion gates

```text
fresh main ancestry reconstruction
V13 parent SHA unchanged
recoverable HOTELS_MASTER rollback artifact exists
PK-keyed writes only
ASR-1.0 = EXACT
DB ↔ HOTELS_MASTER affected PKs exact
invalid ALIASES_TO = 0
orphan superseded HOTEL/INTEL nodes = 0
Intelligence denominator = corrected active denominator
Operational Graph denominator = corrected active denominator
restore/replay/idempotency = PASS
no concurrent parent movement
```

Failure of any gate means `RECOVERY_RECONCILE / DEGRADED_CANARY`; no partial authority promotion.

## Durable recovery

Drive report: `ASR_REPAIR_CANARY_2026-08-28_V1`, document ID `1AACvFVJx7WvgEnme9nibCqQgebSYZ_qDrwkg43aAdAY`, under `11_OPERATIONAL_DB_SNAPSHOTS`.

The local SQLite canary could not be connector-egressed from the sandbox. Its deterministic recipe and SHA are retained here and in the Drive report; immutable V13 remains the durable parent.

## Hard locks

```text
authority_advanced = FALSE
canonical H-ID allocations = 0
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```
