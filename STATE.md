# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution coordination frontier: **2026-08-30T08:29:00Z**. Current execution parent main SHA: **`804a3ee8ea29e567cb93bc48a46b5cc5f2d8a33f`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, SRET, PIE, cache and canary remain non-authoritative. No canonical ID is reserved from staging/review.

## Source / mapping frontier

```text
source records / pages               2061 / 172
candidate records                         1438
ECV exact-current                    1438 / 1438
ECV verified frontier                1438 / 1438
ECV remaining never verified                   0
pre-authority terminal source mappings       658
unique canonical targets                    656
RECONCILE_REQUIRED                         1403
RAGR reverse authority gaps                  34
explicit SRR deltas                          34
```

PR #344 independently re-proved exact lower49 classification coverage **49/49** from fresh main: 47 ordinary nonterminal distinctness reviews plus two relationship-sensitive cases. PR #345 quarantined the diverged stale token6 transition. PR #346 released token5 and activated fresh token6 for SRR-special preauthority only.

## Coordination / SRR special frontier

Fencing token **6** (`CLAIM-CRM-SRR-SPECIAL-006`) is **ACTIVE** with authority ceiling `PREAUTH_SRR_DECISION_ONLY_NO_CANONICAL_MUTATION`.

- Neu-Schönstatt `MD-33d867e983644585e4b2` is now accepted as a bounded explicit SRR-1.1 pre-authority `ALIAS_EXISTING -> H-0114` mapping. This advances only the pre-authority source overlay `657 -> 658` and `RECONCILE_REQUIRED 1404 -> 1403`; H-0114 was already source-covered, so unique canonical targets remain 656 and RAGR gaps remain 34. Full deterministic 658-row terminal coverage rebuild is pending.
- Delta Resort Apartments `MD-7976c173678dc89c9cf0` remains `OPERATED_AS_SUBPROPERTY_OF -> H-0220`; canonical entity granularity is unresolved, so no identity collapse, NEW_CANONICAL terminal decision, or H-ID reservation is authorized.

## Provider / recovery boundaries

Current discover.swiss documentation still requires an `Ocp-Apim-Subscription-Key` for Infocenter API requests; HotellerieSuisse AccommoDataHub access uses the HotellerieSuisse project selector. No runtime subscription key / capture-valid structured member-directory manifest is available in this activation, so SSR-1.0 remains blocked. The qualified member-directory snapshot plus exact-current verification is a fallback and is explicitly not SSR-equivalent.

The exact E4 SQLite can be deterministically reconstructed from the verified Drive V13 parent, but generated local file-reference egress is unavailable through the current connector (`GENERATED_LOCAL_FILE_REFERENCE_EGRESS_UNAVAILABLE`). Therefore no Sheets-first authority promotion is allowed. Drive/canary/cache state cannot advance authority.

## NEXT

Rebuild exact **658-row** terminal coverage from the immutable 2061-source snapshot plus 34 explicit SRR deltas, require source-key conservation and re-attest RAGR. Then continue bounded unresolved-source review/staging under token6 while probing only materially different provider-accepted DB-egress routes. Do not repeat failed local file-reference upload/replace/import variants. Never reserve H-0691 or any H-ID from preauthority work; keep `OUTBOUND=CLOSED` and `send_allowed=0`.

Recovery inputs and exact blockers are persisted in `docs/state/NEXT.json` and `docs/state/NEXT_META_EXECUTION_2026-08-30.json`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
