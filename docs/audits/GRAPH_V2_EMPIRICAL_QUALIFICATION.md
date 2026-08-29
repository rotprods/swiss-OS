# GRAPH V2 — EMPIRICAL QUALIFICATION

Version: **GRV2-EQ-1.0**  
Status: **CP12 EXECUTABLE CONTRACT**  
Owner: Performance Engineer / Reliability Engineer  
Last updated: 2026-08-30

## Objective

Replace single-run confidence with repeated measurements for the V2 foundation and runtime-drill scope.

The qualification does not benchmark the Swiss hotel data plane, provider latency or full operational disaster recovery. Those remain separate domain SLOs.

## Workload

Each exact-SHA CI qualification performs:

```text
multiple deterministic foundation compiles
multiple isolated zero-context recoveries
multiple complete agent-death/concurrency/replay/security suites
multiple read-only executions over the real public-safe CRM NEXT pointer
```

Default CI sample:

```text
runtime/recovery/shadow iterations = 30
compile iterations                = 7
```

A smaller repeated sample is also exercised in unit/integration tests.

## Measurements

For each workload:

```text
count
minimum
median
mean
p95
maximum
failures
```

Determinism checks:

- compiled graph/context/event/file manifests are identical for identical inputs;
- runtime semantic result shape is stable;
- CRM shadow graph, event watermark and ContextPack are stable for identical inputs;
- every output remains bound to the exact commit SHA.

Concurrency winner identity is not itself required to be deterministic. The required invariant is one accepted overlapping writer, one rejected conflicting writer and preserved non-overlapping parallelism.

## Foundation thresholds

```text
compile p95                       <= 5000 ms
zero-context bundle recovery p95 <= 5000 ms
runtime drill suite p95          <= 2000 ms
CRM NEXT shadow p95              <= 1000 ms
failure count                    = 0
compile semantic variants        = 1
runtime semantic variants        = 1
shadow semantic variants         = 1
```

These are intentionally generous regression thresholds for a standard GitHub-hosted runner. They detect pathological regressions rather than advertise performance guarantees for unrelated infrastructure.

## Fail-closed rules

Qualification fails when:

- the SHA-bound test attestation differs from the target commit;
- any compile/recovery/runtime/shadow iteration fails;
- any p95 threshold is exceeded;
- deterministic build fields diverge;
- result-state semantics diverge;
- any artifact claims authority/H-ID/outbound permission.

## Hard authority boundary

```text
authority advanced = FALSE
H-ID allocations = 0
terminal source mappings changed = 0
OUTBOUND = CLOSED
send_allowed = 0
```

## CP12 acceptance

CP12 may be marked `VERIFIED_FOR_DECLARED_SCOPE` after:

1. PR workflow passes the repeated qualification;
2. adversarial review confirms no operational mutation;
3. PR merges;
4. the main push workflow passes;
5. the exact artifact is downloaded and independently verified;
6. measurements, runner/environment, thresholds and hashes are persisted to GitHub recovery state, Library and Drive.

CP12 does not authorize CP13 migration or CP14 production authority.
