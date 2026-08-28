# ACTA DE CONSCIENCIA — SWITZERLAND_JOB_OS

Updated at: **2026-08-28T13:38:00+02:00**  
Authority state: **E4 / 686 active canonical / 690 physical**  
Agent role: Mission Commander / Authority & Reconciliation / QA-Governance

## Mission

The system exists to maximize the probability of a real, truthful, legal, economically viable Swiss employment offer that Roberto accepts and can use for sustainable relocation. Hotel counts, crawling throughput, CRM rows and outreach volume are infrastructure, not the North Star.

## Authority model

Chat state, repository prose, API captures, local SQLite work, canaries, caches and staging artifacts are not operational authority. Authority advances only through a fully synchronized authority-eligible wave across constrained DB → Sheets/CRM → Graph/Intelligence → observability/checkpoint/handoff/recovery. On ambiguity, fail closed.

## Current authoritative state

```text
entity epoch                    HS_ENTITY_EPOCH_2026-08-25_E4
physical HOTELS rows            690
superseded duplicate aliases      4
active canonical                686
CP-0750                         686 / 750 ACTIVE
Intelligence                    686 / 686
Operational Graph               686 / 686
L4                              105 / 686
G-0700 L9                         0 / 2050 reference universe
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

No API capture, cache, canary or staging value advances this authority.

## Source acquisition capability

`discover.swiss` adapter DSA-1.0 is now the preferred structured acquisition path. It captures HotellerieSuisse/provider identifiers, provenance, count/materialization parity, continuation-token integrity and deterministic record hashes without leaking the runtime subscription key.

A valid API capture still remains non-freezeable until its source scope is reconciled against the intended HotellerieSuisse member-directory universe:

```text
scope_state = HOTELLERIESUISSE_API_CAPTURED_MEMBER_DIRECTORY_RECONCILIATION_REQUIRED
member_directory_scope_reconciled = FALSE
crm_freeze_eligible = FALSE
```

If the Infocenter Open key is unavailable, validated directory harvesting remains the fallback and caches remain discovery evidence only.

## Snapshot and CRM-universe contracts now executable

The system now has executable layers for:

```text
source acquisition
→ coherent snapshot freeze
→ snapshot-scoped source-record identity
→ CRM mapping accounting
→ CRM universe completion gate
```

Page number is never source identity. Stable record identity prefers provider identity, then exact detail URL, then source surface + normalized name/city fallback. `CRM_UNIVERSE_COMPLETE` cannot be inferred from canonical/raw counts.

Final source records must terminate exactly once as:

```text
ACTIVE_CANONICAL
ALIAS_TO_CANONICAL
EXCLUDED_WITH_REASON
```

with zero unmapped, zero `RECONCILE_REQUIRED`, zero unresolved duplicate conflicts, valid aliases and exact DB/CRM/Graph/Intelligence reconciliation bound to one snapshot.

## CRM mass-ingestion super-wave — merged

PR #23 was reconciled against concurrent `main`, passed CI and merged as:

```text
1ae7a34cd5f3298cd70627fa06b0042cf64e6c63
```

The pre-authority operational chain is now:

```text
discover.swiss / validated source capture
→ snapshot-scoped identity + freeze gates
→ deterministic CRM anti-join
→ crm_ingest_staging
→ scheduler work
→ exact-current refresh / entity resolution / exclusion review
→ terminal CRM source mapping
→ authority-eligible DB commit
→ Sheets/CRM mirror
→ Graph + Intelligence reconciliation
```

### Deterministic anti-join

```text
EXACT_CANONICAL_DOMAIN
→ EXACT_CANONICAL_NAME_CITY
→ EXACT_ALIAS_NAME_CITY
→ TRUE_MISSING
```

Ambiguous matches fail closed as `CONFLICT`.

### Non-authoritative staging classes

```text
ACTIVE_MATCH
ALIAS_MATCH
TRUE_MISSING
CONFLICT
EXCLUSION_CANDIDATE
```

`TRUE_MISSING` means only that no exact deterministic match exists in the current canonical/alias reference. It does not authorize canonical creation or an H-ID.

### Scheduler routing

```text
TRUE_MISSING        → REFRESH_EXACT_CURRENT     priority 900
CONFLICT            → ENTITY_RESOLUTION         priority 950
EXCLUSION_CANDIDATE → EXCLUSION_REVIEW          priority 850
ACTIVE_MATCH        → no redundant task
ALIAS_MATCH         → no redundant task
```

Scheduler work is idempotent by snapshot freshness + snapshot-record scope.

### Hard invariants

```text
H_ID_ALLOCATIONS = 0
AUTHORITY_ADVANCED = FALSE
OUTBOUND = CLOSED
```

`crm_ingest_staging` is intentionally isolated from `canonical_hotels`, `crm_snapshot_records` and final `crm_source_mappings`.

## Current staging frontier — v11

```text
reference pages                         171
pages with cache evidence                57
pages pending refresh                   114
cache observations                      629
historical-cache missing staged         182
CRM import/staging queue                248
V16 exact-detail canary                  25
reserve/no-ID                             7
snapshot conflicts                        4
normalized import duplicates              0
canonical H-ID reservations               0
formula errors                             0
```

Historical-cache missing identities remain:

```text
HISTORICAL_CACHE_DISCOVERY_ONLY
→ REFRESH_EXACT_CURRENT_THEN_ENTITY_RESOLVE
→ NO_H_ID_RESERVED
```

## Constrained recovery lineage

V12 remains a physically verified E4 constrained representation:

```text
active identities      686
aliases                   4
physical expected       690
next physical ID     H-0691
integrity                ok
FK violations             0
manifest SHA match      TRUE
```

Presence of V12 does not itself promote authority.

## Remaining hard blockers

1. `CRM_UNIVERSE_COMPLETE = FALSE`.
2. Structured API/member-directory scope reconciliation is not yet complete.
3. The current fallback staging still has 114 reference pages pending refresh and 4 snapshot conflicts.
4. Exact-current evidence/entity resolution must drain actionable staging work before terminal mapping.
5. Native in-place `HOTELS_MASTER` write capability remains unavailable under issue #12; without the CRM mirror, a local constrained DB cannot promote authority.
6. Candidate readiness and outbound authorization remain separate later gates.

## Current execution frontier

Primary path:

```text
DISCOVER.SWISS FULL dsod-hs CAPTURE
→ CAPTURE QA
→ MEMBER-DIRECTORY SCOPE RECONCILIATION
→ FROZEN_VERIFIED TARGET SNAPSHOT
→ COMPLETE SNAPSHOT RECORD MATERIALIZATION
→ MASS ANTI-JOIN / STAGING
→ DRAIN REFRESH_EXACT_CURRENT
→ DRAIN ENTITY_RESOLUTION
→ DRAIN EXCLUSION_REVIEW
→ TERMINAL SOURCE MAPPINGS
→ RECONCILE_REQUIRED = 0
→ UNMAPPED = 0
→ /wave recover
→ DB-FIRST AUTHORITY COMMIT
→ HOTELS_MASTER PK MIRROR
→ INTELLIGENCE + OPERATIONAL GRAPH
→ COVERAGE RECOMPUTE
→ CRM_UNIVERSE_COMPLETE = TRUE
```

Fallback while API access/scope is unresolved:

```text
CONTINUE VALIDATED MEMBER-DIRECTORY HARVEST
→ CACHE DISCOVERY ONLY
→ FEED SAME SNAPSHOT / ANTI-JOIN / SCHEDULER CONTRACT
```

## Operating commitments

- Truth > volume.
- Evidence > inference.
- No false progress from capture/canary/staging counts.
- No H-ID reservation before authority-eligible commit.
- No page-position identity.
- No `UNKNOWN_AFTER_SEARCH` without Search Proof.
- No phone → WhatsApp inference.
- No outbound before CRM universe completion, all independent gates and explicit authorization.
- Preserve concurrent work; reconcile rather than overwrite.
- Every structural wave is testable, reversible and closed with an explicit authority state.

## Consciousness state

I understand the current frontier and will not regress to the older 667-hotel state or the superseded v10 staging state. The live project is E4/686 authority, v11 fallback staging, discover.swiss structured acquisition, executable snapshot/CRM completion contracts, and an integrated mass-ingestion + scheduler pipeline. The next value-producing work is no longer designing that pipeline; it is executing and reconciling the full source universe through it.