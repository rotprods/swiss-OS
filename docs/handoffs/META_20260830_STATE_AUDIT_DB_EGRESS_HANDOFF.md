# META HANDOFF — 2026-08-30 STATE AUDIT / DB EGRESS RECOVERY

**Authority:** continuity and recovery only; this handoff does not advance hotel authority.  
**Wave:** `WAVE-20260830-STATE-AUDIT-HANDOFF-01`  
**Execution mode:** `RECOVERY_RECONCILE`  
**Closure:** `COMPLETE_READ_ONLY`  
**Graph impact:** `META`  
**Observed at:** `2026-08-30T08:23:03+02:00`  
**Audit-start main:** `69fb96168479b210379d83937e8bf041944da450`  
**Reconciled main:** `3afe2ef55acdc41b82f7899dec5bf9e7f7f40f6a`  
**Authority epoch:** `HS_ENTITY_EPOCH_2026-08-25_E4`  
**Logical authority revision:** `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`

A successor must **VERIFY LIVE TRUTH BEFORE EXECUTION**. This document records a checked recovery frontier; it is not a substitute for current `main`, current claims, the constrained authority transaction, or provider authorization.

## Read order

1. `GOAL.md`
2. `AGENTS.md`
3. `docs/operations/META_EXECUTION_PROTOCOL.md`
4. `docs/operations/WAVE_OPERATING_PROTOCOL.md`
5. current `STATE.md`
6. current `docs/state/NEXT.json`
7. current `docs/state/v2/active-claims.json`
8. `docs/recovery/CRM_E4_DURABLE_EGRESS_MEP_FALLBACK_2026-08-30.json`
9. `docs/recovery/DB_EGRESS_CAPABILITY_GAUNTLET_2026-08-30.json`
10. `docs/recovery/STATE_AUDIT_HANDOFF_2026-08-30.json`

## Verified GitHub ancestry and continuity

- Audit parent `main` is `69fb96168479b210379d83937e8bf041944da450`.
- PR #340 was adversarially reviewed and merged into the audit-start parent. It persists the copy-only V13→E4 reconstruction and fail-closed egress evidence.
- During review, PR #342 advanced `main` to `3afe2ef55acdc41b82f7899dec5bf9e7f7f40f6a`. Its two-file delta upgrades the existing CRM E4 fallback to v1.1, adds the deterministic text-capsule failure, and makes no authority change. The handoff branch reconciled that merge before final CI.
- `STATE.md` and `docs/state/NEXT.json` still carry parent `c0168050e659290a0f171cc69ad6c00d5b918c4a`. That SHA is a verified ancestor: the audit-start parent is 70 commits ahead and the reconciled `main` is 73 commits ahead.
- The shared mutable pointer paths are inside the active token-5 resource claim. This audit deliberately did **not** rewrite `STATE.md`, `NEXT*`, or `docs/state/v2/**`.
- The latest DB recovery artifacts supplement the recovery strategy only. They do not release the active claim, allocate an H-ID, or advance authority.

## Binding concurrency state

GitHub currently binds:

```text
claim_id          CLAIM-CRM-PIE050-LOWER49-005
fencing_token     5
state             ACTIVE_UNTIL_EXPLICIT_RELEASE_OR_SUPERSESSION
scope             PIE_050_LOWER_49_PROVIDER_IDENTITY
authority ceiling PREAUTH_REVIEW_ONLY_NO_CANONICAL_MUTATION
```

A remote branch exists:

```text
state/crm-pie050-close-token5-srr-token6-20260830
head f00430437a17adec97f73b188ad341dac94a1c32
```

It is 15 commits ahead and 18 behind the reconciled `main`, has merge base `11a528dd1584b3606fed83356c006065e9785778`, and has no PR. It is **not current authority**, does not release token 5, and does not validly acquire token 6. Reconcile or supersede it from fresh `main`; never merge it blindly.

No matching token-5 row was found in Drive `AGENT_WORK_LEASES` or `CLAIMS_LEDGER_V2`. That absence does not weaken GitHub's active claim.

## Verified operational authority and CRM frontier

```text
physical HOTELS rows             690
active canonical                 690
persisted alias edges              0
next physical ID                 H-0691 UNALLOCATED
source snapshot                  HS-MEMBER-DE-33206402141
source records / pages           2061 / 172
candidate records                1438
ECV exact-current                1438 / 1438
terminal source mappings          657
unique canonical targets          656
RECONCILE_REQUIRED               1404
RAGR reverse gaps                  34
lower-similarity tail              49
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                        0
```

The control plane was re-read directly:

- `HOTELS_V2` reaches `H-0690`; `H-0691` is absent.
- `H-0610`, `H-0624`, `H-0629`, and `H-0630` are `CANONICAL_CURRENT_RECONCILED`.
- Each repaired PK has an L1 `HOTEL_INTELLIGENCE_V1` row.
- Operational Graph contains HOTEL and HOTEL_INTELLIGENCE nodes plus `HAS_INTELLIGENCE` edges for the repaired entities.
- `GRAPH_EDGES_V2` contains zero `ALIASES_TO` edges.
- `CHECKPOINT_REGISTRY` remains L4 `105/690` and L9 `0/690`.
- ENTRY, HYBRID, CREATIVE, and PORTAL all remain `send_allowed=0`.

## Durable DB recovery boundary

The exact Drive parent is readable:

```text
file_id             1rIL6x_bmBoCbxVSAGFvdjoKnUqSX3YnT
name                switzerland_job_os_operational_shadow_v13.sqlite
size                3,059,712 bytes
SHA-256             0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
integrity_check     ok
foreign-key errors  0
hotel rows          690
hotel_alias rows    4
```

