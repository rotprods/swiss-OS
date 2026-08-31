# SWITZERLAND_JOB_OS — HISTORICAL REGRESSION 2026-09-01

Status: **AUDITED HISTORY / NON-AUTHORITATIVE**  
Scope: architecture, operational authority, CRM universe, recovery, concurrency, testing, market/application execution.  
Authority: historical evidence only. Current operational truth remains `STATE.md` + live authority reconstruction.

## 1. Purpose

Reconstruct the project as a causal history rather than a sequence of chat decisions. For every major pivot or escaped failure this audit asks:

```text
what existed
→ what failed
→ root cause
→ broken invariant
→ why prior checks missed it
→ repair
→ generalized failure family
→ permanent regression protection
→ residual debt
```

Historical artifacts are never allowed to override current authority. Superseded states remain queryable.

## 2. Historical phases

### H00 — Drive-first operating system

The project began with Google Drive/Sheets as the durable operational plane. The North Star and control-plane concepts already existed before GitHub became the reviewed executable-contract plane.

Risk discovered later: prose, sheets, local databases and chat could each look authoritative without an explicit precedence model.

### H01 — GitHub bootstrap

Commit `21d5264abb80b07f1129ab3d7d08faf772f048cb` bootstrapped the repository from Drive with `GOAL.md`, `STATE.md`, `AGENTS.md`, operating rules, runbook, authority model, public-repository boundary and repository guard.

Key property preserved: Drive/Sheets + constrained DB remained operational truth; GitHub became reviewed system memory/code rather than a replacement operational database.

### H02 — Executable integrity core

The repository acquired executable manifest parsing, constrained SQLite, reconciliation, scheduler/idempotency, CLI and invariant tests. A key semantic correction separated physical lineage rows from active canonical entities.

Escaped assumption: structural integrity was initially treated as stronger evidence of identity correctness than it actually was.

### H03 — State drift / Wave Operating Protocol

Stable documents accumulated mutable frontier values. `README`, `GOAL`, `AGENTS`, architecture docs and `STATE` could disagree.

Commit `5c9bfd6e98b1fe1b55c89d761b478e4a6bb502dc` introduced WOP-1.1 and the rule that `STATE.md` is the only mutable current-state pointer in GitHub. Contract guards were added so stable architecture cannot silently become a second live dashboard.

### H04 — CRM universe becomes a hard pre-outbound gate

The project moved from “reach an intermediate hotel count” to “map one frozen/versioned source universe completely before outbound can even be evaluated.” Historical directory pages proved that page number and global count were unstable across locale/cache epochs.

The system therefore separated source observations, source-record identity, canonical entities and terminal mappings.

### H05 — Structured acquisition / source-scope reconciliation

DSA-1.0 introduced discover.swiss acquisition; SSR-1.0 required exact source-scope reconciliation instead of assuming API count equality meant directory equivalence. MDM/PAB then compiled coherent member-directory evidence and pre-authority bundles.

Provider credential absence became a route blocker, not a global project blocker.

### H06 — Meta Execution / continuous fallback

Commit `62886e4bac48f726603d1a481ee027d0515e4939` introduced MEP-2.0 + durable `NEXT`: reconstruct ancestry/authority/capabilities, choose the highest-value safe route, execute a bounded WOP wave, persist, compute NEXT, and continue. Capability failure became a deterministic fallback problem instead of an idle condition.

### H07 — Alias semantic corruption escape

Commit `41b597a6b4a65c7f0eb728226950eb8b3a925d37` persisted an alias-aware 673/677 state. Later issue #89 proved four persisted alias edges were structurally valid but semantically connected different real-world hotels.

`PRAGMA integrity_check=ok` and FK=0 had not detected the corruption.

Commit `377744d9860e89861f0c80d045d774dcb58eb03b` introduced ASR-1.0; ARR/AAR/SRS generalized copy-on-write repair, replay, cross-plane gate and whole-database postcondition checking. Commit `8f7bde7bcc01f9511f24d616593ec589546976fd` persisted the repaired 690/690/0 authority state.

### H08 — Restore semantics corrected

Binary SQLite SHA equality was previously conflated with logical restore equivalence. The project replaced that with integrity/FK/schema/table-set/row-count and bidirectional `EXCEPT` equivalence. Binary SHA remains transfer identity, not the definition of logical restore success.

### H09 — Exact-current evidence factory

The candidate universe was materialized in deterministic sub-batches. ECV eventually reached 1438/1438. Staging explicitly did not reserve H-IDs and did not advance authority.

Failure family exposed during this phase: packet lineage/hash mismatches and malformed provider-work lineage must fail closed rather than be patched into canonical state.

### H10 — Concurrency / stale-branch fencing

Repeated concurrent branches demonstrated that a green branch can still be stale. Several PRs were deliberately closed as `SUPERSEDED` rather than rebased blindly. Fencing tokens, active claims, fresh-main ancestry checks and CSP-1.0 were introduced.

Core lesson: CI proves the branch contents, not that the branch still owns the right to mutate current state.

### H11 — Context survival

