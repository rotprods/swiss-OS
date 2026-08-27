# STATE — LIVE HANDOFF POINTER

Last full control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest constrained local canary: **SV2-059 / V16**.

## 1. Authoritative state — DO NOT INFER FROM CANARY

The last state fully synchronized through Drive/Sheets, constrained DB, Intelligence, Graph and governance remains:

```text
entity epoch              HS_ENTITY_EPOCH_2026-08-25_E4
physical HOTELS rows      690
superseded aliases          4
active canonical          686
CP-0750                   686 / 750 ACTIVE
remaining                  64
next authoritative ID     H-0691
Intelligence              686 / 686
Graph V2                  686 / 686
L4                        105 / 686
G-0700 L9                   0 / 2050
outbound                  CLOSED
send_allowed                0
```

Alias lineage is immutable:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

## 2. Latest physically verified authoritative parent

The E4 control plane referenced a V12 shadow that was not physically discoverable during recovery. V13 was reconstructed deterministically from the last persisted V9 plus authoritative E3/E4 deltas and the four alias mappings.

```text
V13 physical rows          690
V13 active                 686
integrity_check             ok
FK violations                0
ID gaps                      0
replay delta                 0
send_allowed                 0
SHA-256  0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
```

V13 is the authoritative constrained parent until a later full synchronization succeeds.

## 3. SV2-059 / V16 local acceleration canary

Batch05 has reached the configured bounded ceiling: **25 exact member/entity-detail identities** staged as non-authoritative canary rows.

```text
local physical rows                         715
local candidate entities excluding aliases 711
Batch05 exact-detail candidates              25
integrity_check                              ok
FK violations                                 0
ID gaps                                       0
name+city duplicates                          0
non-empty domain duplicates                   0
idempotency replay new inserts                0
external actions                              0
send_allowed                                  0
restore tables compared                      63
restore logical differences                   0
```

Projection **only if** the future synchronized commit revalidates the allocation:

```text
711 / 750
39 remaining
next ID H-0716
```

These projection values are **not current authority**.

Full public-safe V16 detail:

`docs/state/SV2_059_V16_CANARY.md`

## 4. Intelligence prefetch

Public-safe staging research for the same 25-ID execution lane is persisted at:

`docs/intelligence/SV2_059_INTELLIGENCE_PREFETCH.md`

Strongest current Batch05 signal: Hotel Crystal St. Moritz has a current official careers/open-positions route. Other discovered general contacts, brand-level career portals and group relationships remain separately typed and do not earn L4 by themselves.

Authoritative L4 remains **105 / 686**. Prefetch L4 promotions = **0**.

## 5. Restore invariant

SQLite binary SHA equality is a transfer invariant, not the restore-equivalence invariant.

Restore PASS requires:

- source and restore `integrity_check = ok`;
- zero FK violations on both;
- identical operational schema objects;
- identical table sets and row counts;
- `source EXCEPT restore = ∅` for every table;
- `restore EXCEPT source = ∅` for every table.

Executable contract: `swiss_os.db.sqlite_logical_differences()`.

## 6. Authority blocker

The Google Drive/Sheets write plane became unavailable during SV2-059. Under `INV-025`, DB-only state cannot become canonical.

Before promotion, execute exactly:

```text
REHYDRATE LIVE DRIVE/SHEETS
→ ANTI-JOIN ALL 25 CANDIDATES + ALIASES + DOMAINS
→ REALLOCATE IDs IF THE LIVE FRONTIER MOVED
→ CONSTRAINED DB COMMIT
→ SHEETS PK MIRROR
→ INTELLIGENCE L1
→ GRAPH V2
→ ENTITY EPOCH
→ METRICS / HEALTH / SLO
→ CHECKPOINT / SCHEDULER
→ STATE TRANSITIONS / RUN LOG
→ PERSISTENT HANDOFF
```

No provisional `H-0691..H-0715` ID is reserved until that chain succeeds.

## 7. Active execution frontier

`SV2-059 / CP0750-BATCH05`

Discovery quota for this bounded batch is complete at **25/25 exact-detail**. Do not continue blind canonical allocation beyond the batch ceiling. Use remaining time for evidence/intelligence prefetch, QA and recovery hardening until the live authority plane can be re-read.

## Source precedence

```text
PHYSICAL + CONSTRAINED DATA
> live Sheets registries / active control plane
> latest validated operational manifest
> repository STATE.md
> historical release prose / handoffs
```

GitHub stores public-safe executable contracts and handoff state only. Operational SQLite payloads, people/channels, candidate private data and raw evidence stay outside the public repository.
