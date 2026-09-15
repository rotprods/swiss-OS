# EXECUTION LEASE PROTOCOL — GLOBAL WRITER SERIALIZATION

Version: **ELP-2.1**  
Status: **CONVERGENCE CANDIDATE / TOKEN19+ ENFORCEMENT**  
Authority effect: **ORCHESTRATION ONLY — NO DOMAIN OR OUTBOUND AUTHORITY**

## 1. Purpose

SWISS-OS requires a globally serialized writer lease for every material writer at fencing token **19 or higher**.

The historical rule

```text
read main fencing watermark
→ choose max + 1
→ create a private branch claim
```

is not an atomic acquisition protocol. Two branches can read the same watermark and independently claim the same token while each remains internally deterministic.

That exact failure occurred with CRM PR #459 and Semantic Runtime PR #460: both started from `dcf70473…`, observed `active_claims=[]` and watermark `17`, and independently selected token18.

A branch-local claim remains required lineage, but for token19+ it is **not sufficient ownership evidence**.

## 2. Fixed durable lease slot

The one global lease projection lives at:

```text
repository: rotprods/swiss-OS
branch: coordination/execution-lease
path: docs/state/execution-leases/current.json
```

This fixed ref/path is intentionally not a per-agent branch. Every writer competes on the same mutable object.

The projection contains:

```text
schema_version
generation
fencing_high_watermark
active_lease
last_lease
last_transition
```

`fencing_high_watermark` survives release and prevents token reuse.

## 3. Compare-and-swap law

Every mutation reads the current GitHub blob SHA and updates the file through the GitHub Contents API while supplying that exact SHA.

GitHub therefore provides the compare-and-swap primitive:

```text
READ blob SHA S
→ derive candidate from state at S
→ PUT candidate with expected SHA S
```

If another writer commits first, the stale writer receives HTTP `409`/`422` and MUST:

1. treat its write as uncommitted;
2. re-read live state;
3. downgrade to read-only or typed recovery;
4. never blind-retry the same writer mutation.

There is no valid state in which both stale contenders become writers.

## 4. Empirical concurrency proof

During token19 convergence qualification on 2026-09-12:

1. the lease file was initialized with blob SHA `704a88cedbada5a163fda0918f84ce64b7c67db4`;
2. the convergence writer acquired token19 using that SHA and GitHub accepted the mutation;
3. a controlled second contender attempted a conflicting acquisition using the same old SHA;
4. GitHub rejected it with HTTP `409` — `current.json does not match 704a88…`;
5. the valid token19 lease was read back unchanged.

This is the required empirical theorem for issue #54:

```text
two contenders from identical durable state
→ exactly one CAS winner
→ loser cannot overwrite winner
```

Unit/adversarial tests preserve this behavior independently of the provider probe.

## 5. Lease identity

An active lease binds:

```text
project_id
lease_id
owner_agent_id
run_id
session_id
wave_id
acquired_at
expires_at
parent_main_sha
authority_epoch
fencing_token
state
idempotency_key
mutation_allowed
```

`lease_id` is deterministically derived from the idempotency identity.

A material claim at token19+ must match the live lease on at least:

```text
agent_id == owner_agent_id
session_id == session_id
fencing_token == fencing_token
base_sha == parent_main_sha
preconditions.authority_epoch == authority_epoch
```

The live lease must be unexpired and `ACTIVE`.

## 6. Admission and terminalization semantics

### No active lease

A new writer may acquire only when:

- parent SHA equals canonical main;
- authority epoch equals canonical authority epoch;
- requested fencing token is strictly greater than the durable high-watermark.

### Same live holder

The same owner/run/session/wave/parent/epoch/token may renew before expiry. Renewal preserves identity and token.

### Foreign live lease

A foreign activation receives:

```text
READ_ONLY_FALLBACK
writer_allowed = false
```

It may continue safe non-mutating work; it may not acquire canonical/material writer authority.

### Expired lease

The expired holder may not resurrect the same run/session. Takeover requires:

```text
new run_id
new session_id
strictly higher fencing_token
current parent SHA
current authority epoch
```

The takeover itself is still a CAS mutation and can have only one winner.

### Release

Only the exact active holder may release. Release:

- sets the lease terminal;
- clears `active_lease`;
- stores the released lease as `last_lease`;
- preserves/increases `fencing_high_watermark`;
- prevents same-token resurrection.

