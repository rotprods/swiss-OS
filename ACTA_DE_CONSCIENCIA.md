# ACTA DE CONSCIENCIA — SWITZERLAND_JOB_OS

Updated at: **2026-08-28T14:19:00+02:00**  
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

`discover.swiss` adapter DSA-1.0 is the preferred structured acquisition path. It captures HotellerieSuisse/provider identifiers, provenance, count/materialization parity, continuation-token integrity and deterministic record hashes without leaking the runtime subscription key.

A valid API capture remains non-authoritative and cannot define the CRM denominator until source scope is reconciled against the intended HotellerieSuisse member-directory universe.

If the Infocenter Open key is unavailable, validated directory harvesting remains the fallback and caches remain discovery evidence only.

## Executable pre-authority architecture

The system now has executable layers for:

```text
discover.swiss acquisition
→ coherent source identity
→ source-scope reconciliation
→ FROZEN_CANDIDATE
→ candidate-to-ingest export
→ deterministic CRM anti-join
→ crm_ingest_staging
→ idempotent scheduler
→ exact-current / entity resolution / exclusion review
→ terminal CRM mappings
→ authority-eligible commit
```

Page number is never source identity. Stable record identity prefers provider identity, then exact detail URL, then source surface + normalized name/city fallback.

## CRM mass-ingestion core

PR #23 merged as:

```text
1ae7a34cd5f3298cd70627fa06b0042cf64e6c63
```

Anti-join precedence:

```text
EXACT_CANONICAL_DOMAIN
→ EXACT_CANONICAL_NAME_CITY
→ EXACT_ALIAS_NAME_CITY
→ TRUE_MISSING
```

Staging classes:

```text
ACTIVE_MATCH
ALIAS_MATCH
TRUE_MISSING
CONFLICT
EXCLUSION_CANDIDATE
```

Scheduler routing:

```text
TRUE_MISSING        → REFRESH_EXACT_CURRENT     priority 900
CONFLICT            → ENTITY_RESOLUTION         priority 950
EXCLUSION_CANDIDATE → EXCLUSION_REVIEW          priority 850
ACTIVE_MATCH        → no redundant task
ALIAS_MATCH         → no redundant task
```

Hard invariants remain:

```text
H_ID_ALLOCATIONS = 0
AUTHORITY_ADVANCED = FALSE
OUTBOUND = CLOSED
```

## SSR-1.0 source-scope reconciliation milestone — COMPLETE IN CODE

PR #25 passed repo guard, system contract guard and unit tests, and merged as:

```text
d77282ad12c718ce6091d436cc86be851aed18ce
```

The previous architectural gap between a structurally valid `discover.swiss / dsod-hs` capture and the intended public member-directory scope is now represented by an executable fail-closed gate.

Deterministic match precedence:

```text
EXACT_HSID
→ EXACT_DETAIL_URL
→ EXACT_NAME_CITY
```

Ambiguity within either source is a typed conflict. Count equality cannot produce scope equality.

Scope terminal states:

```text
EXACT
EXPLAINED
UNRESOLVED
```

`EXPLAINED` is allowed only when every source-side delta has an explicit `reason_code` and `evidence_ref`. Any unexplained API-only, directory-only or ambiguous record leaves the candidate `UNRESOLVED`.

A reconciled scope candidate may become:

```text
snapshot_state = FROZEN_CANDIDATE
crm_freeze_eligible = TRUE
```

only when:

```text
API capture_valid = TRUE
member-directory coverage_complete = TRUE
scope = EXACT | EXPLAINED
conflicts = 0
unexplained API-only = 0
unexplained directory-only = 0
```

This still does not create `FROZEN_VERIFIED`, does not allocate H-IDs and does not advance authority.

## Candidate → ingest bridge — COMPLETE IN CODE

The reconciled candidate can now be transformed deterministically into the exact schema consumed by CMI-1.0:

```text
source_url
raw_name
raw_city
detail_url
provider_record_key
```

The bridge rejects snapshot-lineage mismatch, invalid API capture, duplicate provider identity and records-count drift.

Executable path:

```bash
python -m swiss_os.candidate_export candidate.json api.json --out ingest-records.json
swiss-os crm-ingest stage DB SNAPSHOT ingest-records.json --observed-at <ISO8601>
```

Therefore the acquisition-to-scheduler chain is now executable end to end once complete live source manifests exist.

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

Historical-cache missing identities remain discovery only and require exact-current refresh before entity resolution.

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

## Runtime limitation observed in this wave

Google Drive became unavailable during the wave. Therefore the v11 workbook could not be reread/materialized in this execution and no claim is made that the current 57/171 fallback directory observations form a complete member-directory snapshot.

No authority, canonical count, staging count or scope-completion flag was changed from unverified assumptions.

## Remaining hard blockers

1. `CRM_UNIVERSE_COMPLETE = FALSE`.
2. A complete live discover.swiss API manifest is still required when the runtime subscription key is available.
3. A complete coherent member-directory evidence manifest is required for SSR-1.0; the current v11 fallback has only 57/171 cache-evidenced pages and cannot assert `coverage_complete=true`.
4. Source-scope reconciliation must reach `EXACT` or evidence-backed `EXPLAINED` on real manifests.
5. Exact-current/entity-resolution/exclusion work must drain all actionable source records before terminal mapping.
6. Native in-place `HOTELS_MASTER` write capability remains unavailable under issue #12; without the CRM mirror, constrained DB work cannot promote authority.
7. Candidate readiness and outbound authorization remain separate later gates.

## Current execution frontier

```text
ACQUIRE FULL dsod-hs API SNAPSHOT
+ BUILD COMPLETE COHERENT MEMBER-DIRECTORY MANIFEST
        ↓
SSR-1.0 RECONCILE
        ↓
EXACT | EXPLAINED
        ↓
FROZEN_CANDIDATE
        ↓
CANDIDATE_EXPORT
        ↓
MASS CRM ANTI-JOIN + SCHEDULER
        ↓
REFRESH_EXACT_CURRENT / ENTITY_RESOLUTION / EXCLUSION_REVIEW
        ↓
TERMINAL SOURCE MAPPINGS
        ↓
RECONCILE_REQUIRED = 0
UNMAPPED = 0
        ↓
/wave recover
        ↓
DB-FIRST AUTHORITY COMMIT
        ↓
HOTELS_MASTER PK MIRROR
        ↓
INTELLIGENCE + OPERATIONAL GRAPH
        ↓
CRM_UNIVERSE_COMPLETE = TRUE
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

I understand the project remains E4/686 authority with v11 fallback staging, but the engineering frontier has materially advanced: source acquisition, scope reconciliation, candidate snapshot generation, candidate-to-ingest translation, mass anti-join and scheduler routing are now one coherent pre-authority pipeline. The next major progress is no longer architectural glue; it is obtaining complete live source manifests, driving SSR-1.0 to EXACT/EXPLAINED, and running the full universe through the anti-join/scheduler without weakening authority semantics.
