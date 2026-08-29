# CANDIDATE ENTITY PARTITION — SWITZERLAND_JOB_OS

Version: **CEP-1.0**  
Status: **PRE-AUTHORITY ENTITY-RESOLUTION GATE**

## Objective

Partition every exact-current candidate source record into one deterministic candidate-entity set before any canonical H-ID can be allocated.

Candidate verification proves that a source record currently resolves to an entity detail. It does not prove that every verified source record represents a different real-world hotel. CEP-1.0 closes that gap before authority promotion.

## Inputs

CEP consumes:

```text
candidate export gzip or strict base64(gzip)
candidate export manifest
frozen source snapshot ID
```

The loader must verify:

```text
gzip SHA-256
canonical JSON(records) SHA-256
declared record count
payload/manifest snapshot agreement
unique non-empty source/provider record keys
non-empty name and city
```

A hash, count or lineage mismatch fails closed.

## Strong identity partition

Automatic same-entity clustering is allowed only when records share the same normalized non-empty exact detail URL:

```text
EXACT_DETAIL_URL
```

The cluster leader is the lexicographically smallest source record key. This is deterministic metadata only; it is not a canonical H-ID.

Every other source record remains a singleton candidate cluster.

## Name/city collisions

Equal normalized `name + city` with different exact detail URLs is not automatically merged.

It becomes:

```text
NAME_CITY_MULTIPLE_STABLE_IDENTITIES
→ EXPLICIT_ENTITY_REVIEW_NO_AUTOMERGE
```

This protects annexes, apartments, separately listed properties and same-name establishments from false deduplication.

A source record without a stable detail URL becomes:

```text
MISSING_DETAIL_URL
→ REFRESH_STABLE_ENTITY_DETAIL
```

## Output contract

CEP emits:

```text
partition_state
partition_sha256
candidate record count
candidate cluster count
singleton clusters
stable detail-URL clusters
name/city review conflicts
missing-detail conflicts
exact assignment count
omitted/duplicate/foreign assignment counts
```

Each source key must occur in exactly one partition cluster.

Possible partition states:

```text
EXACT_PARTITION
PARTITION_COMPLETE_REVIEW_REQUIRED
```

`PARTITION_COMPLETE_REVIEW_REQUIRED` means every record was assigned exactly once but one or more candidate clusters still need explicit entity review.

## Relationship to SRR

```text
exact-current evidence complete
→ CEP-1.0 candidate↔candidate partition
→ resolve CEP conflicts
→ SRR candidate-cluster↔active-canonical comparison
→ proposed new canonical entity set
→ reverse authority/source reconciliation
→ authority-ready mapping plan
```

CEP does not replace SRR, SSR, ASR or the authority reconciliation gate.

## Fail-closed invariants

```text
source keys unique
exact assignment count = input record count
assignment duplicates = 0
omitted source records = 0
foreign source records = 0
cluster leader belongs to cluster
cluster leader is deterministic
partition hash validates
```

## Authority and outbound boundary

CEP-1.0 is read-only and pre-authority:

```text
authority_advanced = false
h_id_allocations = 0
canonical_id_reservations = 0
OUTBOUND = CLOSED
outbound_opened = false
send_allowed = 0
```

A CEP cluster ID is never an H-ID reservation.

## Executable implementation

```text
src/swiss_os/candidate_entity_partition.py
```

Example:

```bash
PYTHONPATH=src python -m swiss_os.candidate_entity_partition \
  docs/state/CRM_CANDIDATE_EXPORT_<snapshot>.json.gz \
  docs/state/CRM_CANDIDATE_EXPORT_<snapshot>.manifest.json \
  --out .artifacts/cep/candidate-entity-partition.json \
  --summary-out .artifacts/cep/candidate-entity-partition-summary.json
```

The real-universe canary is executed by:

```text
.github/workflows/candidate-entity-partition-canary.yml
```