CSP-1.0 made chat/model context disposable cache. Context survival binds current Git ancestry, authority/projection revision, active claims, exact NEXT and content-addressed recovery surfaces. Compaction may optimize context but cannot become project authority.

### H12 — Entity granularity and similarity discipline

Similarity and shared addresses repeatedly produced plausible but unsafe identity collapses. EGR-1.0 separated property identity from operator/group/component relationships. Examples include Delta Resort Apartments/Parkhotel Delta, Overlook Lodge/CERVO, sibling properties, locality variants such as St. Moritz-Bad and Montreux-Territet, and generic hotel-name collisions.

Similarity is now review-space reduction only; it cannot terminalize mappings.

### H13 — Coherent source recapture

A recovered 2061-row directory capture was discovered to be `LIVE_PARTIAL`: page-count drift and unresolved reported counts meant “all rows we saw” was not a coherent frozen snapshot. A fresh recapture produced the coherent current 2061/172 source universe and forced exact lineage transfer for changed Gonten source identities.

Core lesson: materialized count is not source completeness.

### H14 — Terminal mapping / current-source resolution

The system rebuilt exact terminal mappings and anti-joined the unresolved 1403 candidate-side records. Review bands were generated for prioritization only. Current-source B01–B06 then reduced ambiguity with independent evidence while keeping new-canonical findings pre-authority and `H-0691` unallocated.

### H15 — Market/application execution in parallel

A read-only bulk market factory covered the 2061-record source universe and recovered 436 properties with current opening routes. Vacancy-first application semantics and AAG-3.0 were added without opening outbound.

This parallel lane exposed several execution failures that became permanent regression cases: self-referential aggregate hashes, route-level security failures killing a shard, lexical vs numeric shard ordering, GitHub artifact HTTP 503 transport, and Actions inability to create PRs.

## 3. Escaped-bug graph

| ID | Escaped failure | Root cause | Why prior checks missed it | Generalized invariant / repair | State |
|---|---|---|---|---|---|
| HDR-001 | Stable docs disagreed on current frontier | mutable state duplicated in architecture/prose | no mechanical state-free contract | WOP + `system_contract_guard`; `STATE.md` only mutable Git pointer | RESOLVED |
| HDR-002 | 677 physical rows interpreted as canonical 677 despite explicit supersessions | physical lineage conflated with active entity count | counters lacked semantic denominator contract | physical vs active canonical invariant; aliases excluded only when semantically valid | RESOLVED |
| HDR-003 | V12/V13 recovery lineage appeared missing/inconsistent | artifact discovery and prose pointers diverged | recovery depended on narrative/file location assumptions | hash-addressed parent manifests + recovery pointers + direct revalidation | RESOLVED |
| HDR-004 | Blind row-offset writes could target wrong semantic cell | spreadsheet position treated as identity | row offsets passed local write checks | PK-keyed writes only; canary/readback before commit | RESOLVED |
| HDR-005 | Four alias edges linked different real-world hotels | row/ID drift survived PK/FK validity | structural DB checks cannot prove semantic identity | ASR-1.0 semantic alias gate; ARR/AAR/SRS repair family | RESOLVED |
| HDR-006 | SQLite restore judged by binary SHA | physical file layout confused with logical state | SHA was easy to compare and looked strong | logical schema/table/bidirectional row equivalence | RESOLVED |
| HDR-007 | Directory page number/count treated as stable source identity | locale/cache pagination drift | each page looked internally coherent | snapshot-scoped source-record identity; MDM/SSR/PAB | RESOLVED |
| HDR-008 | Staging duplicated V16/reserve/cache identities | evidence lanes anti-joined independently | dedupe precedence was implicit | deterministic staging precedence + normalized name/city QA | RESOLVED |
| HDR-009 | Fresh branches became stale while CI was green | concurrent main advances | CI did not include ownership/ancestry authority | fresh-main recheck + fencing tokens + SUPERSEDED semantics | RESOLVED |
| HDR-010 | Context/handoff could regress after compaction | conversational memory was implicit dependency | no content-addressed recovery contract | CSP-1.0 + durable NEXT + pinned Git blob OIDs | RESOLVED |
| HDR-011 | Pytest-style top-level assertions existed but `unittest discover` did not execute them | test-framework mismatch | files existed and looked like tests | executable unittest conversion; historical regression requires test-run evidence | RESOLVED |
| HDR-012 | Generated E4 SQLite could be reconstructed but not durably egressed | connector file-reference boundary | repeated variants looked like independent solutions | generalized `GENERATED_LOCAL_FILE_REFERENCE_EGRESS_UNAVAILABLE`; strategy retry cap | DEGRADED_EXTERNAL |
| HDR-013 | Source capture had 2061 rows but was not coherent complete | pagination epoch drift | materialized count was mistaken for completeness | PCF/MDM coherent page-set gate and fresh recapture | RESOLVED |
| HDR-014 | Source identities changed across recapture (Gonten) | current provider naming/key changes | prior evidence was correct for old snapshot | exact lineage transfer only on unchanged identity; explicit re-review changed keys | RESOLVED |
| HDR-015 | Similarity/generic names/locality variants risked false aliasing | heuristic similarity overloaded as identity evidence | review score looked decisive | similarity = triage only; independent current evidence + locality/EGR semantics | RESOLVED |
| HDR-016 | Self-referential aggregate hash could never validate | hash recomputed including its own declared digest | manifest format lacked explicit hash domain | hash canonical payload excluding digest field; permanent fixture | RESOLVED |
| HDR-017 | One SSRF-safe URL rejection killed whole vacancy shard | security exception escaped route boundary | security gate was correct but failure isolation was absent | route-level typed rejection; unrelated runtime exceptions still raise | RESOLVED |
| HDR-018 | Recovered shard set failed because filenames sorted lexically (`1,10,2`) | ordering semantics conflated filename and numeric identity | set equality was checked separately from ordered comparison | numeric index normalization + exact-set/cardinality regression fixture | RESOLVED |
| HDR-019 | GitHub artifact HTTP 503 repeatedly killed recovery before research | transient provider transport | retry policy absent at artifact transport boundary | bounded retry/backoff only for GitHub artifact/API transport | RESOLVED |
| HDR-020 | Actions completed data work but failed trying to create a PR | workflow token/permission boundary | publication step was coupled to research completion | Actions persist branch/artifact; interactive orchestrator owns PR creation | RESOLVED |
| HDR-021 | Relationship evidence could collapse distinct subproperties | entity granularity not first-class | identity ontology lacked component/operator edges | EGR-1.0 typed relationships; granularity review before aliasing | RESOLVED |
| HDR-022 | Structured discover.swiss route unavailable without runtime key | external credential boundary | preferred route was initially treated as critical path | MEP provider-neutral fallback; SSR stays blocked, project continues | DEGRADED_EXTERNAL |
| HDR-023 | Current authority/source reverse gaps and unresolved mappings remain | source universe larger/different than E4 | historical CRM was not full source parity | bounded current-source entity-resolution waves + RAGR/EGR + terminal mapping gate | OPEN |
| HDR-024 | Historical/stale open PRs can visually resemble live work | old branches remained open after supersession | GitHub PR state not automatically tied to NEXT/claims | stale-PR hygiene audit; live NEXT/claims outrank branch existence | OPEN_P2 |

