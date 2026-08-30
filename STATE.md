# STATE — LIVE HANDOFF POINTER

Latest CRM coordination frontier reconstructed from live GitHub after concurrent Delta relationship waves. Observed parent main SHA for this transition: **`11a528dd1584b3606fed83356c006065e9785778`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, SRET, PIE, cache and canary remain non-authoritative. No canonical ID may be reserved from staging/review.

## Source / mapping frontier

```text
source records / pages               2061 / 172
candidate records                         1438
ECV exact-current                    1438 / 1438
terminal source mappings                    657
unique canonical targets                    656
RECONCILE_REQUIRED                         1404
RAGR reverse authority gaps                  34
```

## PIE050 lower49 — classification frontier closed

The exact lower-similarity queue contains 49 records. Five bounded packets completed current-public distinctness review for **47/47 ordinary weak collisions** without terminalizing from similarity. The two relationship-sensitive records are also classified:

- `MD-33d867e983644585e4b2` Jugend & Familienzentrum Neu-Schönstatt → strong same-property candidate to existing `H-0114` Hostel Neu-Schönstatt; requires exact SRR/authority review.
- `MD-7976c173678dc89c9cf0` Delta Resort Apartments → current evidence supports `OPERATED_AS_SUBPROPERTY_OF` existing `H-0220` Parkhotel Delta, but not identity collapse. Canonical entity granularity remains unresolved.

Two Delta evidence artifacts were produced concurrently from the same parent. The canonical decision surface is `docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json`; `docs/state/PIE050_DELTA_RESORT_RELATIONSHIP_CANDIDATE_2026-08-30.json` is supporting evidence only. Historical artifacts are preserved; neither has authority effect.

```text
lower49 classification              49 / 49
ordinary distinctness reviews       47 / 47
special relationship reviews          2 / 2
terminal mapping delta                    0
terminal mappings                       657
RECONCILE_REQUIRED                     1404
```

Token **5** (`CLAIM-CRM-PIE050-LOWER49-005`) is `RELEASED` after 49/49 preauthority classification. Fresh fencing token **6** (`CLAIM-CRM-SRR-SPECIAL-006`) owns only `SRR_SPECIAL_RELATIONSHIP_MATERIALIZATION_PREAUTH`. Any writer with token <=5 is stale for this lineage.

## Provider / recovery boundaries

SSR-1.0 is still provider-blocked because no discover.swiss Infocenter Open subscription key / capture-valid structured manifest is available. MEP remains the coherent HotellerieSuisse member-directory snapshot + exact-current verification, without API-equivalence claims. Drive is recovery/control-plane projection only.

## NEXT

Under token 6, compile exact **SRR-1.1** review semantics for the two special records. Validate Neu-Schönstatt as an `ALIAS_EXISTING` candidate to active canonical H-0114 only if the SRR transfer contract and exact evidence gates pass. Keep Delta `UNRESOLVED` until entity-granularity authority policy is explicit; preserve the H-0220 relationship as a parent/subproperty edge, not an identity mapping. Only after an evidence-qualified terminal decision changes the mapping frontier may source-key conservation and RAGR be recomputed and an authority transaction evaluated.

`OUTBOUND=CLOSED`, `send_allowed=0`, `H-0691 UNALLOCATED` remain hard locks.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
