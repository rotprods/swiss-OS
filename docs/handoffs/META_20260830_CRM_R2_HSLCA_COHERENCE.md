# META HANDOFF — CRM R2 HSLCA COHERENCE

Generated: 2026-08-30T22:00:00Z  
Project: `SWITZERLAND_JOB_OS`  
Checkpoint: `CRM_UNIVERSE_COMPLETE`  
Parent main: `b0ec94f4a13fb7c24d39454439d9792d90bb7e46`  
Authority: `HS_ENTITY_EPOCH_2026-08-25_E4` / `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`

## Decision

The highest-value safe bottleneck is now **R2 coherent member-directory acquisition**, not further terminal mapping against the historical 2061-record substrate.

The exact source artifact from GitHub Actions run `33206402141` was recovered and inspected. Its materialized 2061 records are real source evidence, but its own manifest is explicit:

```text
capture_mode      LIVE_PARTIAL
coverage_claim    PARTIAL
coverage_complete FALSE
records           2061
pages captured    172
violations        REPORTED_RECORDS_UNRESOLVED
                  PAGE_COUNT_DRIFT:171,172
PCF               FAIL_CLOSED
```

The run crossed a provider pagination epoch while crawling. PCF correctly rejected the capture as a coherent complete member-directory manifest. Therefore the 2061 substrate remains useful for historical anti-join/review, but it cannot be promoted to `coverage_complete`, cannot independently satisfy the member-directory side of SSR-1.0, and cannot authorize exclusions or terminal mappings merely because a current entity is absent from it.

A deterministic scan of the 24 RAGR `IN_SCOPE_NO_SOURCE_MATCH` rows found **0 exact name+city matches** in that partial substrate. Current HotellerieSuisse detail evidence nevertheless exists for multiple rows, including Work Life Residence, Hotel Eggishorn, Crans Montana Suites, Drei Berge Hotel and Hotel Du Commerce. This is consistent with a capture coherence/scope problem and reinforces the fail-closed decision.

## Bounded capability unlock

The HSLCA workflow is changed only to make the existing safe acquisition route invokable by a main-branch request artifact:

```text
request path   docs/state/source/HSLCA_LIVE_CAPTURE_REQUEST.json
branch         main only
surface        HotellerieSuisse member-directory / de
parallelism    1
page delay     1 second
retry policy   bounded existing policy
concurrency    one live HSLCA capture lane
```

The shorter sequential delay stays above the HSLCA protocol's 0.5-second default while reducing the exposure window that caused the 20-minute prior crawl to cross a page-count epoch. No parallel crawler, CAPTCHA bypass, authentication bypass or anti-bot circumvention is introduced.

The request is fail-closed and pins the pre-merge main SHA plus the unchanged E4 authority tuple. On a push-triggered execution, the workflow rejects the request if the event's prior main SHA differs from the pinned SHA.

## Safety / authority boundary

```text
authority advanced              FALSE
canonical H-ID allocations      0
canonical H-ID reservations     0
H-0691                           UNALLOCATED
CRM_UNIVERSE_COMPLETE            FALSE
OUTBOUND                         CLOSED
send_allowed                     0
irreversible external actions    0
```

This wave is `COMPLETE_READ_ONLY`. A successful future HSLCA run is still source evidence only. It does not advance E4 authority.

## NEXT

`R2_HSLCA_COHERENT_MEMBER_DIRECTORY_RECAPTURE`

Acceptance requires one single-locale current capture with a complete coherent page set and `coverage_complete=true`. If it succeeds, immediately validate the artifact, recompute the 24-row exact-source anti-join, and then choose between:

1. SSR-1.0 if a capture-valid discover.swiss `dsod-hs` manifest is available; or
2. the CUP member-directory fallback mass anti-join/staging route while preserving `AUTHORITY_ADVANCED=FALSE` and zero H-ID allocation until an authority-eligible reconciliation transaction exists.

If the new live capture again reports page/count drift, do not normalize the drift away. Persist the exact run/artifact diagnostics and route to the next provider-safe acquisition strategy.

## Recovery inputs

- `docs/state/source/HSLCA_R2_COHERENCE_BLOCKER_2026-08-30.json`
- `docs/state/source/HSLCA_LIVE_CAPTURE_REQUEST.json`
- source artifact `9700376482`
- source run `33206402141`
- RAGR disposition `docs/state/RAGR34_POST_REVIEW_DISPOSITION_WORKSET_2026-08-30.json`
- `docs/state/NEXT.json`
- Drive `HOTELS_MASTER/HOTELS_V2`

**Verify live main ancestry and E4 authority tuple before any new material wave.**
