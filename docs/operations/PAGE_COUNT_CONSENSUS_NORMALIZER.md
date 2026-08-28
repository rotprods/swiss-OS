# PAGE COUNT CONSENSUS NORMALIZER — SWITZERLAND_JOB_OS

Version: **PCCN-1.0**  
Status: **PRE-PCF, PRE-AUTHORITY EVIDENCE NORMALIZER**

## Purpose

A live HotellerieSuisse capture can encounter one stale cache response whose pagination metadata reports one fewer page than the complete partition set observed by the rest of the same run. PCF-1.0 correctly rejects any raw page-count drift. PCCN-1.0 provides a separate, narrow and auditable normalization gate so PCF itself remains strict.

PCCN never treats arbitrary source drift as coherent. It accepts only the bounded cache-skew shape below.

## Acceptance invariant

Given a count-less current HSLCA capture with `expected_pages = N`:

```text
capture pages are exactly positions 1..N
>= 99% of page responses independently report observed_expected_pages = N
every outlier reports exactly N-1
terminal page N itself reports N
capture has no violation other than REPORTED_RECORDS_UNRESOLVED and PAGE_COUNT_DRIFT
all authority / H-ID / outbound flags remain false / zero
```

Anything else fails closed.

The raw capture is immutable evidence. PCCN emits a **derived** capture. For every normalized outlier it retains:

```text
observed_expected_pages_original = <raw value>
observed_expected_pages = N
page_count_consensus_normalized = true
```

and adds a `page_count_consensus` proof containing the histogram, outlier positions and rule. This derived capture can then enter the existing PCF-1.0 partition/cardinality/identity checks.

## Why this is not a source-universe authority shortcut

PCCN resolves only a narrow pagination-metadata cache skew. PCF still independently requires exact partition positions, stable non-last partition cardinality, bounded terminal partition cardinality, unique detail URLs, current-run checkpoint timestamps, non-empty identity fields and materialized-record parity. MDM and every downstream CRM mapping gate remain independent.

PCCN cannot:

```text
allocate H-IDs
advance E4 or any later authority epoch
promote staging/cache/canary rows
set CRM_UNIVERSE_COMPLETE
open outbound
```

## Runtime chain

```text
HSLCA-R1.0 + MDC-1.1
→ HPCB-1.0 current-run checkpoint provenance
→ PCCN-1.0 only for bounded page-count metadata skew
→ PCF-1.0 materialized partition finalizer
→ MDM
→ CMI → CWP → ECV → SMC → SRR-1.1
```

## Production evidence that motivated the gate

Live capture `HS-MEMBER-DE-33206402141` materialized 172 contiguous pages and 2,061 unique detail records. 171 page responses reported 172 pages; page 170 alone reported 171; page 172 existed, reported 172 and contained 9 records while every preceding page contained 12. Raw evidence remains preserved as GitHub Actions artifact `9700376482` with ZIP digest `sha256:721f9ff9f84e2d5d9df62c6b22f12e7354cef3a298cb8990be66a202e1e769ce`.

PCCN was introduced because PCF correctly failed that raw capture with `PAGE_COUNT_DRIFT:171,172`; it is not a relaxation for wider drift.

## Safety

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```
