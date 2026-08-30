# MARKET ENRICHMENT FACTORY — MEF-2061 v1.0

Status: **READ_ONLY_RESEARCH / OUTBOUND CLOSED**

## Mission

Turn the complete frozen HotellerieSuisse source universe (`2061` records) into a parallel market-intelligence plane without waiting for every CRM entity-resolution decision to become authoritative.

The factory processes immutable source `record_id`s, not provisional canonical H-IDs. This permits vacancy, recruiting-route, housing, people, scoring and application-preparation work to progress safely while `CRM_UNIVERSE_COMPLETE=false`.

## Pipeline

```text
2061 frozen member-directory records
  -> deterministic 42-shard partition
  -> HotellerieSuisse detail readback
  -> explicitly signaled official property website
  -> official careers/jobs route discovery
  -> current vacancy evidence (JSON-LD JobPosting / direct opening routes / explicit no-openings proof)
  -> E07 Vacancy
  -> E08 Housing
  -> E09 People-route discovery
  -> E10 Application Channel
  -> E11 evidence/freshness
  -> E12 graph edges
  -> E14 recheck priority
  -> E15 market-readiness scoring
  -> E16 private Candidate Truth join placeholder
  -> E17 hotel-specific application seed
  -> E18 QA
  -> E19 observability
  -> E20 recovery hashes
  -> E21 GitHub Actions delivery
  -> E22 outbound/security lock
```

## Evidence semantics

- T1/property-controlled evidence outranks aggregators.
- `JobPosting` structured data on a property-controlled route is a strong current vacancy signal.
- A direct job/opening route is current discovery evidence even when structured vacancy data is absent.
- “No vacancies” is asserted only when an official careers surface states it explicitly. Missing job links never become a negative claim.
- General contact is never promoted to recruitment.
- Team/people pages are route discovery only; personal contact data is not persisted in this public artifact.
- Staff-housing claims require an explicit current housing route.
- Similarity and source-record presence cannot allocate H-IDs or change authority.

## Network/security contract

- GET-only public HTTPS.
- DNS/IP SSRF guard before every request and redirect.
- localhost, private/link-local/reserved IPs, embedded credentials and non-standard ports are rejected.
- `robots.txt` is respected; ambiguous robots failures fail closed.
- bounded timeout and response size.
- raw HTML is never persisted.
- only explicitly labelled website links from the HotellerieSuisse detail page may become the primary official-site candidate.

## Parallelization

The 2061-record manifest is partitioned into 42 exact contiguous shards. GitHub Actions runs at most six shards concurrently. Aggregate publication is blocked unless the union of shard `record_id`s exactly equals the frozen 2061-record set with no duplicates and the source records SHA remains:

`62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`

The full per-hotel aggregate remains an Actions artifact. The public repository receives only a public-safe summary and run receipt.

## Personalized proposal semantics

E17 generates one hotel-specific application **seed** per source record using only public hotel/vacancy context. It cannot fabricate Roberto's skills, languages, availability, work history or relocation constraints. Those facts must enter through the private Candidate Truth plane before a final application can be rendered.

Thus:

```text
hotel-specific personalization = automatic
candidate-specific factual claims = private Candidate Truth join
final_send_ready = false
```

## Hard locks

```text
authority_advanced                    false
canonical_id_allocations              0
canonical_id_reservations             0
CRM_UNIVERSE_COMPLETE                 false
OUTBOUND                              CLOSED
send_allowed                          0
irreversible_external_actions         0
```

No output from MEF-2061 is operational authority or permission to contact an employer.
