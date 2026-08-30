# STATE — LIVE HANDOFF POINTER

Latest CRM chained Meta Execution coordination frontier: **PIE050 lower49 PREAUTH closeout**. Reconstructed parent main SHA: **`11a528dd1584b3606fed83356c006065e9785778`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
next physical ID                H-0691 UNALLOCATED
terminal source mappings        657
unique canonical targets        656
RECONCILE_REQUIRED             1404
RAGR reverse authority gaps      34
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, SRET, PIE, cache and canary remain non-authoritative. No canonical ID is reserved from staging/review.

## Source / exact-current frontier

```text
source records / pages          2061 / 172
candidate records                    1438
ECV exact-current               1438 / 1438
ECV never verified                        0
```

Pinned recovery artifacts remain Actions `9700376482` (source) and `9718866661` (candidate), plus Drive `HOTELS_MASTER/HOTELS_V2` and source-snapshot recovery projection.

## PIE050 lower49 closeout

Exact lower49 queue: **49**, key-set SHA-256 `66baae0a46a8e1b807855c1ba05746fcb5bdff3779687d5d382dda9859d6f43b`.

```text
ordinary weak-similarity records with current distinctness evidence   47 / 47
relationship-sensitive records classified                              2 / 2
PREAUTH classification total                                           49 / 49
PREAUTH review pending                                                       0
terminal mapping delta                                                       0
H-ID allocations / reservations                                             0 / 0
```

The two relationship-sensitive records remain outside authority:

1. `MD-33d867e983644585e4b2` — **Jugend & Familienzentrum Neu-Schönstatt** → strong same-property candidate for existing `H-0114` **Hostel Neu-Schönstatt**, but only `PROPOSED_ONLY`; requires authority review.
2. `MD-7976c173678dc89c9cf0` — **Delta Resort Apartments** ↔ existing `H-0220` **Parkhotel Delta Wellbeing Resort**. Current evidence proves a same-operator/same-license adjacent-premises subinventory relationship but does not choose canonical entity granularity. Canonical PREAUTH surface is `docs/state/PIE050_DELTA_RESORT_RELATIONSHIP_CANDIDATE_2026-08-30.json`. The compatible later `PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json` is retained as **SUPERSEDED_REDUNDANT_EVIDENCE**, not a second source of truth.

Token 5 `CLAIM-CRM-PIE050-LOWER49-005` is **RELEASED**. Fencing high-watermark remains 5. A fresh claim is mandatory for any successor mutation. DEC-0106 records the closeout and concurrency reconciliation.

A continuity defect was also surfaced: several `docs/state/PIE050_*` artifacts were semantically in token-5 scope but outside its original literal resource glob. Historical scope is not rewritten. Future claims must explicitly enumerate the PIE050 artifact pattern before mutation.

## Provider / authority boundaries

`SSR-1.0` remains provider-blocked: no discover.swiss Infocenter subscription key / capture-valid structured manifest is available. The HotellerieSuisse member snapshot is a coherent MEP recovery source, not discover.swiss API-equivalent authority.

The lower49 PREAUTH scope cannot be promoted under token 5. `SRR-1.1` explicitly separates preauthority resolution from the later bounded authority transaction. Any accepted `MATCH_EXISTING`/alias/new-canonical decision must be followed by deterministic source-mapping rebuild/replay and required DB → HOTELS_MASTER → Intelligence → Operational Graph → observability/recovery reconciliation before authority or CRM completion can advance.

## NEXT

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

1. Reconstruct current `main`, E4 authority, active claims and open PRs.
2. If an explicit authority-eligible entity-resolution claim is available, adjudicate the two special cases only: Neu-Schönstatt identity and Delta canonical granularity. Do not allocate or reserve H-0691 from PREAUTH/staging.
3. If any terminal decision becomes authority-eligible, rebuild the complete 2061-record source mapping, recompute source-key conservation/RAGR, and execute exact cross-plane reconciliation before promotion.
4. Independently, if a discover.swiss Infocenter key becomes available, run structured capture → capture-valid manifest → SSR-1.0 without persisting the credential.
5. Otherwise remain **BLOCKED_EXTERNAL_OR_AUTHORITY** rather than manufacturing a mapping or SSR claim.
