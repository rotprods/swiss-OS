# RAGR-1.0 — Reverse Authority Gap Review

## Purpose

`RAGR-1.0` is a deterministic **review-only** authority→source coverage gate. It runs after source-side entity-resolution has produced a terminal-coverage set and asks the inverse question:

> Which active canonical E4 rows still have no terminal current-source mapping in the frozen source universe?

It does not mutate authority, delete legacy rows, reserve IDs or decide that a canonical is stale/closed/duplicate merely because the current member directory does not map to it.

## Inputs

- frozen source universe records;
- active/inactive canonical catalog snapshot;
- explicit terminal source→canonical coverage rows;
- exact SHA-256 for each input plane;
- source snapshot ID and authority epoch.

Every input hash is recomputed before queue construction. Coverage source keys must exist in the supplied source universe; coverage targets must exist and be active canonicals. Multiple source records may legitimately cover one canonical, but a source key cannot appear twice.

## Queue semantics

For each active canonical not represented in the unique covered target set, RAGR emits one row containing:

- canonical identity;
- read-only authority metadata useful for review;
- count of same-city source records;
- up to three deterministic same-city source suggestions, ranked by a bounded name/token similarity score;
- a reason distinguishing `NO_SAME_CITY_SOURCE_CANDIDATE` from `SAME_CITY_CANDIDATES_PRESENT`;
- `required_action=EVIDENCE_BACKED_REVERSE_GAP_REVIEW`.

Suggestions are search-space reduction only. They are never source mappings.

## Hard boundary

```text
review_only = true
terminal_decision_allowed_from_queue = false
authority_mutation_allowed_from_queue = false
authority_advanced = false
h_id_allocations = 0
canonical_id_reservations = 0
OUTBOUND = CLOSED
send_allowed = 0
```

The queue intentionally forbids `action`, `resolution_action` and `classification` fields. Any eventual classification such as current-directory omission, current-but-renamed property, duplicate canonical, historical/closed property, non-member property, exclusion candidate or unresolved must be supported independently and then pass the appropriate authority reconciliation contract. Absence from a source directory is not deletion evidence.

## Determinism / QA

RAGR:

- validates exact source, catalog and terminal-coverage hashes;
- validates source-key and H-ID uniqueness/boundaries;
- excludes inactive canonicals from the gap denominator;
- computes unique canonical coverage separately from source-mapping count;
- generates only same-city suggestions;
- sorts gap H-IDs and suggestions deterministically;
- hashes the complete review queue;
- fails closed if an input plane drifts or a coverage row points outside the frozen source/active-authority universe.

## Intended production flow

```text
frozen 2061-source universe
+ terminal source→canonical decisions
+ E4 canonical catalog
  -> RAGR-1.0
  -> evidence-backed review of remaining reverse gaps
  -> bounded authority reconciliation only when evidence and all upstream gates permit
```

RAGR cannot make `CRM_UNIVERSE_COMPLETE=true`, cannot satisfy SSR-1.0, and cannot allocate the next H-ID.