## 4. Historical invariants that are now non-negotiable

1. **Authority is not a count.** It is a synchronized, provenance-bearing state transition.
2. **Structural integrity is not semantic identity.** PK/FK/SQLite integrity cannot prove two hotel records represent the same real-world entity.
3. **Page position is never source identity.** Source records are snapshot/provider scoped.
4. **Canary/staging never reserves H-IDs.** Allocation exists only inside an eligible authority transaction.
5. **CI green is not mutation authority.** Main ancestry, active claim/fencing and current authority must be rechecked immediately before merge/write.
6. **Similarity never terminalizes identity.** It only reduces review space.
7. **One route failure must not destroy unrelated evidence work.** Isolation must preserve security boundaries and fail closed on programming faults.
8. **Retries are typed and bounded.** Retry only transient transport/provider classes; change strategy after repeated identical failures.
9. **Tests must be proven executed.** A test file without test-run evidence is not coverage.
10. **Context is cache.** Zero-context recovery must reconstruct NEXT, authority, claims and evidence from durable state.
11. **Outbound is independent.** Market/CRM/application readiness cannot imply send permission.
12. **Historical truth is superseded, never rewritten.** Old counts/decisions remain evidence of what was believed then, not current truth.

## 5. Historical debt still open

### HD-OPEN-001 — CRM terminal parity

Current source universe remains larger than the authority set. Current-source entity resolution must continue until every frozen source record is terminally mapped and reverse authority/source discrepancies are resolved.

### HD-OPEN-002 — Structured SSR credential boundary

The discover.swiss path remains unavailable without a runtime subscription key/capture-valid manifest. This is not a global blocker because provider-neutral member-directory/current-source work remains productive.

### HD-OPEN-003 — Generated-file egress boundary

The historical `BLOCKED_FILE_REFERENCE` failure family is external/runtime-specific. Do not repeat equivalent upload/replace/import strategies unless the provider capability changes materially.

### HD-OPEN-004 — Stale PR hygiene

Old superseded PRs still open should be closed or explicitly marked historical where they no longer match `STATE/NEXT/claims`, to reduce operator ambiguity.

## 6. Regression conclusion

The project improved by converting every major escaped failure into a stricter invariant, typed state, or durable recovery path. The dominant current risk is no longer silent architectural ambiguity; it is the volume and semantic difficulty of completing current-source entity resolution without weakening identity evidence.

The correct continuation is therefore **not another infrastructure rewrite**. It is:

```text
fresh-main + CSP reconstruction
→ execute current B07 source-resolution workset
→ preserve preauthority/NO-H-ID semantics
→ continue bounded current-source waves
→ terminalize only evidence-qualified mappings
→ recompute source/authority gaps
→ cross-plane authority transaction only when all gates pass
```

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
