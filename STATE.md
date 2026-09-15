# STATE — LIVE HANDOFF POINTER

Latest reconciled GitHub frontier: **main `3c902a791be0e8df1db564034e211ea90c41f1b3`**. B11 is merged and SWISS-OS remains in **`CONVERGENCE_ONLY`**. Draft PR **#464** is the single convergence candidate. Token25 repaired inherited terminal-lineage ambiguity, passed full active-state qualification, and is now **terminal KEEP / RELEASED** on both Git claim and external CAS lease surfaces. No successor writer is authorized.


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

## Global writer serialization — terminalization + lineage parity proven

The duplicate-token18 collision is protected by the candidate GitHub blob-SHA CAS lease. The later orphan-lease defect was exercised through token24 two-surface terminalization. Token25 then repaired the final PR-wide lineage ambiguity without weakening same-branch fail-closed behavior.

Token25 lifecycle:

```text
claim          CLAIM-CONVERGENCE-TERMINALIZATION-025
session        SES-20260915T082640Z-CONVERGENCE-025
fencing token  25
state          RELEASED
iteration      ITER-convergence-terminal-lineage-token25 = KEEP
active qualify repo-guard 4464 / workflow 34947621820 = PASS
lease release  commit 742472a28bd593f7ff45096e3f3f92bee2d4fd37
lease readback active_lease=null / last_lease=token25 RELEASED / watermark=25
```

COMPLETE was withheld until external release readback. The material lineage guard now ignores inherited terminal provenance from another branch only when exactly one terminal owner belongs to the current PR branch; same-branch and no-match ambiguity remain fail-closed.

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

Current control state is **terminal convergence candidate awaiting final zero-writer gauntlet and explicit owner merge instruction**.

```text
reseal Runtime Graph + V2/Context Survival to zero active writers / watermark25
→ final exact-head terminal-state gauntlet
→ re-read live main for drift
→ await explicit owner merge instruction for PR #464
```

Do not open B12, Semantic V4 or another feature wave. Do not merge PR #464 without explicit owner instruction. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
