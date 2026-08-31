# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-08-31T00:38:20Z**. Verified bootstrap main: **`02dad1a5bd82219b34430b5fd1cee3ee088642b6`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

Live Drive `HOTELS_V2` was re-read in this activation: `H-0690` remains the physical frontier and `H-0691` is absent/unallocated. The native `HOTELS_MASTER` file is `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`, last observed modified `2026-08-30T21:30:11.606Z`.

No staging, cache, canary, review, source-acquisition or CI artifact is authority merely because it is current or structurally valid. Any future authority wave must remain DB-first and reconcile every required plane before promotion.

## Current coherent HotellerieSuisse source universe

The prior partial HSLCA substrate has been superseded for **current source identity** by a coherent complete member-directory capture:

```text
snapshot_id                    HS-MEMBER-DE-33339392661
GitHub Actions run             33339392661
artifact_id                    9740219406
pages                          172
records                        2061
coverage_complete              TRUE
records_sha256                 b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404
```

Current source projection is persisted in `docs/state/CRM_CURRENT_SOURCE_MAPPING_PROJECTION_33339392661.json`. Current renamed Gonten lineage is persisted in `docs/state/CRM_CURRENT_GONTEN_ECV_SRR_LINEAGE_33339392661.json`.

The superseded artifact `9700376482` / run `33206402141` remains historical lineage only and must not be reused as the current coverage authority.

## CRM mapping frontier

```text
exact current ACTIVE matches             623
reviewed exceptional mappings carried     35
terminal source mappings                 658
unique canonical targets                 656
RECONCILE_REQUIRED                      1403
reverse authority/source gaps             34
canonical H-ID reservations                0
H-ID allocations                            0
```

The two Gonten renames (`Huus Bären 1602`, `Huus Löwen 1878`) were explicitly re-anchored to their new current source keys and their prior `NEW_CANONICAL` pre-authority reviews were reconfirmed. They remain `RECONCILE_REQUIRED`; no H-ID was allocated or reserved.

Source conservation remains `658 + 1403 = 2061`.

## Open P0 execution program

- **#240** — close the 2061-source CRM universe and reach authority parity.
- **#239** — batch-safe terminal source resolver / deterministic review semantics.
- **#14** — API-first structured source-universe acquisition and reconciliation.

Issue #12 (native Sheets in-place writer) is resolved. Drive native Sheets read/write is available and canary-verified, but this does not authorize Sheets-first promotion.

## Capability / provider frontier

Available now:

```text
GitHub read/write/branch/PR/merge       YES
GitHub CI / Actions artifact read        YES
Drive native Sheets read/write           YES
Drive recovery artifact creation         YES
web current-source research              YES
File Library read                        YES
File Library write                       NO
```

Provider/authority boundaries:

```text
discover.swiss runtime subscription key          ABSENT
capture-valid discover.swiss structured manifest ABSENT
SSR-1.0 structured route                         BLOCKED ON ABOVE
durable DB-first E4 provider egress               BLOCKED_FILE_REFERENCE_DO_NOT_REPEAT
```

These boundaries do **not** block productive CRM work: the 1403 unresolved current member-directory records can continue through bounded deterministic SRR/entity-resolution review.

## NEXT

Execute **`CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION`**.

Operating rules:

```text
immutable current source keys
current evidence for every identity decision
exact URL / exact normalized identity before any similarity review
similarity may nominate candidates, never autobind
no canonical H-ID allocation or reservation from staging
no authority advancement from source/cache/canary/CI state
OUTBOUND = CLOSED
send_allowed = 0
```

Structured discover.swiss acquisition/SSR remains the secondary route and should be resumed immediately when a runtime subscription key produces a capture-valid manifest. Authoritative cross-plane reconciliation remains deferred until a genuine DB-first E4 egress route is recovered and the selected authority batch independently passes all promotion gates.

Exact recovery inputs, blockers and resume semantics are in `docs/state/NEXT.json` and `docs/handoffs/META_20260831_CRM_CURRENT_REBASE.md`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
