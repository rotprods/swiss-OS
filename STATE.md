# STATE — LIVE HANDOFF POINTER

Last full operational control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest Drive-mount read recovery / CRM-universe wave: **2026-08-28**.  
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

## 2. Full CRM universe is now the pre-outbound hard gate

User requirement and historical Drive goal are aligned:

```text
CRM_UNIVERSE_COMPLETE = FALSE
```

Outbound must remain CLOSED until **100% of a frozen verified target directory snapshot** is represented in CRM and every source record is deterministically mapped.

Intermediate checkpoints such as CP-0750 are scale milestones only. They cannot be interpreted as outbound readiness.

Governing contract:

`docs/operations/CRM_UNIVERSE_PROTOCOL.md`

## 3. Drive recovery capability

The direct Google Drive connector is disabled in this runtime. However, Google Drive is mounted read-only through ChatGPT Library at `/Google Drive`.

Recovered project path:

`/Google Drive/01_AI_SYSTEMS_AGENTS/00_AGENTIC_SYSTEMS_OS/01_PROJECTS/SWITZERLAND_JOB_OS`

Recovered live CRM/control-plane Sheet:

`01_HOSPITALITY_VERTICAL/HOTELS_MASTER`

Capabilities in this runtime:

```text
Drive mount listing/read/materialize       AVAILABLE
HOTELS_MASTER physical read                AVAILABLE
create-only new artifacts into Drive mount AVAILABLE
native Sheets in-place mutation            UNAVAILABLE
AUTHORITATIVE_WRITE to HOTELS_MASTER       BLOCKED
```

Therefore the current wave runs `RECOVERY_RECONCILE → DEGRADED_CANARY` for CRM ingestion staging.

## 4. CRM target / snapshot state

Drive `G-0500` already defines full Swiss hotel-universe parity with `2050` retained as an immutable reference epoch while later count observations are versioned separately.

Drive source snapshot `HS_2026-08-19_WORKING` records:

```text
working reference records  2050
working reference pages     171
```

Older indexed HotellerieSuisse pages expose different historical totals, confirming that the source denominator changes over time. The completion denominator therefore must be a frozen/versioned snapshot rather than a timeless hard-coded number.

Current gate state:

```text
working reference          2050 / 171 pages
fresh frozen snapshot      NOT YET RECONSTRUCTED
source records fully mapped NO
CRM_UNIVERSE_COMPLETE       FALSE
```

## 5. Latest physically verified constrained authority parent

A deterministic constrained **V13** is the latest physically verified authority parent:

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

V16 remains staging/canary only:

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

Previously proposed IDs are not reservations. Reallocation is mandatory if the live frontier changes before commit.

## 7. Mass CRM ingestion artifact

Created in this recovery wave:

`CRM_UNIVERSE_STAGING_2026-08-28.xlsx`

Contents include:

```text
690 mounted Drive HOTELS_V2 physical rows
25 V16 canary candidates
7 no-ID reserve candidates
171-page directory crawl queue
historical indexed page observations typed discovery-only
existing discovery registry mirror
Drive source-snapshot / goal / checkpoint recovery context
CRM import staging queue
```

This artifact is an ingestion/recovery package, not an authority database.

Public-safe wave detail:

`docs/state/CRM_UNIVERSE_WAVE_2026-08-28.md`

## 8. Production priority

The production bottleneck is now **CRM universe seeding**, not deep enrichment of bounded hotel batches.

Canonical strategy:

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

Only after `CRM_UNIVERSE_COMPLETE = TRUE` may the separate outbound gate be evaluated. Candidate readiness, channel/evidence freshness, suppression/idempotency and explicit user authorization remain independent requirements.

## 10. Source precedence

```text
PHYSICAL + CONSTRAINED AUTHORITY-ELIGIBLE DATA
> live/mounted control plane
> validated authority-eligible manifest
> GitHub STATE pointer
> historical release/handoff prose
```

A local canary is excluded from authority until full promotion.

## 11. Public/private boundary

GitHub stores public-safe executable contracts and state/handoff pointers only. Operational SQLite payloads, contacts, candidate-private data and sensitive raw evidence remain outside the public repository. ChatGPT Library and Drive staging artifacts are recovery/ingestion surfaces, not authority by themselves.