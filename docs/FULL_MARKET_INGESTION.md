# Full Market Ingestion — Swiss OS

## Purpose

Build a reproducible discovery corpus for the broad Swiss accommodation market before canonical promotion or deep enrichment.

The HotellerieSuisse **Branchenverzeichnis** is treated as a broad discovery surface. It is deliberately separate from the narrower current-member canonical set.

## Two denominators

`UNIVERSE_DISCOVERED`
: Every distinct establishment listing observed on the broad official directory, subject to source/robots/access rules and scope classification.

`MEMBER_CANONICAL`
: Only identities that pass entity resolution and current membership/evidence gates. Existing `H-####` IDs remain immutable.

Never substitute one denominator for the other.

## Pipeline

```text
OFFICIAL DIRECTORY
→ PAGE ENUMERATION
→ LISTING EXTRACTION
→ DETERMINISTIC U-* DISCOVERY ID
→ NAME/CITY/DETAIL-URL NORMALIZATION
→ COUNTRY-SCOPE STATE
→ TYPE HINT (non-authoritative)
→ ENGINE BACKLOG MATRIX
→ QA / MANIFEST / CHECKSUMS
→ ARTIFACT

Then, in a separate controlled phase:

DISCOVERY CORPUS
→ CANONICAL ANTI-JOIN
→ EXACT DETAIL VALIDATION
→ MEMBER / NON-MEMBER / OUT-OF-SCOPE STATE
→ H-* ALLOCATION ONLY FOR QUALIFIED NEW CANONICAL ENTITIES
→ INTELLIGENCE / GRAPH / EVIDENCE
→ DEEP ENRICHMENT
```

## Engine feed semantics

Every discovered entity receives explicit engine state. This means the entity is represented in the orchestration graph and has deterministic downstream work. It does **not** mean the downstream engine has completed enrichment.

Expected L0/L1 states include:

- Discovery: `DISCOVERED_T1_LISTING`
- Entity resolution: `PENDING_CANONICAL_ANTIJOIN`
- Evidence: `T1_LISTING_ONLY`
- Intelligence and research engines: `PENDING_ENTITY_RESOLUTION`
- Opportunity/scoring/personalization/message/QA: `PENDING_DEPENDENCIES`
- TTL: `LISTING_OBSERVATION_TIMESTAMPED`
- Export: `DISCOVERY_EXPORT_READY`
- Governance: `OUTBOUND_CLOSED`

No row-existence shortcut may increment L4/L9.

## Crawl guardrails

- Respect `robots.txt`; fail closed if it cannot be evaluated.
- Rate limit requests.
- Retry only ordinary transient HTTP/network failures.
- Do not bypass access controls.
- Derive current directory result/page counts from the source instead of assuming historical 2050 or a fixed page count.
- Fail if fewer than 2,000 unique discovery entities are extracted.
- Fail if extracted coverage is below 90% of the observed directory result count.
- Suspicious per-page cardinality is surfaced as QA, not silently ignored.
- Large discovery outputs remain GitHub Actions artifacts, not public repository blobs.

## Outputs

`hotelleriesuisse_universe_discovery.csv`
: deduplicated broad discovery entities.

`engine_matrix.csv`
: one row per discovery entity with explicit state for every registered engine.

`hotelleriesuisse_universe_discovery.json`
: machine-readable discovery records.

`manifest.json`
: observed counts, page errors, QA diagnostics, engine contract and SHA-256 checksums.

## Promotion contract

Discovery is not canonical promotion.

A new `H-*` identity requires the normal constrained write protocol:

```text
exact/current evidence
→ normalized anti-join
→ alias/group/domain resolution
→ DB canary
→ integrity/FK/replay/restore PASS
→ canonical mirror
→ Intelligence
→ Graph
→ observability
```

Outbound remains independently CLOSED.
