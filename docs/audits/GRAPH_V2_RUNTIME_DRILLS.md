# GRAPH V2 — RUNTIME DRILLS

Version: **GRV2-RUNTIME-1.0**  
Status: **EXECUTABLE QUALIFICATION CONTRACT**  
Owner: Recovery Engineer / Agentic Systems Architect / CISO  
Last updated: 2026-08-30

## Objective

Turn the V2 foundation's symbolic guarantees into executable runtime evidence while preserving the operational authority ceiling.

## Drill set

### DRILL-V2-ZERO-CONTEXT-RECOVERY

Input: exact-SHA V2 recovery ZIP only, plus the standalone standard-library verifier.

Execution:

```text
copy bundle + verifier to isolated temp directory
→ run Python isolated mode
→ reject ZIP path traversal
→ verify manifest bytes/SHA for every file
→ verify exact main SHA
→ verify graph/assurance/COS/program/ContextPack
→ replay and hash-check event ledger
→ verify test attestation belongs to exact SHA
→ assert authority/H-ID/outbound locks
→ measure elapsed recovery time
```

Qualification target:

```text
state = PASS
recovery duration <= 300000 ms
20 COS projections
18 tasks / 15 checkpoints
open P0/P1 = 0
authority advanced = false
H-ID allocations = 0
OUTBOUND = CLOSED
send_allowed = 0
```

This qualifies recovery of the V2 architecture bundle. Operational DB/HOTELS_MASTER disaster recovery remains independently governed by domain recovery contracts.

### DRILL-V2-AGENT-DEATH

```text
Agent A opens Session, write Claim and Lease
→ Agent A aborts/dies
→ claims and lease are released/expired
→ Agent B acquires same scope
→ newer FencingToken issued
→ stale Agent A token rejected
```

### DRILL-V2-CONCURRENCY

Two threads race for the same write scope through a lock-protected coordination adapter. Exactly one claim is accepted; the other is rejected. A third non-overlapping write scope remains available in parallel.

This qualifies process-local atomicity. A future distributed registry must run its own network-partition/clock/consensus qualification before replacing the adapter.

### DRILL-V2-EVENT-REPLAY

Build, verify and replay a causal event chain ending in `NEXT_EMITTED`; reject duplicate delivery and preserve the event watermark.

### DRILL-V2-SECURITY

Attack:

- `file://` and insecure HTTP;
- credential-bearing URLs;
- loopback/link-local/metadata/localhost targets;
- non-allow-listed provider host;
- path traversal/absolute/Windows/control paths;
- prompt-injection-like provider text;
- credential patterns and secret-bearing keys.

Provider prose is retained only as untrusted data and grants zero authority.

### DRILL-V2-CRM-NEXT-SHADOW

Consume the repository's real public-safe `docs/state/NEXT.json` and traverse:

```text
NEXT input
→ unique Session
→ READ Claim
→ HELLO / WORK_STARTED
→ authority/source observation
→ evidence digest
→ graph + hyperedge projection
→ assurance event
→ ContextPack
→ NEXT_EMITTED
```

The shadow cannot allocate H-IDs, mutate authority or open outbound. It proves the V2 bridge on the real current work pointer without interfering with CRM production.

## CI binding

Workflow:

`.github/workflows/graph-v2-runtime-drills.yml`

The workflow:

1. checks out the exact SHA;
2. runs repository and stable-contract guards;
3. runs the full test suite;
4. creates SHA-bound test evidence;
5. compiles a fresh foundation bundle;
6. recovers it in an isolated directory;
7. runs death/concurrency/replay/security/CRM-shadow drills;
8. asserts every authority/outbound hard lock;
9. uploads one exact-SHA artifact.

## Acceptance

The runtime-drill PR may merge only when both `graph-v2-guard` and `graph-v2-runtime-drills` pass on the same head SHA and adversarial diff review finds no operational mutation.

After merge, the push workflows must also pass and the exact artifact must be independently downloaded and verified before CP7–CP11 are marked verified.

## Residual uncertainty

- process-local coordination is qualified; distributed coordination is not implemented or required;
- the five-minute target is measured for architecture-bundle recovery, not full operational-store restoration;
- one read-only CRM NEXT shadow proves the bridge, not operational migration;
- CP12 requires repeated measurements rather than a single run;
- CP13/CP14 remain blocked until shadow parity and authority migration gates pass.
