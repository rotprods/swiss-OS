# CMI WORK PACKET — SWITZERLAND_JOB_OS

Version: **CWP-1.1**  
Status: **EXECUTABLE NON-AUTHORITATIVE WORK ROUTING CONTRACT**

## Objective

Transform the full CMI anti-join decision set into bounded, deterministic entity-resolution work packets.

```text
complete directory capture
→ D2C records
→ CMI anti-join decisions
→ CWP-1.1 classification
→ bounded exact-current/entity-resolution batches
```

CMI output is not useful operationally if it remains one opaque decision array. CWP separates terminal matches from unresolved work and creates stable batches that MEP can execute sequentially.

## Work states

```text
RECONCILE_REQUIRED
VERIFY_NEW_ENTITY
REVIEW_UNKNOWN_DECISION
MATCHED_EXISTING
```

### `MATCHED_EXISTING`

Terminal for the current anti-join pass. These records are excluded from active work batches and retained by a deterministic digest.

### `RECONCILE_REQUIRED`

Highest-priority work. Includes ambiguous, conflicting or explicitly reconcile-required CMI outcomes.

### `VERIFY_NEW_ENTITY`

Source record has no existing canonical match and requires exact-current identity verification before any future canonical allocation.

The canonical CMI-1.0 staging class `TRUE_MISSING` maps exactly to this work state. This is a routing classification only; it does **not** reserve or allocate an H-ID and does not imply the source record is a genuinely new real-world entity until exact-current and dedupe/group/alias review pass.

### `REVIEW_UNKNOWN_DECISION`

CMI emitted an unrecognized or incomplete decision shape. It remains visible and cannot silently become a new entity.

## Priority

```text
RECONCILE_REQUIRED       100
VERIFY_NEW_ENTITY         80
REVIEW_UNKNOWN_DECISION   60
MATCHED_EXISTING           0
```

Ordering is deterministic:

```text
priority DESC
→ source_record_key ASC
```

## Input compatibility

The builder accepts a direct decision array or an object containing:

```text
decisions
result.decisions
payload.decisions
```

CWP-1.1 directly consumes the canonical `crm-ingest stage` / `mass_ingest.IngestDecision.as_dict()` shape without a translation shim. In particular it recognizes:

```text
staging_class
normalized_name
normalized_city
normalized_detail_url
source_record_key
matched_hotel_id
reason_code
```

Compatibility variants remain accepted for older callers (`decision`, `classification`, `raw_name`, `raw_city`, `detail_url`, etc.). Missing source keys receive an index-scoped fallback key, but duplicate keys fail closed.

Canonical CMI staging routing is:

```text
ACTIVE_MATCH + matched_hotel_id → MATCHED_EXISTING
ALIAS_MATCH + matched_hotel_id  → MATCHED_EXISTING
TRUE_MISSING                    → VERIFY_NEW_ENTITY
CONFLICT                        → RECONCILE_REQUIRED
unknown/unrecognized            → REVIEW_UNKNOWN_DECISION
```

`EXCLUSION_CANDIDATE` remains non-terminal at the CWP layer unless a later exclusion-review contract produces an evidence-backed terminal exclusion mapping.

## Output

```text
CMI-WORK-PACKET-1.0
snapshot_id
input_decisions
active_work_items
terminal_matches
counts_by_state
batch_size
batches[]
packet_sha256
next_route
```

The serialized schema remains `CMI-WORK-PACKET-1.0`; CWP-1.1 is a compatible routing correction, not a wire-format change. Each batch includes its own SHA-256 and hard-lock state.

## Commands

```bash
python -m swiss_os.ingest_packet build \
  CMI_STDOUT.json \
  --snapshot-id <snapshot-id> \
  --batch-size 100 \
  --out CMI_WORK_PACKET.json

python -m swiss_os.ingest_packet validate CMI_WORK_PACKET.json
```

## Hard invariants

```text
terminal matches never enter active batches
source_record_key unique across active batches
batch counts and hashes exact
packet hash exact
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

CWP does not update canonical hotels. It produces the bounded work frontier consumed by exact-current and entity-resolution waves.

## Relationship to MEP

When R4 is the selected route:

```text
CWP first unresolved batch
→ exact-current evidence refresh
→ entity resolution
→ typed terminal outcome
→ packet recompute
→ immediately enter next batch while safe
```

The activation may terminate only under an MEP terminal state and must persist a validated NEXT pointer to the next unresolved batch.
