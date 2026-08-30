# SWITZERLAND_JOB_OS — CRM SRR SPECIAL TOKEN6 HANDOFF

## Live truth at transition

- parent main observed: `11a528dd1584b3606fed83356c006065e9785778`
- authority: `HS_ENTITY_EPOCH_2026-08-25_E4`
- authority SHA-256: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`
- physical/active canonical: `690 / 690`
- next H-ID: `H-0691 UNALLOCATED`
- source: `2061 / 172`
- candidate export / exact-current: `1438 / 1438`
- terminal source mappings: `657`
- `RECONCILE_REQUIRED=1404`
- RAGR gaps: `34`
- `CRM_UNIVERSE_COMPLETE=false`
- `OUTBOUND=CLOSED`
- `send_allowed=0`

## Completed scope

PIE050 lower49 preauthority classification is complete **49/49**: 47 ordinary weak-similarity collisions have current-public distinctness reviews, and the two special records have relationship classifications. Similarity was never promoted to authority and terminal mapping delta is zero.

Neu-Schönstatt: `MD-33d867e983644585e4b2` has strong current first-party same-property evidence toward active canonical `H-0114`; exact SRR-1.1 transition validation is still required.

Delta Resort Apartments: `MD-7976c173678dc89c9cf0` is a distinct accommodation product with proposed relation `OPERATED_AS_SUBPROPERTY_OF` `H-0220`. Do not collapse identity. The canonical decision surface is `docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json`; the concurrently generated `PIE050_DELTA_RESORT_RELATIONSHIP_CANDIDATE_2026-08-30.json` is supporting evidence only.

Token 5 is released. Token 6 `CLAIM-CRM-SRR-SPECIAL-006` is active and is PREAUTH-only.

## NEXT

1. VERIFY LIVE TRUTH BEFORE EXECUTION: main must be the parent above or a descendant; E4 authority hash must be unchanged; token6 must remain the highest active fence.
2. Compile exact SRR-1.1 review records for Neu and Delta.
3. Neu may be staged as `ALIAS_EXISTING -> H-0114` only if current evidence and active-target validation pass the transfer contract.
4. Delta remains `UNRESOLVED` until canonical entity granularity is explicitly decided. Preserve parent/subproperty relation independently of identity.
5. Do not reserve/allocate H-0691 or any canonical ID from staging.
6. Do not change 657/1404 or RAGR until a separately authority-eligible terminal decision is proven and all cross-plane receipts are available.
7. discover.swiss SSR-1.0 remains blocked by missing Infocenter Open subscription key / capture-valid manifest; use the qualified member-directory + exact-current MEP route without equivalence claims.

Recovery inputs are enumerated in `docs/state/NEXT_META_EXECUTION_2026-08-30.json`.
