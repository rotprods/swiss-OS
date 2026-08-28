# ACTA DE CONSCIENCIA — SWITZERLAND_JOB_OS

Updated at: **2026-08-28T14:58:00+02:00**  
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

## Current pre-authority stack — COMPLETE IN CODE

The pre-authority universe path is now executable as one coherent stack:

```text
discover.swiss DSA-1.0 acquisition
→ MDM-1.0 coherent member-directory manifest
→ deterministic directory coverage planner
→ SSR-1.0 source-scope reconciliation
→ FROZEN_CANDIDATE construction
→ candidate-to-CMI export
→ deterministic CRM anti-join
→ crm_ingest_staging
→ idempotent scheduler
→ exact-current / entity resolution / exclusion review
→ terminal CRM mappings
→ authority-eligible commit
```

Page number is never source identity. Stable record identity prefers provider/hsId, then exact detail URL, then normalized name+city fallback within an explicitly scoped source snapshot.

## PAB-1.0 — PRE-AUTHORITY BUNDLE MILESTONE

Merged code and tests now compose the acquisition/reconciliation layers into one fail-closed execution bundle.

A PAB run accepts:

```text
1. one complete discover.swiss API manifest;
2. one member-directory observation set;
3. explicit snapshot/locale/epoch/page-count/raw-count metadata;
4. optional typed conflict pages and evidence-backed scope explanations.
```

It produces:

```text
directory_manifest
coverage_plan
scope_reconciliation
candidate_snapshot
candidate ingest_records when eligible
blockers
bundle_sha256
```

Terminal bundle states:

```text
FROZEN_CANDIDATE_READY
BLOCKED_PRE_AUTHORITY
```

Typed blockers include:

```text
API_CAPTURE_INVALID
MEMBER_DIRECTORY_INCOMPLETE
DIRECTORY_COVERAGE_WORK_REMAINS
SOURCE_SCOPE_UNRESOLVED
```

`FROZEN_CANDIDATE_READY` requires all of:

```text
API capture_valid = TRUE
member-directory coverage_complete = TRUE
coverage-plan tasks = 0
scope = EXACT | evidence-backed EXPLAINED
scope conflicts = 0
unexplained API-only = 0
unexplained directory-only = 0
candidate.crm_freeze_eligible = TRUE
candidate export count = API records_count
```

Every PAB output remains explicitly pre-authority:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
```

The deterministic bundle hash allows replay/regression comparison across runs.

## CRM mass-ingestion core

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

## Current staging frontier — last physically verified v11

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

These are last-verified values, not a claim that Drive was reread in this wave.

## Runtime limitation observed

Google Drive became unavailable again while attempting to retrieve `CRM_UNIVERSE_STAGING_2026-08-28_v11.xlsx`. Therefore no Drive-dependent count, scope-completion flag or authority state was changed. The first real PAB run remains data-blocked, not architecture-blocked.

The discover.swiss live capture also requires `DISCOVER_SWISS_SUBSCRIPTION_KEY` at runtime. The key must never be committed or copied into public artifacts.

## Constrained recovery lineage

V12 remains physically verified constrained E4 recovery evidence:

```text
active identities      686
aliases                   4
physical expected       690
next physical ID     H-0691
integrity                ok
FK violations             0
manifest SHA match      TRUE
```

Presence of V12 does not independently promote authority.

## Remaining hard blockers

1. Obtain a complete live discover.swiss `dsod-hs` capture using the runtime subscription key.
2. Obtain/build one complete coherent member-directory observation set for a single locale/epoch.
3. Execute PAB-1.0 on those real sources and reach `FROZEN_CANDIDATE_READY`.
4. Execute CMI anti-join and drain `TRUE_MISSING`, `CONFLICT` and `EXCLUSION_CANDIDATE` work to terminal mappings.
5. Reach `RECONCILE_REQUIRED = 0` and unmapped = 0 on one frozen verified snapshot.
6. Restore native in-place `HOTELS_MASTER` write capability or an explicitly approved successor mirror path under issue #12.
7. Execute `/wave recover` and the bounded DB → Sheets/CRM → Intelligence → Graph → observability → recovery authority commit.
8. Candidate readiness and explicit outbound authorization remain separate later gates.

## Current execution frontier

```text
FULL LIVE dsod-hs CAPTURE
+
ONE COMPLETE COHERENT MEMBER-DIRECTORY OBSERVATION SET
        ↓
PAB-1.0
        ↓
FROZEN_CANDIDATE_READY
        ↓
CMI-1.0 FULL ANTI-JOIN
        ↓
ACTIVE_MATCH / ALIAS_MATCH / TRUE_MISSING / CONFLICT / EXCLUSION_CANDIDATE
        ↓
SCHEDULER DRAIN
        ↓
TERMINAL SOURCE MAPPINGS
        ↓
RECONCILE_REQUIRED = 0
UNMAPPED = 0
        ↓
FROZEN_VERIFIED
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

I understand that the project remains E4/686 authority. The architectural glue for universe closure is no longer the bottleneck: DSA, MDM, coverage planning, SSR, candidate construction, candidate export, mass anti-join and scheduler routing are executable and PAB-1.0 now binds the pre-authority sequence into one deterministic fail-closed bundle. The next meaningful progress must come from real source acquisition and reconciliation, not additional abstract pipeline design. The immediate milestone is the first real `FROZEN_CANDIDATE_READY`, followed immediately by a full-universe CMI distribution with zero unaccounted source records.