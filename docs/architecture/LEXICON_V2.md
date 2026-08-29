# CANONICAL LEXICON V2 — SWITZERLAND_JOB_OS

Version: **LEX-2.0**  
Authority: semantic contract  
Owner: Architecture / Knowledge Graph  
Last updated: 2026-08-30

The following terms are normative. Unqualified uses of overloaded words are invalid in authority-sensitive artifacts.

| Term | Canonical definition | Deprecated/ambiguous use | Anti-example |
|---|---|---|---|
| `PROPOSED` | Designed or requested; not implemented | ready, done | A plan described as working code |
| `IMPLEMENTED` | Code/configuration exists at a named revision | complete | Code exists but has not executed |
| `EXECUTED` | Ran against declared input/environment | tested | Fixture standing in for runtime |
| `VERIFIED` | Named invariant/test passed with persisted evidence | looks good | CI claimed without run/artifact |
| `EMPIRICALLY_QUALIFIED` | Repeated production-like evidence satisfies a threshold | proven forever | One successful canary |
| `BLOCKED` | Typed dependency prevents the scoped transition | impossible | Preferred route unavailable while fallback exists |
| `DEGRADED_EXTERNAL` | External capability unavailable; safe fallback may continue | system down | Sheets unavailable but research route open |
| `SUPERSEDED` | Historical object remains immutable but is not current | silently replaced | Rewriting old state as current |
| `AUTHORITY` | Source allowed to determine one scoped canonical fact | latest file | Newer cache outranking constrained state |
| `AUTHORITY_CEILING` | Maximum mutation/claim power of an event/session/artifact | permission | Research event allocating H-ID |
| `CANARY` | Bounded reversible candidate execution; cannot advance authority alone | pre-production truth | Valid local DB called canonical |
| `STAGING` | Prepared non-authoritative data awaiting gates | imported | Staging rows assigned permanent IDs |
| `CURRENT` | Fresh relative to declared TTL, observed time and source scope | recently seen | Cached search result with no scope |
| `EXACT` | Deterministic unique match under a named contract | close enough | Similarity used as identity |
| `COMPLETE` | All scoped DoD and gates pass | count target reached | Resolution called known-value coverage |
| `READY` | All prerequisites for one named transition pass | usable | Candidate lane missing truth/assets |
| `EVENT` | Immutable causal envelope describing something that occurred | editable log row | Status row rewritten in place |
| `COMMAND` | Requested intent that may produce events/outcomes | successful event | Request treated as mutation success |
| `STATE` | Reducer output at a named watermark/revision | history | Prior truth lost during update |
| `PROJECTION` | Deterministic read model from named sources/reducer | authority | Graph summary changing hotel truth |
| `CONTEXT_PACK` | Bounded digested recovery cache with freshness assertions | memory | Chat context assumed current |
| `SESSION` | Globally unique execution identity with lifecycle/agent | chat | Reusing ID across waves |
| `CLAIM` | Declared ownership of resource/semantic scope | intention | Two writers silently editing same contract |
| `LEASE` | Time-bounded claim authorization | permanent lock | Dead agent retaining write right |
| `FENCING_TOKEN` | Monotonic token rejecting stale lease holders | timestamp | Old writer accepted after takeover |
| `WAVE` | Smallest bounded material transaction under WOP | turn | Response with no persisted identity |
| `META_CYCLE` | MEP loop selecting/chaining bounded waves | daemon | Claiming continuous background execution |
| `NODE` | Typed graph entity with stable ID/lifecycle | row | Important object existing only in prose |
| `EDGE` | Typed directed relation with provenance/validity | link | Correlation treated as causation |
| `HYPEREDGE` | Multi-participant relation with explicit roles | paragraph | Decision impact hidden in narrative |
| `EVIDENCE` | Persisted observation supporting a scoped claim | URL | URL without extraction/time/scope |
| `FACT_CLAIM` | Assertion with explicit authority, confidence and provenance | fact | Inference presented as observation |
| `UNKNOWN_AFTER_SEARCH` | Resolved search process with valid Search Proof and no known value | negative | No housing inferred from no page |
| `TERMINAL_MAPPING` | Frozen source record ends as canonical, alias or evidenced exclusion | matched | `RECONCILE_REQUIRED` called complete |
| `RECOVERY_EQUIVALENCE` | Same logical state/topology within declared tolerance | byte-identical DB | Equal SQLite states rejected for byte difference |
| `OUTBOUND` | Irreversible employer-facing action plane | draft | Generating copy equated with sending |
| `RELEASE_CANDIDATE` | Scoped artifact passes its stated assurance gates | production ready | Foundation build called operational cutover |

## Semantic collision rules

1. `verified` always names contract and evidence.
2. `complete` always names scope and DoD.
3. `active` always names entity/state machine.
4. `current` always names TTL, observed time and source scope.
5. `authority` always names concept and boundary.
6. `graph` always distinguishes Operational Graph, Project Memory Meta Graph or projection.
7. `real-time` means synchronous reconciliation before authoritative wave closure unless an actual daemon is proven.
8. Similarity can generate candidates but never grant identity authority.
9. `foundation implemented` cannot be shortened to `V2_FINAL`.
10. `PASS`, `FAIL`, `SKIPPED`, `CANCELLED`, `NOT_RUN` and `NOT_APPLICABLE` are never interchangeable.
