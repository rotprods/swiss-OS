# META HANDOFF — CRM PIE050 TOKEN-4 TAKEOVER

authority: coordination/preauthority only
scope: CRM_ENTITY_RESOLUTION_REVIEW / PIE_050_CAPTURED27
owner: AGENT-GPT56SOL-CRM-004
last_updated: 2026-08-29T23:42:36Z
source_revision: 26be95e927d089b79223482703aaf6ffe37be635
supersedes: docs/handoffs/META_20260829_V2_PIE050_SESSION_MIGRATION_V2.md

## Live truth

- main base: `26be95e927d089b79223482703aaf6ffe37be635`
- authority epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`
- authority SHA-256: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`
- active canonical: `690`
- next ID: `H-0691 UNALLOCATED`
- terminal mappings: `657`
- `RECONCILE_REQUIRED=1404`
- RAGR reverse gaps: `34`
- provider evidence .50-.59: `47/47`
- reviewed: `20`; captured/pending: `27`; lower tail: `49`
- `OUTBOUND=CLOSED`; `send_allowed=0`

## Fencing decision

Token 3 (`CLAIM-CRM-PIE050-CAPTURED27-D42F9A`) is `SUPERSEDED`. Its durable branch head `eff73609004e3034d1ba5d6286ef40cda67f9b23` contains session/claim/context migration state but no captured-27 review output. Token 4 (`CLAIM-CRM-PIE050-CAPTURED27-TAKEOVER-004`) is the only active claim for this semantic scope.

Any writer presenting fencing token <=3 is stale.

## Recovery inputs

- SUB03 artifact `9722145032`
- FINAL17 artifact `9722212725`
- source snapshot `HS-MEMBER-DE-33206402141` = 2061 records / 172 pages
- candidate export = 1438; ECV exact-current 1438/1438
- Drive HOTELS_MASTER `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`
- canonical comparison surface = `HOTELS_V2`

## NEXT

Independently compare a bounded subset of the 27 provider-evidence records against current `HOTELS_V2`. Promote only explicit same-property SRR where identity is proven. Distinctness/novelty is nonterminal and cannot decrement `RECONCILE_REQUIRED`. Do not allocate/reserve H-0691. After the 27 frontier closes, continue into bounded targetless PIE waves for the lower-similarity 49.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
