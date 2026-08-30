# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-08-30T22:25:00Z**. Verified main parent: **`b0ec94f4a13fb7c24d39454439d9792d90bb7e46`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Live Drive `HOTELS_V2` re-read confirms `H-0690` is the physical frontier and `H-0691` is absent/unallocated. No staging, cache, canary, RAGR, SRR, ECV, HSLCA or GitHub artifact is authoritative merely because it is structurally valid or current-looking.

## CRM source / mapping frontier

```text
partial HSLCA substrate records/pages    2061 / 172
partial substrate records SHA             62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2
candidate records                         1438
ECV exact-current                         1438 / 1438
ECV verified frontier                     1438 / 1438
ECV remaining never verified                 0
pre-authority terminal source mappings     658
unique canonical targets                   656
RECONCILE_REQUIRED                        1403
reverse authority source gaps               34
RAGR evidence-classified                   34 / 34
RAGR IN_SCOPE_NO_SOURCE_MATCH              24
```

Source-key conservation for the historical partial substrate remains `658 + 1403 = 2061`. Those counts are preserved for lineage; they are **not** a claim that the 2061-record member-directory capture is coherent or complete.

The 1438-row candidate export and completed 1438/1438 ECV frontier remain deterministic historical lineage from that partial substrate. They are valid pre-authority work products, but must not be reinterpreted as proof that the current member-directory universe is complete.

## Critical R2 correction — 2061 capture is partial, not coverage-complete

The exact source artifact from GitHub Actions run `33206402141`, artifact `9700376482`, was recovered and inspected. Its own manifest states:

```text
capture_mode        LIVE_PARTIAL
coverage_claim      PARTIAL
coverage_complete   FALSE
materialized        2061 records
observed pages      172
capture violation   REPORTED_RECORDS_UNRESOLVED
capture violation   PAGE_COUNT_DRIFT:171,172
PCF result           FAIL_CLOSED
```

The prior live crawl crossed a pagination epoch. The partition-count finalizer correctly rejected the capture with `capture has non-count violations: PAGE_COUNT_DRIFT:171,172`.

Therefore:

- the 2061 rows remain usable as historical/read-only anti-join and review substrate;
- they are not a coherent complete member-directory manifest;
- they are not independently SSR-1.0 directory-coverage eligible;
- absence from that substrate is not authority for exclusion, deactivation or terminal mapping.

A deterministic exact name+city scan of all 24 RAGR `IN_SCOPE_NO_SOURCE_MATCH` rows against the recovered 2061 records returned **0 exact matches**. Current HotellerieSuisse identity evidence exists for multiple such rows, strengthening the decision to repair source acquisition before terminal reconciliation.

Public-safe evidence is persisted in `docs/state/source/HSLCA_R2_COHERENCE_BLOCKER_2026-08-30.json`.

## Capability / provider boundaries

Available now:

```text
GitHub read/write/branch/PR/CI       YES
GitHub Actions artifacts/logs        YES
Drive native Sheets read/write       YES
web current-source research          YES
File Library read                    YES
File Library write                   NO
```

Hard provider/authority boundaries remain:

```text
discover.swiss runtime key                 ABSENT
discover.swiss capture-valid dsod-hs       ABSENT
SSR-1.0 structured side                    BLOCKED ON ABOVE
durable DB-first E4 provider egress        BLOCKED_FILE_REFERENCE_DO_NOT_REPEAT
```

Native Sheets capability does not permit a Sheets-first authority promotion. Exact constrained DB → Sheets → Graph/Intelligence → observability reconciliation is still mandatory for any later authoritative write.

## Current bounded execution wave

A fail-closed live capture request is staged at:

`docs/state/source/HSLCA_LIVE_CAPTURE_REQUEST.json`

The HSLCA workflow is being updated through the required branch → tests → PR → CI → adversarial review → merge path so that a change to that request on `main` launches a **single-lane, sequential, bounded** German member-directory recapture. It uses a 1-second page delay, one concurrent capture lane and existing bounded retry/backoff semantics. This is source acquisition only; it cannot allocate/reserve H-IDs, mutate authority or open outbound.

## NEXT

Execute **`R2_HSLCA_COHERENT_MEMBER_DIRECTORY_RECAPTURE`**.

Acceptance:

```text
one coherent locale/surface epoch
coverage_complete = TRUE
missing pages = 0
record/detail identity validation = PASS
AUTHORITY_ADVANCED = FALSE
H-ID allocations/reservations = 0
OUTBOUND = CLOSED
send_allowed = 0
```

On success, immediately validate/download the fresh artifact, recompute current source identity/anti-join (including the RAGR24 set), then continue into SSR-1.0 only if a capture-valid discover.swiss manifest exists; otherwise continue the provider-neutral member-directory fallback staging route without authority promotion.

On repeated provider page/count drift, persist the exact diagnostics and choose the next provider-safe acquisition route. Never normalize drift away to manufacture `coverage_complete=true`.

Recovery inputs and the exact blocker are in `docs/state/NEXT.json`, `docs/state/source/HSLCA_R2_COHERENCE_BLOCKER_2026-08-30.json` and `docs/handoffs/META_20260830_CRM_R2_HSLCA_COHERENCE.md`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
