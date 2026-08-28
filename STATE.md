# STATE — LIVE HANDOFF POINTER

Last full operational control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest Drive-mount read recovery / CRM-universe staging: **2026-08-28 v5**.  
Latest constrained local canary: **SV2-059 / V16**.

## 1. Authoritative operational state — DO NOT INFER FROM CANARY

The last state fully synchronized through Drive/Sheets, constrained DB, Intelligence, Operational Graph and governance remains:

```text
entity epoch                 HS_ENTITY_EPOCH_2026-08-25_E4
physical HOTELS rows         690
superseded duplicate aliases   4
active canonical             686
CP-0750                      686 / 750 ACTIVE
Intelligence                 686 / 686
Operational Graph            686 / 686
L4                           105 / 686
G-0700 L9                      0 / 2050 reference universe
OUTBOUND                     CLOSED
send_allowed                   0
```

Alias lineage remains immutable:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

No canary/staging count advances authority until the full affected-plane promotion chain reconciles.

## 2. Full CRM universe is the pre-outbound hard gate

```text
CRM_UNIVERSE_COMPLETE = FALSE
```

Outbound remains CLOSED until **100% of a frozen verified target directory snapshot** is represented in CRM and every source record is deterministically mapped.

Intermediate checkpoints such as CP-0750 are scale milestones only. They cannot be interpreted as outbound readiness.

Governing contract:

`docs/operations/CRM_UNIVERSE_PROTOCOL.md`

## 3. Drive recovery capability

The direct Google Drive connector is disabled in this runtime. Google Drive is nevertheless mounted through ChatGPT Library at `/Google Drive`.

Recovered live CRM/control-plane:

`/Google Drive/01_AI_SYSTEMS_AGENTS/00_AGENTIC_SYSTEMS_OS/01_PROJECTS/SWITZERLAND_JOB_OS/01_HOSPITALITY_VERTICAL/HOTELS_MASTER`

Capabilities:

```text
Drive mount listing/read/materialize       AVAILABLE
HOTELS_MASTER physical read                AVAILABLE
create-only new Drive artifacts            AVAILABLE
native Sheets in-place mutation            UNAVAILABLE
AUTHORITATIVE_WRITE to HOTELS_MASTER       BLOCKED
```

Issue `#12` tracks only the missing native writer capability.

## 4. CRM target / snapshot state

Drive `G-0500` already defines full Swiss hotel-universe parity with `2050` retained as an immutable reference epoch while later count observations are versioned separately.

Drive source snapshot `HS_2026-08-19_WORKING` records:

```text
working reference records  2050
working reference pages     171
```

Historical indexed member-directory pages expose different totals across crawl dates, confirming that completion must use a newly frozen/versioned snapshot rather than a timeless hard-coded denominator.

Current gate:

```text
working reference           2050 / 171 pages
fresh frozen snapshot       NOT YET RECONSTRUCTED
source records fully mapped NO
CRM_UNIVERSE_COMPLETE        FALSE
```

## 5. Latest physically verified constrained authority parent

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

## 6. V16 acceleration canary — NON-AUTHORITATIVE

```text
local physical rows                         715
local candidate entities excluding aliases 711
exact-detail candidates                      25
integrity_check                              ok
FK violations                                 0
ID gaps                                       0
name+city duplicates                          0
non-empty domain duplicates                   0
idempotency replay unintended inserts         0
restore logical differences                   0
external actions                              0
send_allowed                                  0
```

Previously proposed H-IDs are not reservations.

## 7. CRM mass-ingestion staging v5

Latest staging artifact:

`CRM_UNIVERSE_STAGING_2026-08-28_v5.xlsx`

SHA-256:

`db719f9c16aad80bb7b097ccb7b17148552bb5a60db27ae48fb7e5e669ad9cab`

Drive artifact ID:

`external-gdrive:file:1xBk3c7BWhKv8yM7ET85XDMA6pUy0a6Pr`

Staging metrics:

```text
current mounted Drive physical rows    690
V16 exact-detail canary                  25
reserve candidates without ID             7
historical-cache missing identities       61
CRM import queue                           93
reference directory crawl pages          171
canonical H-ID reservations                0
formula errors                              0
```

The 61 historical-cache identities are **discovery-only**. They passed exact normalized name+city anti-join against the current CRM/staging but still require current exact entity refresh and full entity resolution before any promotion.

The historical cache has already shown its intended acceleration value: in one 84-observation harvest, 57 observations were already current/staged and 27 were new missing identities. Historical cache therefore accelerates discovery without being treated as current membership authority.

Latest recovery pointers are persisted to both Library and Drive:

- `LATEST_CRM_UNIVERSE.json` in Library;
- `LATEST_CRM_UNIVERSE_2026-08-28_v5.json` in Drive;
- `CRM_UNIVERSE_META_GRAPH_DELTA_2026-08-28_v5.json` in Drive Context Hub + Library.

## 8. Production priority

The bottleneck is **CRM universe seeding**, not deep enrichment of bounded hotel batches.

```text
FREEZE/REFRESH DIRECTORY SNAPSHOT
→ ENUMERATE ALL SOURCE RECORDS
→ SOURCE-RECORD STAGING IDS
→ BULK NORMALIZE
→ ANTI-JOIN CRM / ALIASES / GROUPS / DOMAINS
→ ENTITY-RESOLUTION BATCHES
→ DB-FIRST CANONICAL/ALIAS/EXCLUSION COMMIT
→ SHEETS / CRM PK MIRROR
→ OPERATIONAL GRAPH + INTELLIGENCE SEEDS
→ SOURCE-RECORD COVERAGE RECOMPUTE
```

Deep vacancy/housing/people/channel/digital enrichment may proceed in parallel after seeding; it must not block the remaining directory universe from entering CRM.

Primary production issue: `#14 — P0 CRM universe: map 100% frozen hotel snapshot before outbound`.

## 9. Next authoritative execution frontier

When native Sheets write is available:

```text
/wave recover
→ re-read live HOTELS_MASTER / goal / checkpoint / scheduler / issues / snapshots
→ freeze/verify current directory snapshot
→ anti-join all accumulated source-record staging
→ allocate canonical IDs only at DB commit time
→ constrained batch commits
→ Sheets/CRM PK mirror
→ Intelligence seed sync
→ Operational Graph sync
→ metrics / health / SLO / scheduler / issues / transitions
→ source-record coverage reconciliation
→ GitHub STATE/handoff
→ Library + Drive recovery
→ CRM_UNIVERSE_COMPLETE only at 100% mapped snapshot
```

Only after `CRM_UNIVERSE_COMPLETE = TRUE` may the separate outbound gate be evaluated. Candidate readiness, evidence/channel freshness, suppression/idempotency and explicit user authorization remain independent requirements.

## 10. Source precedence

```text
PHYSICAL + CONSTRAINED AUTHORITY-ELIGIBLE DATA
> live/mounted control plane
> validated authority-eligible manifest
> GitHub STATE pointer
> historical release/handoff prose
```

A local canary or cache-derived staging row is excluded from authority until full promotion.

## 11. Public/private boundary

GitHub stores public-safe executable contracts and state/handoff pointers only. Operational SQLite payloads, contacts, candidate-private data and sensitive raw evidence remain outside the public repository. ChatGPT Library and Drive staging artifacts are recovery/ingestion surfaces, not authority by themselves.