### Terminalization parity — mandatory

Token21 exposed a second real defect during the 2026-09-13 cemetery sweep: the branch claim was committed as `RELEASED` and branch projections showed zero active writers, but the fixed global lease remained `ACTIVE / mutation_allowed=true` until TTL expiry because the terminalization workflow never called the external lease release.

Therefore **claim terminalization is not lease terminalization**.

A writer may be declared `COMPLETE` only after all of the following are durable and read back:

```text
claim.state = RELEASED (or other valid terminal state)
latest heartbeat/session = terminal
Runtime Graph / V2 active writer projection = zero for that session
coordination/execution-lease.active_lease = null
coordination/execution-lease.last_lease = released holder
fencing_high_watermark >= released token
last_transition.kind = RELEASE
```

The zero-claim state itself MUST read the fixed global lease slot. The following state is a P0 violation even when it is fail-closed:

```text
active_claims = []
AND active_lease != null
```

A terminalization workflow may persist branch terminal state before calling `wave_lease_guard.py release`, but it MUST NOT report success/COMPLETE until release and post-release readback succeed. If the process dies in that window, recovery must classify the surviving lease as `ORPHAN_GLOBAL_LEASE`/terminalization-incomplete and fail closed. If the lease expires before recovery, only a new run/session with a strictly higher token may take over.

A successful terminalization must allow a legitimate successor to acquire `token+1` immediately; waiting for the old TTL to expire is evidence of an incomplete terminalization.

## 7. CI enforcement

`repo-guard` runs `scripts/execution_lease_live_guard.py`.

For active claims with `fencing_token >= 19`, CI reads the fixed live lease directly from GitHub and fails closed on:

- no lease;
- expired lease;
- agent/session/token mismatch;
- claim base SHA vs lease parent mismatch;
- authority epoch mismatch;
- lease high-watermark trailing the active claim;
- unavailable live readback.

For **zero active claims**, CI still reads the fixed live lease and fails closed when:

- live readback is unavailable; or
- `active_lease` is non-null (`GLOBAL_LEASE_WITHOUT_ACTIVE_CLAIM`).

Claims below token19 are historical/legacy and are not retroactively required to have used ELP-2.x.

## 8. Runtime interface

Use:

```text
python scripts/wave_lease_guard.py status
python scripts/wave_lease_guard.py acquire ...
python scripts/wave_lease_guard.py release ...
```

`GITHUB_TOKEN` is read from the environment only and is never persisted or printed.

A CAS conflict is a normal concurrency outcome, not a retry hint.

## 9. Authority boundary

The lease answers only:

```text
which material writer, if any, owns the current global mutation slot?
```

It does **not** authorize:

- hotel/CRM authority promotion;
- H-ID allocation or reservation;
- candidate-private truth mutation;
- application submission;
- Gmail mutation;
- outbound communication.

All existing domain, evidence, privacy, human-approval and outbound gates remain independent.

## 10. Recovery contract

A zero-context agent must:

1. read current `main`;
2. replay claim/event lineage;
3. read the fixed lease projection and its blob SHA even when branch projections report zero active claims;
4. validate TTL, holder, parent, epoch, high-watermark and claim↔lease terminalization parity;
5. fail closed on contradiction;
6. only then perform a material mutation.

Deleting or bypassing the lease branch does not grant ownership. Missing/invalid lease state for token19+ is a typed P0 until reconstructed safely.

A remote branch/ref is provenance only. It is never sufficient evidence that an agent is alive or owns writer authority.

## 11. Definition of Done

```text
same-snapshot two-contender test = one winner exactly
CAS stale writer = rejected
foreign live writer = read-only fallback
same-holder pre-expiry renewal = PASS
expired same-session resurrection = REJECTED
expired new-session higher-token takeover = PASS
release = terminal
released token reuse = REJECTED
stale parent = REJECTED
stale authority epoch = REJECTED
CI live claim↔lease parity = PASS
zero active claims + active global lease = REJECTED
zero active claims + active_lease null = PASS
terminal workflow release readback = PASS
successor token+1 immediately after release = PASS
crash between branch terminalization and lease release = FAIL_CLOSED / RECOVERABLE
claim_collisions = 0 for token19+ candidates
```
