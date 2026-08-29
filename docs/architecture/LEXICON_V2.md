# CANONICAL LEXICON V2 — SWITZERLAND_JOB_OS

Version: **LEX-2.0**  
Authority: semantic contract  
Owner: Architecture / Knowledge Graph  
Last updated: 2026-08-30

The terms below are normative. Unqualified uses of overloaded words are invalid in authority-sensitive artifacts.

| Term | Canonical definition | Deprecated / ambiguous aliases | Anti-example |
|---|---|---|---|
| `PROPOSED` | Designed or requested; not yet implemented | ready, done | A plan described as working code |
| `IMPLEMENTED` | Code/configuration exists at a named revision | complete | Code exists but has not executed |
| `EXECUTED` | Ran against declared inputs/environment | tested | A unit fixture standing in for runtime |
| `VERIFIED` | Named invariant/test passed with persisted evidence | looks good | CI mentioned without run/job/artifact |
| `EMPIRICALLY_QUALIFIED` | Repeated production-like evidence satisfies declared threshold | proven forever | One successful canary |
| `BLOCKED` | A typed dependency prevents the scoped transition | impossible | Preferred route unavailable while fallback exists |
| `DEGRADED_EXTERNAL` | External capability is unavailable; safe fallback may continue | system down | Native Sheets unavailable but read-only work exists |
| `SUPERSEDED` | Historical object remains immutable but is no longer current | deleted, replaced silently | Rewriting old state to appear current |
| `AUTHORITY` | Source allowed to determine a scoped canonical fact | latest file | A newer cache outranking constrained state |
| `AUTHORITY_CEILING` | Maximum mutation/claim power an event/session/artifact may exercise | permission | Research event allocating an H-ID |
| `CANARY` | Bounded, reversible candidate execution that cannot advance authority alone | pre-production truth | Valid local DB called canonical |
| `STAGING` | Non-authoritative prepared data awaiting gates | imported | Rows assigned permanent IDs |
| `CURRENT` | Fresh relative to a declared TTL/source scope | recently seen | Search-cache age without observation time |
| `EXACT` | Deterministic unique match under the named contract | close enough | Fuzzy similarity used as identity |
| `COMPLETE` | All scoped DoD/gates pass, not merely count target | finished | 100% resolution presented as known-value coverage |
| `READY` | All declared prerequisites for one named next transition pass | usable | Candidate lane missing required truth/assets |
| `EVENT` | Immutable causal envelope describing something that occurred | log line | Editable status row |
| `COMMAND` | Requested intent that may produce events/outcomes | event | Treating request as successful mutation |
| `STATE` | Current reducer output at a named event watermark/revision | history | Losing prior truth during update |
| `PROJECTION` | Deterministic read model derived from named sources/reducer | authority | Graph summary changing hotel truth |
| `CONTEXT_PACK` | Bounded digested recovery/read cache with freshness assertions | memory | Chat context assumed current |
| `SESSION` | Globally unique execution identity with lifecycle and owner agent | chat | Reusing a session ID across waves |
| `CLAIM` | Declared ownership of resource/semantic scope | intention | Two writers editing the same contract silently |
| `LEASE` | Time-bounded claim authorization | lock forever | Stale agent retaining write rights |
| `FENCING_TOKEN` | Monotonic token rejecting stale lease holders | timestamp | Old writer accepted after takeover |
| `WAVE` | Smallest bounded material execution transaction under WOP | turn | A conversation response with no persisted identity |
| `META_CYCLE` | MEP coordination loop that selects and chains waves | daemon | Claiming continuous background execution |
| `NODE` | Typed graph entity with stable ID and lifecycle | row | Important object only in prose |
| `EDGE` | Typed directed relation with provenance/validity | link | Unqualified correlation treated as causation |
| `HYPEREDGE` | Queryable multi-participant relation with participant roles | paragraph | Decision impact hidden in narrative |
| `EVIDENCE` | Persisted observation supporting a scoped claim | source URL alone | URL without extraction/time/scope |
| `CLAIM_FACT` | Assertion whose authority/confidence/provenance are explicit | fact | Inference presented as observation |
| `UNKNOWN_AFTER_SEARCH` | Resolved search process with valid Search Proof and no known value | negative | “No housing” because no page found |
| `TERMINAL_MAPPING` | Frozen source record ends as canonical, alias or evidenced exclusion | matched | `RECONCILE_REQUIRED` called complete |
| `RECOVERY_EQUIVALENCE` | Same logical state/topology within declared tolerance | byte-identical SQLite | Different SQLite bytes failing despite equal rows/schema |
| `OUTBOUND` | Irreversible employer-facing action plane | draft | Generating a message equated with sending |

## Semantic collision rules

1. `verified` always names the contract and evidence.
2. `complete` always names the scope and DoD.
3. `active` always names the state machine/entity type.
4. `current` always names TTL, observed time and source scope.
5. `authority` always names concept and boundary.
6. `graph` always distinguishes Operational Graph, Project Memory Meta Graph or projection.
7. `real-time` means synchronous reconciliation before authoritative wave closure unless an actual daemon is proven.
8. Similarity is candidate-generation evidence only; it cannot grant identity authority.
