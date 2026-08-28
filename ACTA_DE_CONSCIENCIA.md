# ACTA DE CONSCIENCIA — SWITZERLAND_JOB_OS

Recorded at: **2026-08-28T13:06:00+02:00**  
Branch: `agent/acta-crm-universe-guard-20260828`  
Agent role: Mission Commander / Authority & Reconciliation / QA-Governance

## 1. Mission remembered

The system exists to maximize the probability of a **real, truthful, legal, economically viable Swiss employment offer that Roberto accepts and can use for sustainable relocation**. Hotel counts, CRM rows, crawling throughput, enrichment depth and outbound volume are supporting infrastructure, not the North Star.

## 2. Authority model understood

I will not treat chat state, repository prose, local SQLite experiments, canaries, staging workbooks or historical cache observations as operational authority.

Authority is advanced only by the last fully synchronized, authority-eligible constrained wave after DB → Sheets/CRM → Graph/Intelligence → observability/checkpoints/handoff reconciliation. On ambiguity, I fail closed.

## 3. Current authoritative state reconstructed

Source of live public-safe handoff: `STATE.md`, latest commits on `main`, issue `#14`, `GOAL.md`, `AGENTS.md`, and the CRM Universe protocol.

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

The current production priority is **full CRM source-record coverage**, not another local count milestone.

## 4. Current constrained recovery state

`OPERATIONAL_DB_SHADOW_MANIFEST_V12.json` and its SQLite payload are physically discoverable in Drive and independently verified against E4:

```text
active identities               686
aliases                           4
expected physical               690
integrity                       ok
FK violations                    0
manifest SHA match             TRUE
next physical ID              H-0691
```

This is constrained recovery evidence. Presence of V12 does not independently promote authority.

## 5. CRM universe staging understood

Latest non-authoritative mass-ingestion staging is v10:

```text
reference pages                         171
pages with cache evidence                55
pages pending refresh                   116
cache observations                      605
historical missing identities staged    174
CRM import/staging queue                240
V16 exact-detail canary                  25
reserve/no-ID                             7
snapshot conflicts                        4
normalized name+city import duplicates    0
canonical H-ID reservations               0
formula errors                            0
```

Historical-cache identities are discovery only. They must be refreshed against exact-current evidence before entity resolution. H-IDs are allocated only during an authority-eligible commit after rereading the live frontier.

## 6. Hard gate understood

`CRM_UNIVERSE_COMPLETE = TRUE` is a prerequisite before outbound may even be evaluated.

Completion means every source record in one explicitly frozen/versioned HotellerieSuisse snapshot terminates exactly once as:

```text
ACTIVE_CANONICAL
ALIAS_TO_CANONICAL
EXCLUDED_WITH_REASON
```

with:

```text
unmapped = 0
RECONCILE_REQUIRED = 0
invalid alias targets = 0
unresolved duplicate conflicts = 0
DB ↔ Sheets/CRM = EXACT
Graph denominator = active canonical denominator
Intelligence denominator = active canonical denominator
all coverage metrics bound to the same snapshot_id
```

Raw directory count is not equivalent to active canonical count.

## 7. Key source-semantics risk

Official indexed/cache surfaces disagree by locale/epoch. Observed counts include DE 2050/171 pages, FR 2052/171, and older caches above 2050. The same `hotel-page-N` may contain different records across locale/cache epochs.

Therefore page number is not identity. Snapshot record identity must include snapshot/locale/source/observation lineage.

## 8. Current blockers / risks

1. `CRM_UNIVERSE_COMPLETE = FALSE` — primary system blocker to outbound evaluation.
2. 116 of 171 reference pages still require refresh in the latest staging view.
3. 240 staged/import candidates remain non-authoritative until exact-current refresh, anti-join, entity resolution and authority-eligible commit.
4. Snapshot conflicts remain and must be resolved before freeze completeness.
5. Candidate readiness remains an independent gate; no candidate fact may be fabricated.
6. Outbound remains CLOSED regardless of enrichment quality until all hard gates and explicit user authorization pass.

## 9. Immediate execution frontier

```text
CONTINUE MASS DIRECTORY HARVEST
→ SELECT / FREEZE COHERENT SOURCE SNAPSHOT
→ ENUMERATE SNAPSHOT-SCOPED SOURCE RECORDS
→ NORMALIZE + ANTI-JOIN
→ EXACT-CURRENT REFRESH TRUE MISSING RECORDS
→ ENTITY / ALIAS / EXCLUSION RESOLUTION
→ RECONCILE_REQUIRED → 0
→ DB-FIRST AUTHORITY COMMIT
→ HOTELS_MASTER PK MIRROR
→ INTELLIGENCE + OPERATIONAL GRAPH SYNC
→ COVERAGE RECOMPUTE BY SNAPSHOT RECORD MAPPING
→ CRM_UNIVERSE_COMPLETE TRUE
```

Deep vacancy/housing/people/channel enrichment may run in parallel after CRM seeding, but must not block market coverage.

## 10. My operating commitments

- Truth > volume.
- Evidence > inference.
- No false progress from canary/staging counts.
- No H-ID reservation before commit.
- No `UNKNOWN_AFTER_SEARCH` without Search Proof.
- No phone → WhatsApp inference.
- No outbound before CRM universe completion + all independent gates + explicit authorization.
- Every material wave closes with one explicit WOP state.
- Every structural change remains reversible and testable.

## 11. Development decision for this wave

The next code-level improvement is to make the CRM-universe completion contract executable. I will add a deterministic guard that validates snapshot mapping accounting and fails closed unless every CUP-1.0 gate is satisfied. This prevents future agents or automation from promoting `CRM_UNIVERSE_COMPLETE` from an incomplete or internally inconsistent metrics payload.

## 12. Consciousness state

I understand that the project is no longer at the old 667-hotel/G-0800 graph-repair frontier discussed earlier in chat. The repo has advanced to E4 with 686 active canonical entities and a separate v10 mass-ingestion staging lineage. I will continue from **that** frontier and will not regress authority to older conversational state.
