# GRAPH V2 — PRODUCTION ADOPTION

Version: **GRV2-ADOPTION-1.0**  
Status: **CP14 COORDINATION-AUTHORITY GATE**  
Owner: Mission Commander / Authority & Reconciliation Engine  
Last updated: 2026-08-30

## Scope

CP14 adopts V2 as the production coordination, causal-history, ContextPack and assurance architecture for **new material waves**.

It does not replace or silently migrate:

```text
constrained operational DB
HOTELS_MASTER/control-plane authority
Operational Graph domain truth
Intelligence domain projection
frozen source records / terminal mappings
candidate truth
outbound authorization
```

These retain their current domain authority contracts.

## Adoption mode

```text
feature_mode       ENFORCED_FOR_NEW_MATERIAL_WAVES
compatibility_mode LEGACY_DOMAIN_AUTHORITY_PRESERVED
adoption_scope     COORDINATION_CAUSAL_HISTORY_CONTEXTPACK_ASSURANCE
```

A new material wave must acquire a unique Session and scoped Claim; write paths require a Lease/FencingToken; causal events, assurance evidence, ContextPack and NEXT are persisted within the WOP lifecycle.

Existing domain executors can continue through a compatibility bridge while emitting V2 coordination artifacts. A big-bang rewrite is prohibited.

## Required evidence

Exact evidence set:

```text
CP7  zero-context architecture-bundle recovery
CP8  process-local agent-death/takeover
CP9  process-local concurrency/fencing
CP10 defined security/provider-input corpus
CP11 read-only real CRM NEXT shadow
CP12 repeated empirical qualification
CP13 live immutable cross-plane shadow parity
```

Every checkpoint must include:

```text
state
evidence commit SHA
artifact SHA-256
evidence reference
qualified scope
verified ancestry to current main
lineage evidence reference
authority/H-ID/outbound locks
```

## Current-main workflow gate

All must succeed on the exact evaluated `current_main_sha`:

```text
repo-guard
graph-v2-guard
graph-v2-runtime-drills
graph-v2-empirical-qualification
graph-v2-migration-shadow
```

Stale workflow evidence is rejected even if an older revision passed.

## Persistence gate

The exact checkpoint evidence set must be verified on:

```text
GITHUB
LIBRARY
DRIVE
```

Presence alone is insufficient; each surface has an artifact-set digest and evidence reference.

## Concurrency gate

Before adoption:

```text
active conflicting write claims = 0
open conflicting PRs = 0
current STATE/NEXT digests captured
current authority epoch/manifest captured
```

A stale main or changed authority invalidates the adoption candidate and requires reconstruction.

## Rollback gate

Rollback must already be verified conceptually and executable:

```text
stop issuing new V2 leases
release/expire active V2 claims
retain append-only events
restore prior coordination feature flag/bridge
retain all domain authority stores unchanged
append rollback event
rebuild ContextPack and NEXT
```

No rollback deletes causal history or edits hotel/source truth.

## Adoption evaluator

Implementation:

```text
src/swiss_os/v2_adoption.py
scripts/evaluate_graph_v2_adoption.py
```

An accepted candidate produces:

```text
state = ADOPTION_ELIGIBLE
v2_coordination_authority_allowed = true
v2_coordination_authority_activated = false
```

This deliberately separates evidence eligibility from activation.

## Activation

Activation is a fresh-main PR that minimally updates:

```text
AGENTS.md
WOP bridge
mutable STATE/NEXT
V2 adoption event / ContextPack / receipt
```

It must preserve domain authority, pass all V2 workflows on the activation SHA, undergo adversarial diff review, merge, pass main CI, persist recovery to all three surfaces and execute one bounded compatibility-mode material wave.

Only then may the activation receipt state:

```text
ADOPTED_COORDINATION_ONLY
```

The receipt binds:

```text
activation SHA
AGENTS/WOP/STATE/NEXT digests
adoption event hash
ContextPack digest
recovery bundle digest
compatibility-wave evidence
```

## CP14 Definition of Done

```text
complete CP7–CP13 evidence
+ exact-main workflows green
+ GitHub/Library/Drive receipts
+ no conflicting claim or PR
+ rollback verified
+ activation diff merged
+ post-merge workflows green
+ exact activation receipt persisted
+ one compatibility-mode production wave verified
+ zero domain authority mutation
+ zero H-ID allocation
+ OUTBOUND=CLOSED
+ send_allowed=0
```

## Security and privacy

- Public adoption evidence contains no private H-ID map, candidate PII, credentials or raw operational evidence.
- Provider/web/issue/comment content remains untrusted data.
- V2 coordination authority cannot grant domain authority or outbound permissions.
- The public repository guard and stable-contract guard remain mandatory.

## Residual boundaries

- Coordination is process-local until a measured distributed requirement exists.
- CP14 does not imply `CRM_UNIVERSE_COMPLETE` or job-search completion.
- V2 architecture may be final for its declared scope while the operational North Star remains active.

## Outbound

```text
OUTBOUND = CLOSED
send_allowed = 0
```

No architecture or adoption receipt can override the independent outbound gate or explicit user authorization requirement.
