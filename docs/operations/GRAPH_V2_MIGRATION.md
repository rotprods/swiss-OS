# GRAPH V2 — MIGRATION AND AUTHORITY ADOPTION

Version: **GRV2-MIGRATION-1.0**  
Status: **CP13 SHADOW MIGRATION CONTRACT**  
Owner: Migration Architect / Authority & Reconciliation Engine  
Last updated: 2026-08-30

## Objective

Migrate current SWITZERLAND_JOB_OS architecture, coordination and projection semantics into V2 without rewriting or duplicating operational authority.

## Migration state vocabulary

```text
INVENTORY_PROPOSED
INVENTORY_VERIFIED
SHADOW_COMPILED
SHADOW_PARITY_VERIFIED
ADOPTION_ELIGIBLE
ADOPTED_COORDINATION_ONLY
PRODUCTION_AUTHORITY
BLOCKED
SUPERSEDED
```

`SHADOW_PARITY_VERIFIED` is CP13 evidence. It is not CP14 authority.

## CP13 inputs

The migration compiler consumes immutable copies of:

```text
current GitHub source revision
constrained DB artifact
HOTELS_MASTER/control-plane artifact
Intelligence projection
Operational Graph projection
alias semantic state
explicit historical unknowns
current outbound/authority locks
active conflicting write claims
```

The operational inventory remains private. Public output contains only counts, hashes, parity states and authority boundaries.

## Hard entry gates

```text
source revision is exact
source artifacts are immutable copies
constrained DB integrity_check = ok
foreign-key violations = 0
DB physical H-ID set = HOTELS_MASTER physical H-ID set
DB active H-ID set = HOTELS_MASTER = Intelligence = Operational Graph
alias edges agree across DB/HOTELS_MASTER/Operational Graph
ASR state = EXACT | NOT_APPLICABLE
active aliases are excluded from active canonical set
expected authority counts equal physical sets
active conflicting write claims = 0
OUTBOUND = CLOSED
send_allowed = 0
authority/H-ID/outbound preauthorization = false
```

Equal counts are insufficient; PK sets must match exactly.

## Privacy-preserving shadow graph

The compiler creates a private pseudonymous entity reference for every physical H-ID:

```text
ENTITY:HOTEL:sha256(secret_salt + H-ID)
```

The salt is supplied at runtime and never enters public GitHub or public attestations. A private map allows recovery/migration; public artifacts expose only digest/count evidence.

Every physical entity receives a `CROSS_PLANE_ENTITY_BINDING` hyperedge connecting:

```text
DomainEntityRef
+ constrained authority backend
+ HOTELS_MASTER mirror
+ Intelligence projection
+ Operational Graph projection
```

Alias relations are represented separately through `SUPERSEDES`. Missing pre-V2 causation becomes explicit `HISTORICAL_UNKNOWN`, never invented history.

## Outputs

```text
public_attestation.json        public-safe counts/hashes/parity
private_shadow_graph.json      private pseudonymous graph
private_id_map.json            private H-ID→pseudonym map
migration_event_ledger.jsonl   append-only shadow events
contextpack.json               SHA/watermark/projection-bound recovery
rollback_manifest.json         exact no-write rollback contract
migration_plan.json            CP14 preconditions and NEXT
manifest.json                  file hashes/bytes/privacy classification
```

## CP13 Definition of Done

```text
all entry gates pass
+ every physical authority entity has exactly one shadow binding
+ active/alias semantics preserved
+ historical uncertainty explicit
+ graph validates
+ event ledger verifies
+ ContextPack binds source/compile revisions
+ rollback manifest proves zero authority writes
+ public artifact exposes no raw H-ID
+ exact artifact persisted to Library and Drive
+ PR/main CI and independent artifact verification pass
```

CP13 may then be labelled `SHADOW_PARITY_VERIFIED`.

## CP14 adoption gate

CP14 does not require rewriting the hotel database into a graph store. It adopts V2 as the production **coordination, causal-history, ContextPack and assurance architecture** for new material waves while current domain authority stores remain authoritative.

Before adoption:

1. re-read fresh `main`, STATE/NEXT, authority artifacts and active claims;
2. verify CP7–CP13 exact evidence on current ancestry;
3. update `AGENTS.md` and WOP bridge so material waves create unique Session, Claim, Event and ContextPack artifacts;
4. update public-safe STATE/NEXT without copying mutable operational data into stable contracts;
5. define compatibility mode for existing domain workflows;
6. persist the adoption event/graph/ContextPack to GitHub, Drive and Library;
7. run a real bounded production wave in V2 coordination mode without changing its domain authority semantics;
8. prove rollback by disabling the coordination gate while preserving domain state and causal events.

## CP14 hard blocks

```text
stale main/authority/projection revision
active conflicting writer claim
unverified CP13 parity
missing recovery artifact
failed V2 workflow
authority store replacement or destructive migration
unreviewed public/private data leak
implicit H-ID allocation
outbound change
```

## Rollback

CP13 rollback discards shadow artifacts and retains all source authority unchanged.

CP14 rollback:

```text
stop issuance of new V2 leases
release/expire active V2 claims
retain append-only events
restore prior coordination feature flag / WOP adapter
retain current domain authority stores and projections
emit rollback event and rebuild ContextPack/NEXT
```

No rollback deletes historical events or rewrites hotel/source truth.

## Infrastructure posture

This migration deliberately uses current Python/JSON/SQLite/GitHub/Drive primitives. A distributed lease store, message bus or graph database requires an explicit empirical trigger and a separate decision record.

## Outbound

Migration and adoption never authorize employer-facing actions.

```text
CRM_UNIVERSE_COMPLETE may remain FALSE
OUTBOUND = CLOSED
send_allowed = 0
```
