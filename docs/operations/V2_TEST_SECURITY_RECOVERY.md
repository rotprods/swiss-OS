# V2 TEST, SECURITY AND RECOVERY MODEL

## Test taxonomy

- unit: pure validators/reducers/hash functions;
- contract/schema: required IDs/types/authority ceilings;
- property-style: deterministic replay/idempotency and ordering invariants;
- integration: Git state files + guard;
- E2E: acquire claim → event → projection → ContextPack → handoff;
- physical runtime: GitHub Actions execution;
- security: malformed booleans, untrusted payloads, public-repo guard;
- concurrency: overlapping claims, fencing takeover, stale writer;
- replay: duplicate and late events;
- recovery: delete projection/cache and rebuild;
- performance: event replay/claim collision only when measured;
- empirical qualification: repeated real agent handoffs;
- death drill: zero-context successor recovers objective/main/claims/blockers/tests/next safe action.

## Escaped-bug corpus

### BUG-V2-001 duplicate bootstrap

Observed: identical architecture bootstrap intent created two GitHub issues in the same session before duplicate detection. Instance was corrected immediately.

Invariant: a material coordination action has a deterministic idempotency key; duplicate key with different event/object ID is rejected/flagged.

Permanent tests: duplicate event ID, duplicate idempotency key, overlapping active claim.

### BUG-HIST-ASR-001 alias row/H-ID drift

Historical issue #89 demonstrated structural SQLite integrity can coexist with semantic identity corruption.

Invariant retained from V1: row offset never authority; alias identity must be stable-identity exact and cross-plane reconciled.

V2 consequence: coordination/projection correctness never substitutes for semantic operational authority.

## Threat model

| Asset | Threat | Boundary | Mitigation | Detection | Recovery |
|---|---|---|---|---|---|
| Hotel authority | stale/unauthorized writer | coordination→operational | authority ceiling + WOP/AAR/ASR | cross-plane gates | rollback/restore |
| Session/claim state | replay/duplicate | tool/Git | idempotency + fencing | V2 guard | supersede/rebuild projection |
| ContextPack | stale/tampered | cache/handoff | main/projection/authority hashes | validation | regenerate |
| Evidence | provider/prompt poisoning | external input | UNTRUSTED_DATA + schema/provenance | evidence validators | discard/reacquire |
| Secrets/PII | public repo leakage | connector/repo | existing repo_guard + public-safe schemas | CI | rotate/remove |
| Outbound | authority escalation | agent/tool | immutable false ceilings + existing outbound gates | CI + runtime gates | suppress/rollback task |

Residual risks:

- Git files do not provide a distributed transaction for multiple concurrent writers; PR/ancestry/fencing discipline remains required.
- Fencing enforcement is initially contract/CI-level, not a remote lock service.
- Event ledger is public-safe project coordination only; private operational/PII events belong in appropriate private authority planes.
- external SSR provider credential remains a domain blocker independent of V2.

## Recovery drill

Coordination recovery acceptance:

1. assume chat, local checkout, ContextPack and graph projections are deleted;
2. read live GitHub main;
3. recover stable goals/architecture + append-only events/claims;
4. validate event/claim schemas;
5. replay coordination reducer;
6. reproduce projection revision or emit drift;
7. generate new ContextPack pinned to current main and authority revision;
8. list active claims/open PRs/blockers/next safe actions;
9. refuse authority mutation until external operational authority is reread.

PASS requires same important coordination topology, blockers and next safe action within declared tolerance.

## Agent-death drill

A zero-context successor must locate within five minutes:

North Star; objective; main SHA; authority revision; event watermark; active claims; open PRs; verified/unverified work; tests/evidence; blockers/risks; next safe action.

`death_drill()` encodes the minimum machine fields.

## Concurrency gauntlet

- two agents same resource scope;
- same semantic scope but disjoint resources;
- stale claimant after fencing takeover;
- duplicate WORK_STARTED retry;
- main advances after CI;
- ContextPack built before latest event;
- late WORK_COMPLETED after session supersession.

Until executable fencing transitions land, overlapping exclusive claims are a fail-closed review condition.
