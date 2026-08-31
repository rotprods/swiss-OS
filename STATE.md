# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-09-01 current-source entity-resolution B07**. Fresh coordination parent: **`d56593efff5a5947ae736026578176cb315d0535`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

The authoritative ceiling remains E4/690. Source review, web evidence, staging, CI, cache and canary artifacts are preauthority only.

## Current coherent source universe

```text
snapshot                         HS-MEMBER-DE-33339392661
Actions run                      33339392661
artifact                         9740219406
records / pages                  2061 / 172
coverage_complete                TRUE
records SHA256                   b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404
terminal source mappings          658
unique canonical targets          656
RECONCILE_REQUIRED               1403
reverse authority/source gaps      34
```

## Coordination / fencing

Historical regression found that the old token6 lease had outlived its bounded SRR-special scope and still carried stale 657/1404 preconditions. It was explicitly superseded rather than silently reused.

```text
superseded claim    CLAIM-CRM-SRR-SPECIAL-006     token 6
active claim        CLAIM-CRM-CURRENT-B07-007     token 7
session             SES-20260831T222003Z-CRM-B07-007
authority ceiling   PREAUTH_CURRENT_SOURCE_REVIEW_ONLY_NO_CANONICAL_MUTATION
```

Token7 excludes HOTELS authority mutation, H-ID allocation/reservation, outbound execution and discover.swiss authority.

## Entity-resolution frontier — B07 complete

B07 exact source keys are persisted in `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B07_2026-09-01.json`.

All ten records were reviewed against current independent property evidence and canonical collision/granularity risk. Notable safeguards include:

- Hotel Restaurant Hammer vs generic `hotel/restaurant` overlap;
- Nidwaldnerhof vs generic Swiss Quality descriptors;
- Ô Pied-à-Terre preserved as a motel-residence accommodation entity under EGR-1.0;
- Boutique Hôtel Corbetta vs generic Boutique Hotel descriptors;
- Mövenpick Genève vs Mövenpick Lausanne as same-brand sibling properties, not aliases.

Every B07 result remains:

```text
decision                 NEW_CANONICAL_PREAUTH
mapping_state            RECONCILE_REQUIRED
terminal_mapping_created FALSE
H-ID allocations         0
H-ID reservations        0
authority effect         NONE
```

Frontier:

```text
candidate lineage accounted                    1438 / 1438
ECV verified                                    1438 / 1438
current <0.35 reviewed cumulative                 70
cumulative NEW_CANONICAL preauthority             184
historical <0.35 tail remaining                 1219
zero-exact-city lane remaining                   415
terminal source mappings                          658
RECONCILE_REQUIRED                               1403
```

## Historical regression

`docs/audits/HISTORICAL_REGRESSION_2026-09-01.md` and `docs/state/v2/HISTORICAL_DEBT_2026-09-01.json` persist 24 escaped-failure families and their permanent invariants/tests. Six unequivocally superseded historical PRs were closed so stale branches do not masquerade as live work.

## Runtime capability

GitHub/CI, web research and Drive mount recovery are available. The native Google Drive connector degraded during this wave; no authority write was attempted. Structured discover.swiss remains provider-blocked by the absent subscription key/capture-valid manifest. Exact E4 durable generated-file egress remains `BLOCKED_FILE_REFERENCE_DO_NOT_REPEAT`.

## NEXT

Do **not** infer B08 from current similarity. The `<0.35` lane was defined by a pinned historical selection lineage whose scoring semantics differ from later collision review.

Execute:

```text
COMPUTE_CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B08_FROM_PINNED_LINEAGE
→ load original historical lt350000 lineage
→ subtract exact reviewed B01..B07 keys
→ select next ten keys in original deterministic order
→ persist exact B08 NEXT
→ current-source evidence review
```

Durable pointer: `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B07.json`.

Keep `H-0691=UNALLOCATED`, `OUTBOUND=CLOSED`, `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
