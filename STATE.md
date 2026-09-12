# STATE — LIVE HANDOFF POINTER

Latest reconciled GitHub frontier: **main `3c902a791be0e8df1db564034e211ea90c41f1b3`**. B11 is merged and SWISS-OS is in **`CONVERGENCE_ONLY`**. The only live material convergence lane is draft PR **#463** on `convergence/main-singularity`, currently owned by `CLAIM-CONVERGENCE-LEASE-020` / global fencing token **20** under the bounded authority ceiling `CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY`.

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

These completed evidence frontiers remain monotonic historical facts. Preserving them in the live handoff prevents a later convergence pointer from appearing to regress already-completed work:

```text
ECV verified frontier                           1438 / 1438
ECV remaining never verified                    0
lower49 typed SRR materialized                   47 / 47
RAGR evidence-classified                         34 / 34
```

`pending_requeue=0` remains represented in the durable `NEXT.json` ECV frontier. These completed evidence frontiers do **not** imply `CRM_UNIVERSE_COMPLETE`; operational reconciliation remains incomplete at `RECONCILE_REQUIRED=1403`.

## B11 — merged PREAUTH evidence, no authority mutation

B11 (`CURR-U1403-B11`) reviewed operational zero-city positions 101–110 with 10/10 current evidence:

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

The four accommodation-granularity cases preserve EGR semantics and forbid conventional-hotel coercion. Erlebnisland Grizzlybär preserves the announced end-2026 temporal risk. Brand/operator/group relationships remain non-identity evidence unless independently proven.

B12 positions 111–120 are durably preserved as **backlog/provenance only** in `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B11.json`. GOAL-DRAIN forbids automatic execution of B12 while convergence mode is active.

## Dual-plane NEXT semantics

`docs/state/NEXT.json` remains the **domain monotonicity pointer** and therefore continues to expose the unresolved CRM domain route `CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION` for legacy/data-contract consumers.

`docs/state/NEXT_CONVERGENCE_ONLY_2026-09-12.json` is the **control-plane execution pointer** used by Context Survival during this convergence. It says `route=CONVERGENCE_ONLY` and explicitly sets the B12 backlog to `execution_allowed=false`.

This separation is intentional:

```text
domain still incomplete  !=  permission to execute next CRM batch
CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION  !=  B12 authorized now
control plane route = CONVERGENCE_ONLY
```

## Convergence / global writer serialization

The `/aprende` cycle reproduced a real duplicate-token acquisition race: two independent branches read watermark17 and both selected token18. The corrective contract is now being qualified in PR #463.

Global mutable lease slot:

```text
branch: coordination/execution-lease
path:   docs/state/execution-leases/current.json
```

The slot uses GitHub Contents SHA compare-and-swap. Empirical provider evidence already demonstrated:

1. token19 acquired from one exact blob SHA;
2. a second contender using the same stale SHA received HTTP 409;
3. the winner remained intact;
4. when main advanced, token19 was released fail-closed;
5. token20/new session was acquired against fresh main with a higher durable watermark.

Current holder:

```text
claim/session   CLAIM-CONVERGENCE-LEASE-020 / SES-20260912T190500Z-CONVERGENCE-020
fencing token   20
parent main     3c902a791be0e8df1db564034e211ea90c41f1b3
lease expires   2026-09-12T22:05:00Z
```

## Convergence progress

- historical semantic PRs #438/#455/#460 are closed as EVIDENCE_ONLY / DONOR_PORT / SALVAGE_REBASE;
- stale CRM #451 is SUPERSEDED;
- research donors #448/#453 are classified and preserved;
- candidate signature #425 and execution-stop policy #414 are classified SALVAGE_REBASE;
- duplicate convergence PR #462 is closed as DONOR_PORT into #463;
- `EXECUTION_STOP_RULES_V1.md` has been harvested into #463;
- Runtime Graph token20 materialization is deterministic and green;
- global execution-lease live parity passes against the real GitHub CAS lease slot;
- deterministic V2 coordination, V2 contract, forward-event contract, Context Survival, empirical death drill, CWP lineage and durable handoff all pass on the stable convergence tree;
- current exact-head qualification has reached unit tests; compatibility repair preserves historical monotonic domain contracts without reauthorizing B12.

## NEXT

Use `docs/state/NEXT_CONVERGENCE_ONLY_2026-09-12.json` as the current **execution/control-plane** route pointer. Keep `docs/state/NEXT.json` as the durable domain-monotonic pointer.

The next safe sequence is:

```text
emit fresh token20 heartbeat
→ reseal Runtime Graph + V2/Context Survival after compatibility repair
→ run complete exact-head unit tests + manifest canary
→ persist KEEP/BLOCKED iteration receipt + fresh ACTIVE heartbeat/handoff
→ final deterministic reseal + exact-head gauntlet
→ re-read live main for drift
```

Do not open B12, Semantic V4 or any other feature wave. Do not merge PR #463 without explicit owner instruction. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
