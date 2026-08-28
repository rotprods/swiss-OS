# CRM UNIVERSE — V10 PUBLIC-SAFE HANDOFF

Date: **2026-08-28**  
Wave: `WAVE-20260828-CRM-UNIVERSE-02`  
Mode: `RECOVERY_RECONCILE → DEGRADED_CANARY`  
Authority mutation: **NONE**

## Objective

Complete the frozen/versioned HotellerieSuisse accommodation universe in CRM before outbound eligibility is evaluated.

## Authority unchanged

```text
E4 active canonical    686
physical lineage       690
superseded aliases       4
CRM_UNIVERSE_COMPLETE FALSE
OUTBOUND              CLOSED
send_allowed            0
```

## Staging v10

```text
pages reference                          171
pages with historical/cache evidence      55
pages pending refresh                    116
cache observations                       605
historical missing identities staged     174
CRM import/staging queue                 240
V16 exact-detail canary                   25
reserve/no-ID                              7
snapshot conflict records                  4
normalized name+city import duplicates     0
H-ID reservations from staging             0
formula errors                             0
```

Artifact SHA-256:

`4d06a64e311c5b27f14ce2d3b0f28b219a4d2a26a247db9021f00af752430cf8`

Operational spreadsheet bytes remain outside the public repository.

## Staging precedence repair

The v8 canary exposed a class of duplicate work: historical page observations could re-stage identities already present in V16/current reserve.

The repair is now explicit:

```text
V16 exact/current staging
> current reserve staging
> historical cache discovery
```

Historical observations remain in the cache/evidence ledger but cannot create a second import task for the same normalized name+city pair.

## Snapshot conflict finding

Official directory observations prove page position is unstable across snapshots/locales:

- DE root cache: 2050 / 171 pages;
- FR root cache: 2052 / 171 pages;
- same page number can contain different entities across DE/FR or cache epochs;
- historical totals observed from roughly 2053 through 2114 with shifted pagination.

Final CRM parity therefore requires source-record identity scoped to a frozen snapshot, not `hotel-page-N` identity.

## V12 constrained artifact recovered

Drive now physically exposes V12 manifest + SQLite for E4.

Verified:

```text
active identities      686
alias rows               4
expected physical      690
integrity               ok
FK violations            0
next physical ID        H-0691
SHA-256                 a5d979814ef6c4c9bf44566ec4577d94f6c2660f9ead9934f1173f2903e7fef6
manifest SHA match      TRUE
```

This corrects the earlier statement that V12 was not physically discoverable. Presence alone does not promote a new authority state; E4 remains unchanged.

## Next

Continue broad discovery/anti-join while prioritizing cached pages that belong to the 2050/171 observation epoch when available. Before authoritative promotion, freeze a coherent source snapshot, map every source record, refresh exact-current evidence for true missing identities, then execute the full constrained DB → HOTELS_MASTER → Intelligence → Operational Graph → observability/recovery transaction.
