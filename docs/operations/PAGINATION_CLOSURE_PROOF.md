# HSLCA PAGINATION CLOSURE PROOF — SWITZERLAND_JOB_OS

Version: **PCP-1.0**  
Status: **PRE-AUTHORITY ENUMERATION PROOF**

## Purpose

A current HotellerieSuisse member-directory capture can expose a deterministic terminal page boundary while the rendered page does not expose a parseable displayed total. PCP-1.0 permits that capture to prove exhaustive source enumeration **without inventing a count**.

PCP is deliberately narrower than `records_seen = source_total`. It is valid only when the same live HSLCA capture proves the complete page interval and every page satisfies strict density, identity and checkpoint-integrity constraints.

## Accepted precursor

Input must be a `MEMBER_DIRECTORY_CAPTURE_V1` HSLCA capture whose only capture violation is:

```text
REPORTED_RECORDS_UNRESOLVED
```

Any page error, page-count drift, override conflict, mixed capture, invalid checkpoint or other violation blocks PCP.

## Closure proof

For terminal page `N` and configured page size `K`, PCP requires all of:

```text
page 1 observed terminal page N from the live source
observed page positions exactly 1..N
all observed pagination metadata agrees on N
all page checkpoints belong to the same capture_id + locale
all page record hashes recompute exactly
pages 1..N-1 contain exactly K records
page N contains 1..K records
every record has non-empty name, city, evidence_ref and detail_url
detail_url is unique across the capture
no page contains an independently parsed reported-record count
```

Only then may the derived raw count be computed as the exact materialized cardinality of the proven page interval.

```text
derived_raw_records = Σ records(page 1..N)
```

This count is tagged with:

```text
method = ROOT_PAGINATION_CLOSURE
```

It is not represented as a displayed provider count.

## Why this is non-circular

PCP does not infer completeness merely because a crawler stopped. The terminal page boundary must have been observed on page 1 during the same capture, and the exact 1..N interval must then be materialized with full non-terminal pages, a valid terminal page, unique identities and hash-valid checkpoints. An arbitrary operator-supplied page count cannot satisfy the root-boundary requirement.

## Output

```bash
python -m swiss_os.pagination_closure prove \
  <capture.json> \
  --out-dir <proved-bundle> \
  --expected-page-size 12
```

Outputs:

```text
capture-pagination-closed.json
member-directory-manifest.json
pagination-closure-proof.json
pagination-closure-summary.json
```

The resulting member-directory manifest must still pass the canonical MDM compiler. PCP adds no bypass around locale/epoch/page coverage, duplicate identity or record-parity rules.

## Hard boundary

PCP remains source evidence only:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```

A PCP-complete directory manifest still requires the remaining pre-authority chain (source-scope reconciliation when applicable, CMI/CWP/ECV/SMC/SRR), terminal source mappings, and a bounded WOP authority transaction across DB → HOTELS_MASTER → Intelligence → Operational Graph → observability/recovery before `CRM_UNIVERSE_COMPLETE` can become true.

Historical cache evidence cannot enter PCP. Old captures whose parser produced semantically invalid entity fields must be rejected or treated only as non-identity acquisition diagnostics.
