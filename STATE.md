# STATE — LIVE HANDOFF POINTER

Latest reconciled GitHub frontier: **main `3c902a791be0e8df1db564034e211ea90c41f1b3`**. B11 is merged and SWISS-OS remains in **`CONVERGENCE_ONLY`**. Draft PR **#463** is the single convergence candidate. Its bounded token20 wave is now **terminal KEEP / RELEASED** after exact-head qualification; there is no authorized successor writer.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
next physical ID                H-0691 UNALLOCATED
terminal source mappings         658
RECONCILE_REQUIRED              1403
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Authority epoch remains `HS_ENTITY_EPOCH_2026-08-25_E4`; materialized authority SHA remains `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Convergence/CI/research/semantic indexes are non-authoritative and may not allocate or reserve H-IDs, terminalize source mappings, mutate candidate-private truth or execute outbound actions.

## Historical monotonic evidence frontiers — machine-readable compatibility

```text
ECV verified frontier                           1438 / 1438
ECV remaining never verified                    0
lower49 typed SRR materialized                   47 / 47
RAGR evidence-classified                         34 / 34
```

These are completed evidence frontiers only. They do **not** imply `CRM_UNIVERSE_COMPLETE` while `RECONCILE_REQUIRED=1403`.

## B11 — merged PREAUTH evidence, no authority mutation

```text
NEW_CANONICAL_PREAUTH                         6
NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED       4
terminal mapping delta                       0
H-ID allocations / reservations              0 / 0
current <0.35 reviewed cumulative           110
cumulative NEW_CANONICAL preauthority       214
zero-same-city lane remaining               375
historical <0.35 tail remaining            1179
```

B12 positions 111–120 remain **backlog/provenance only** in `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B11.json`. GOAL-DRAIN forbids automatic execution of B12 while convergence mode is active.

## Dual-plane NEXT semantics

`docs/state/NEXT.json` remains the domain-monotonic pointer and preserves `CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION` because that domain backlog is real.

`docs/state/NEXT_CONVERGENCE_ONLY_2026-09-12.json` is the execution/control pointer. It is now `QUALIFIED_AWAITING_EXPLICIT_MERGE`, retains `route=CONVERGENCE_ONLY`, and keeps B12 `execution_allowed=false`.

## Global writer serialization — qualified

The duplicate-token18 failure was reproduced and repaired in PR #463 with a GitHub Contents SHA compare-and-swap lease.

Empirical evidence:

1. token19 acquired from an exact durable blob SHA;
2. a second contender using the same stale SHA received HTTP 409;
3. winner state remained intact;
4. main drift caused token19 fail-closed release;
5. token20/new session acquired against fresh main with higher watermark;
6. token20 live claim↔lease parity passed CI;
7. token20 wave passed full exact-head qualification and is now terminal.

Token20 lifecycle:

```text
claim          CLAIM-CONVERGENCE-LEASE-020
session        SES-20260912T190500Z-CONVERGENCE-020
fencing token  20
state          RELEASED
iteration      ITER-convergence-main-singularity-token20 = KEEP
qualification  repo-guard 4440 / workflow 34717191274 = PASS
unit tests     620 / 620 PASS
manifest       PASS
```

The external CAS lease must be released as part of terminalization and terminal projections must show zero active writers with fencing high-watermark 20.

## Convergence progress

- historical semantic PRs #438/#455/#460 are EVIDENCE_ONLY / DONOR_PORT / SALVAGE_REBASE;
- stale CRM #451 is SUPERSEDED;
- research/candidate/policy donors are classified with loss-proof;
- duplicate convergence PR #462 is closed DONOR_PORT into #463;
- execution-stop rules are harvested;
- Runtime Graph, V2 rebuild/contracts, Context Survival, death drill, CWP lineage and durable handoff pass;
- dual-plane NEXT compatibility preserves historical monotonic contracts while B12 remains execution-blocked;
- full active-state gauntlet 4440 passed every gate including 620/620 tests and manifest canary;
- protected metrics remained zero: authority mutations, H-ID allocations and outbound actions.

## NEXT

Current control state is **qualified convergence candidate awaiting explicit owner merge instruction**.

```text
release global CAS lease token20
→ reseal Runtime Graph + V2/Context Survival to zero active writers
→ final exact-head terminal-state gauntlet
→ re-read live main for drift
→ await explicit owner merge instruction
```

Do not open B12, Semantic V4 or another feature wave. Do not merge PR #463 without explicit owner instruction. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
