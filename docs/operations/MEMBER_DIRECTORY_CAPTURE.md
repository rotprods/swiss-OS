# MEMBER-DIRECTORY CAPTURE — SWITZERLAND_JOB_OS

Version: **MDC-1.0**  
Status: **EXECUTABLE CURRENT-SNAPSHOT ACQUISITION CONTRACT**

## Objective

Capture one coherent current HotellerieSuisse member-directory snapshot directly from the selected official locale surface, then emit an MDM-1.0 manifest that can prove source-side completeness.

MDC replaces manual page/snippet harvesting as the preferred directory-side acquisition mechanism when the official surface is technically and legally accessible.

```text
official directory root
→ robots preflight
→ root pagination/count discovery
→ bounded sequential page capture
→ exact member-detail links + display name + city
→ page SHA manifest
→ duplicate/overlap/card QA
→ MDM-1.0 complete or partial manifest
```

## Safety and access rules

MDC:

- reads only public official pages;
- checks `robots.txt` before capture;
- uses a descriptive user agent;
- applies an explicit inter-request delay;
- performs bounded retries;
- never bypasses CAPTCHA, authentication, access controls or provider restrictions;
- stops if robots policy does not allow capture;
- never sends applications or contacts employers.

## Snapshot binding

One capture binds exactly:

```text
source provider
locale
root URL
capture start/end
source epoch
root-discovered page count
root-discovered result count
page response SHA-256
exact member-detail URL
name + city displayed in the same directory card
```

The source epoch is immutable for the capture.

## Card identity

The directory card contract is:

```text
first non-empty anchor text = display name
last non-empty anchor text = city
anchor href = exact member-detail URL
```

A card with insufficient or invalid text is rejected and blocks complete coverage.

`hotel-page-N` is partition lineage only. It is not source-record identity.

Snapshot-scoped `record_id` is derived from the exact detail URL.

## Complete-capture gates

`coverage_complete_requested=true` only when all pass:

```text
robots_allowed
page_errors = 0
observed_pages = root-discovered expected_pages
empty_pages = 0
all non-last pages match expected page size
last page count is within 1..page_size
duplicate detail URLs = 0
sum page records = unique records
root displayed count is unambiguous
root displayed count = unique records
card rejects = 0
```

MDM-1.0 must then independently pass:

```text
provider/locale/epoch coherence
record/detail/name+city uniqueness
partition parity
raw-record parity
current evidence scope only
transfer hash validation
```

Any failed gate produces a partial manifest, never a false complete snapshot.

## Outputs

```text
CAPTURE_SUMMARY.json
PAGE_MANIFEST.json
MEMBER_DIRECTORY_MANIFEST.json
MEMBER_DIRECTORY_RECORDS.json
robots.txt
pages/*.html.gz        optional private recovery evidence
```

The page manifest stores:

- requested/final URL;
- HTTP status;
- observed_at;
- SHA-256;
- byte size;
- records/rejects count;
- ETag/Last-Modified when provided.

## Command

```bash
python -m swiss_os.member_directory_capture capture \
  --root-url https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis \
  --locale de \
  --out-dir private/captures/hs-directory-de \
  --delay 0.30 \
  --expected-page-size 12 \
  --retain-html
```

Exit code is zero only when MDM reports a complete coherent manifest.

## Authority and outbound hard locks

MDC output always remains pre-authority:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

A complete directory manifest can feed SSR/CMI and terminal mapping work. It does not update HOTELS_MASTER or the Operational Graph by itself.

## Relationship to the execution stack

```text
MDC-1.0 complete directory capture
+
DSA-1.0 discover.swiss capture when available
→ SSR-1.0 source-scope reconciliation
→ FROZEN_CANDIDATE
→ candidate export
→ CMI-1.0 mass staging
→ exact-current/entity resolution
→ terminal mappings
→ CUP-1.1 complete CRM universe
```

When the discover.swiss key is unavailable, MEP-2.0 may still execute MDC and CMI canary anti-join to reduce the exact same CRM bottleneck, while preserving SSR and authority gates.