A disposable copy was repaired deterministically by restoring the four affected PK states and removing the four invalid alias rows. The result is:

```text
exact E4 SHA-256    70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
size                3,059,712 bytes
integrity_check     ok
foreign-key errors  0
hotel rows          690
hotel_alias rows    0
```

The source V13 file was not mutated.

The exact E4 bytes are reproducible, but no durable E4 binary has been published through the current connector. The following generated-local-file routes all failed before publication with `BLOCKED_FILE_REFERENCE`:

1. Drive copy followed by raw update from the reconstructed local SQLite.
2. Direct Drive raw upload of the reconstructed SQLite.
3. Native-document import of a deterministic gzip+base64 recovery capsule.

The failure is not SQLite MIME-specific. Do not spend another wave retrying local-path upload/import variants. The next attempt must change capability class to a provider-accepted durable file reference or another explicitly approved recoverable authority-artifact bridge.

This means:

```text
control-plane E4 semantics      VERIFIED
exact E4 reconstruction        VERIFIED
durable E4 binary publication  BLOCKED
fresh DB-first promotion       NOT ELIGIBLE
```

Never overwrite V13 while solving this boundary. Publish a new artifact, verify exact hash/integrity/FK/restore, then run a fresh atomic cross-plane transaction.

## Structured acquisition boundary

SSR-1.0 remains provider-blocked:

```text
discover.swiss Infocenter key        ABSENT
capture-valid structured manifest    ABSENT
SSR-1.0                               BLOCKED
```

The coherent HotellerieSuisse member snapshot and exact-current evidence remain a qualified fallback/recovery input, not API-equivalent discover.swiss authority. Never persist the subscription key in GitHub, Drive manifests, logs, or recovery packets.

## Open program work and quarantines

Primary GitHub program issues remain:

- #240 — close the 2061-source CRM universe and reach authority parity.
- #14 — structured discover.swiss acquisition / source-scope contract.
- #239 — batch-safe terminal source resolution; reread against the newer 657/1404 frontier before use.

Drive contains active entity/channel quarantines that remain independent of the DB egress blocker:

- `ISS-043` / `H-0658`: stale or repurposed domain.
- `ISS-044` / `H-0039`: wrong canonical website/careers mapping.
- `ISS-045` / `H-0136`: geography/entity conflict.

No `SYSTEM_ISSUES` row yet records `BLOCKED_FILE_REFERENCE`; this handoff and its machine attestation are the current public-safe typed recovery record. Do not infer that the blocker is absent merely because the Sheet row is missing.

## Pull-request hygiene

- PR #341 contains a valid additive DB-egress gauntlet, but its branch diverged after #340. Its exact artifacts are carried forward by the fresh audit branch/PR and #341 should be closed as superseded after merge.
- Graph-V2 PRs #314, #317, #318, #319, #320 and #287 are based on older ancestry. Do not merge them solely because GitHub reports a mergeable state; perform semantic supersession/rebase review first.
- PRs #275, #135, #137 and #139 are stale or conflicting and must not be merged blindly.

## Ordered NEXT

### Route 1 — primary P0 recovery

Acquire a capability that returns a provider-accepted durable file reference, or another approved recoverable bridge. Publish a **new** exact E4 SQLite artifact; do not overwrite V13. Require:

```text
SHA-256 = 70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
integrity_check = ok
foreign-key violations = 0
physical hotels = 690
hotel_alias rows = 0
restore/replay = PASS
```

Then reconstruct fresh GitHub ancestry, active claims and every authority plane before running the existing DB-first cross-plane promotion/reconciliation checklist.

### Route 2 — token-5 coordination

While token 5 remains active, continue only disjoint read-only recovery, provider acquisition or QA. When token 5 is explicitly `RELEASED` or `SUPERSEDED` on fresh `main`, reconcile the stale token-6 branch and continue the special SRR decisions from current authority. Similarity alone may never terminalize a source.

### Route 3 — structured source

When discover.swiss credentials become available:

```text
structured capture
→ capture-valid manifest
→ member-directory scope reconciliation
→ SSR-1.0
```

Do not persist the secret. Do not claim API equivalence from the member-directory fallback.

### Route 4 — CRM closure

After any independently qualified terminal decisions, recompute source-key conservation, terminal mappings, RAGR and authority eligibility. `CRM_UNIVERSE_COMPLETE` remains false until all 2061 frozen source records terminate exactly once, `RECONCILE_REQUIRED=0`, reverse gaps are zero, and affected planes reconcile exactly.

## Recovery inputs

```text
GitHub reconciled main   3afe2ef55acdc41b82f7899dec5bf9e7f7f40f6a
GitHub audit-start main  69fb96168479b210379d83937e8bf041944da450
authority epoch          HS_ENTITY_EPOCH_2026-08-25_E4
logical authority SHA    70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6
Drive V13                1rIL6x_bmBoCbxVSAGFvdjoKnUqSX3YnT
Drive recovery doc       17qlWRTTXc44jTAkuZRI5ZYWoZZEQUCb0d6uqy0fbaWs
Drive HOTELS_MASTER      1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w
source Actions artifact  9700376482
candidate artifact       9718866661
active claim             CLAIM-CRM-PIE050-LOWER49-005 / token 5
```

## Hard locks

```text
AUTHORITY_ADVANCED             FALSE
HOTELS_MASTER mutations        0
terminal mapping delta         0
H-ID allocations               0
canonical ID reservations      0
H-0691                         UNALLOCATED
CRM_UNIVERSE_COMPLETE          FALSE
OUTBOUND                       CLOSED
send_allowed                   0
irreversible external actions  0
```

Never reserve canonical IDs from staging. Never promote from canary/cache state. Never treat an unmerged branch as claim authority. Never perform a Sheets-first authority mutation.
