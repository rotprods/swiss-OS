# EGR-1.0 — Entity Granularity Review Protocol

Status: **PREAUTHORITY / FAIL-CLOSED**  
Objective: `CRM_UNIVERSE_COMPLETE`  
Applies to: source records whose current evidence proves a parent/component/subproperty relationship but does not prove identity collapse.

## Decision rule

A related accommodation product may be typed `NEW_CANONICAL` **preauthority only** when current evidence establishes all of the following:

1. the source is exposed as its own named accommodation product or member-directory entry;
2. current first-party or qualified-current evidence distinguishes the source product from the proposed parent/sibling canonical at the accommodation-entity level;
3. the relationship to the parent/operator is explicit and preserved as relationship metadata rather than converted into an alias;
4. no evidence proves that the source name is merely an alternate name for the same sellable accommodation entity;
5. the decision does not reserve or allocate an H-ID, create a terminal mapping, advance authority, or mutate an authority plane.

A shared operator, licence, address, campus/resort membership, booking surface, service bundle, or brand is **never sufficient by itself** to collapse two entities. Conversely, a child/component relationship does not prohibit a separate canonical candidate when the CRM already models separately marketed accommodation entities at that granularity.

## Precedence and comparator rule

Existing canonical granularity is admissible as a consistency check, not as sole proof. Example: `H-0012 CERVO Mountain Resort` and `H-0201 Nomad Lodge by CERVO Mountain Resort` coexist as canonical accommodation entities. This supports, but does not alone prove, separate treatment of another separately marketed CERVO accommodation component.

Every decision must still carry current source evidence and live canonical comparator readback. Similarity remains review-space reduction only.

## Allowed preauthority outcomes

- `NEW_CANONICAL`: distinct sellable/listed accommodation entity; preserve parent/component relationship metadata; `RECONCILE_REQUIRED` remains until an authority-eligible commit.
- `ALIAS_EXISTING` / `MATCH_EXISTING`: only when current evidence proves the same accommodation entity under alternate naming; terminalization is separately gated by SRR authority rules.
- `UNRESOLVED`: evidence establishes relationship but not entity granularity, or evidence conflicts.

## Hard gates

```text
canonical_id_reservation_from_staging = 0
h_id_allocation                       = 0
authority_advance                     = false
terminal_mapping_from_relationship    = 0 unless independently SRR-proven
OUTBOUND                              = CLOSED
send_allowed                          = 0
irreversible_external_actions         = 0
```

Canary, cache, staging, ECV, SRET, PIE and preauthority SRR artifacts cannot independently advance canonical authority. Any authority transaction requires a separate DB-first, receipt-backed, cross-plane reconciliation path and the applicable fencing/authorization preconditions.
