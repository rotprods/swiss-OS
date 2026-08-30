# META HANDOFF — CRM PIE050 LOWER49 TOKEN5 CLOSEOUT

Authority: recovery / coordination handoff only.  
Scope: `CRM_UNIVERSE_COMPLETE` / lower49 provider-identity PREAUTH closeout.  
Source revision: parent main `11a528dd1584b3606fed83356c006065e9785778`.  
Authority epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`.  
Authority SHA-256: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`.

## Zero-context reconstruction

Start with `STATE.md`, `docs/state/NEXT_META_EXECUTION_2026-08-30.json`, `docs/state/CRM_PIE050_LOWER49_CLOSEOUT_33206402141.json`, DEC-0106, active claims and the released token5 claim. **VERIFY LIVE TRUTH BEFORE EXECUTION**; never treat this handoff as fresher than current `main` or authority.

Pinned recovery inputs:

- frozen member snapshot `HS-MEMBER-DE-33206402141`: 2061 records / 172 pages;
- Actions source artifact `9700376482`;
- Actions candidate artifact `9718866661`: 1438 candidates;
- ECV exact-current 1438/1438;
- Drive `HOTELS_MASTER/HOTELS_V2`: 690 canonical rows under E4;
- terminal source mappings 657 → 656 unique canonical targets;
- `RECONCILE_REQUIRED=1404`;
- RAGR reverse authority gaps 34;
- `H-0691` remains UNALLOCATED.

## Lower49 result

The exact lower49 key set is content-bound by SHA-256 `66baae0a46a8e1b807855c1ba05746fcb5bdff3779687d5d382dda9859d6f43b`.

- 47/49 ordinary weak-similarity collisions have current public distinctness evidence in packets 01–05.
- `MD-33d867e983644585e4b2` is a strong same-property candidate for existing `H-0114` but remains `PROPOSED_ONLY` pending authority review.
- `MD-7976c173678dc89c9cf0` is relationship-sensitive relative to `H-0220`: same operator/site/telephone/licence and adjacent premises/subinventory. Evidence proves relationship, not canonical granularity.
- No lower49 source was terminalized in this scope. No H-ID was allocated or reserved.

## Concurrency reconciliation

PR #334 and PR #333 were concurrent compatible Delta evidence waves. #334 merged first and contains the richer granularity-aware artifact `docs/state/PIE050_DELTA_RESORT_RELATIONSHIP_CANDIDATE_2026-08-30.json`; it is the canonical PREAUTH decision surface. The later compatible `docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json` is historical `SUPERSEDED_REDUNDANT_EVIDENCE`. Do not delete either artifact and do not treat both as co-authoritative.

A separate continuity defect was found: token5's semantic scope covered the PIE050 work, but its original literal `resource_scopes` did not enumerate `docs/state/PIE050_*`. Historical claim text is preserved. Future claims must explicitly cover the concrete PIE050 artifact path/pattern before mutation.

## Claim lifecycle

`CLAIM-CRM-PIE050-LOWER49-005`, fencing token 5, is released because the bounded PREAUTH classification scope is complete. `docs/state/v2/active-claims.json` contains no active token5 claim; fencing high-watermark remains 5. Any successor write requires a fresh non-overlapping claim and a token >5 if it continues this coordination lineage.

## Exact blockers

1. **Authority boundary:** SRR-1.1 makes PREAUTH reviews candidates for a later bounded authority transaction. Token5 expressly excluded HOTELS authority mutation and H-ID allocation. The two special cases therefore require a fresh explicitly authority-eligible entity-resolution/terminal-mapping scope before any promotion.
2. **Provider boundary:** discover.swiss SSR-1.0 is still blocked because no Infocenter subscription key / capture-valid structured manifest is available. The HotellerieSuisse member snapshot is a coherent MEP recovery input, not API-equivalent SSR authority.

## NEXT safe route

1. Re-read `main`, active claims, open PRs, E4 authority and Drive control-plane state.
2. If authority eligibility exists, acquire a fresh fenced claim specifically for the two special cases and adjudicate:
   - Neu-Schönstatt same-identity eligibility;
   - Delta entity granularity.
3. If a terminal decision is accepted, rebuild/replay the entire 2061-source mapping, recompute source-key conservation and RAGR, then reconcile DB → HOTELS_MASTER → Intelligence → Operational Graph → observability/recovery before authority promotion.
4. If discover.swiss credentials become available, independently run structured capture → capture-valid manifest → SSR-1.0 without persisting secrets.
5. Otherwise stop as `BLOCKED_EXTERNAL_OR_AUTHORITY`; do not manufacture a mapping, reserve H-0691, advance from staging/cache/canary, or open outbound.

Hard locks remain `CRM_UNIVERSE_COMPLETE=FALSE`, `OUTBOUND=CLOSED`, `send_allowed=0`, authority E4 unchanged.
