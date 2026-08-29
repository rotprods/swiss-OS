# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T18:47:52Z**. Reconstructed parent main SHA: **`f8d496870c8696c42b5e80fb794d1bdcaa85003a`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
ASR-1.0                         EXACT
HOTEL_INTELLIGENCE_V1           690 / 690
Graph HOTEL / INTEL / edges     690 / 690
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging/materialization/ECV/review/cache/canary remain non-authoritative. Native HOTELS_MASTER was reread this activation: H-0690 is present and H-0691 is absent.

## CRM universe / authoritative mapping frontier — unchanged

```text
source pages / records              172 / 2061
ACTIVE_MATCH / TRUE_MISSING          623 / 1438
effective terminal mappings         627
RECONCILE_REQUIRED                  1434
reverse authority/source gaps        66
candidate records                   1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
ECV verified frontier              1438 / 1438
ECV remaining never verified          0
ECV pending requeue                   0
```

The mapping counters above remain authoritative until review decisions are actually transferred through SRR/source-resolution and, where required, later authority commit. Diagnostic projections below MUST NOT replace them.

## Recovery inputs — materialized this activation

The complete qualified member-directory fallback snapshot is recoverable from Actions artifact `9700376482`: 2061 records, records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`. It is coherent fallback evidence and is **not** SSR-1.0 API equivalence.

The complete current candidate export is recoverable from workflow run `33266739167`, artifact `9718866661`, artifact digest `d58c57c5a83cd2ff740f0ec900163f5c7aa795b032045cf9d30ffd194733465e`: 1438 records, records SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`.

A live HOTELS_MASTER-derived active canonical catalog contains 690 rows and hashes to `091a2b1d4f95bc0035135c848104666cf9fca5c4a9e1d691a8a6e16b20e52b99` under the current deterministic projection.

## CMRQ-1.0 bounded pre-authority review — compiled, not applied

Recomputed CMRQ against the current 1438 candidates and 690 active canonicals:

```text
same-city pairs evaluated           10271
queue source records                   16
queue pairs                            16
multi-target source records             0
queue SHA  06d550e3be5bc12e32e67d2d89f6000e1b882b3e3bcacf4e049e4b851f79b11a
review proposals: MATCH_EXISTING       15
review proposals: NEW_CANONICAL         1
reverse-gap-closing match proposals    14
```

The full evidence-backed review packet is persisted privately in Drive document `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. Public-safe summary: `docs/state/CRM_RECON_REVIEW_WAVE_2026-08-29.json`. Meta Graph delta: `docs/state/META_GRAPH_DELTA_CRM_RECON_REVIEW_2026-08-29.json`.

These are **explicit review proposals only**. They allocate no canonical ID, mutate no authority plane, and have no terminal mapping effect until accepted/rejected through SRR-1.1/source-resolution validation.

A diagnostic bidirectional exact normalized name+city reconstruction covers 624 active canonicals and reproduces the current 66 reverse gaps. If and only if the 14 gap-closing CMRQ reviews are accepted, the projected reverse gap count becomes 52. That projection is non-authoritative.

## NEXT — SRR-1.1 review transfer, then bounded reverse-gap evidence review

1. Apply or reject the 16 CMRQ explicit reviews through the SRR-1.1/source-resolution contract while preserving exact-current evidence checks.
2. Recompute source mapping conservation and reverse authority/source gaps from the resulting candidate state.
3. Execute a bounded evidence-only RAGR review over the remaining reverse gaps; do not auto-bind fuzzy matches.
4. Continue CP-R01/CP-R02 until every ambiguous decision is explicit and `authority_batch_ready = TRUE`.
5. Only then consider bounded authority promotion, subject to SSR-1.0 and fresh cross-plane gates.

SSR-1.0 remains blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current without claiming API equivalence. Issue #240 is the execution program; issues #239 and #14 govern resolver safety and source-scope completion.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. Private current review: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. File Library remains cold recovery and may lag GitHub/Drive state.
