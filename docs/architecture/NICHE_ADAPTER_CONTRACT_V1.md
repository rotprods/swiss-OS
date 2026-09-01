# NICHE ADAPTER CONTRACT V1

Status: W1 executable contract

A niche adapter extends the generic employment core; it never forks governance, evidence, candidate truth, application idempotency or outcome semantics.

## Required declarations

- `niche_id` (`NICHE-NNN`)
- stable slug and adapter version
- organization types
- role families
- source-scope classifications
- channel types/policies
- supported candidate lanes
- niche-specific enrichment dimensions only where genuinely distinct

## Required adapter lifecycle

SOURCE SNAPSHOT -> SOURCE RECORDS -> NORMALIZE -> ENTITY RESOLUTION -> ORGANIZATION/ALIAS/GROUP -> OPPORTUNITY -> ROUTING -> FIT -> APPLICATION GATE -> RESPONSE/OUTCOME.

## Invariants

1. Adapter cannot mutate another niche's canonical identity without an explicit cross-niche entity-resolution transaction.
2. Source-record identity is snapshot-scoped; page number is not identity.
3. Unknown is not negative evidence.
4. Scores are heuristic 0-100 rankings, never hiring probabilities.
5. Candidate claims remain owned by Candidate Truth OS.
6. External actions remain owned by the global suppression/idempotency/authorization gate.
7. An adapter cannot open outbound.
8. A niche can be paused without breaking core state.
9. Cross-niche organizations may have multiple `organization_niches` relations; duplicate organization identities are not created merely because the niche differs.
10. Every adapter must prove restore/replay and source-scope semantics before production scale.

## NICHE-001 compatibility rule

`canonical_hotels` remains authoritative during migration. `legacy_hotel_org_bridge` is the explicit compatibility surface. W2 may mark a bridge `VERIFIED_EQUIVALENT` only after identity, source, active-state and alias semantics agree. Generic organizations are not allowed to advance hotel authority independently.

## Anti-overengineering gate

Do not add adapter hooks until NICHE-001 or NICHE-002 demonstrates the need. Shared behavior belongs in core only when at least two niches require the same semantic responsibility or when it is a global truth/governance invariant.
