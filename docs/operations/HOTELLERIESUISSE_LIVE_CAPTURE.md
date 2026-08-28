# HOTELLERIESUISSE LIVE CAPTURE ADAPTER

Version: **HSLCA-1.0**  
Status: **EXECUTABLE PRE-AUTHORITY ACQUISITION ROUTE**

## Objective

Capture one coherent public HotellerieSuisse member-directory surface and emit the `MEMBER_DIRECTORY_CAPTURE_V1` payload consumed by MDMA-1.0.

This adapter exists because historical page caches are useful for discovery but cannot prove a current complete snapshot. It uses current rendered pages, explicit locale/surface/epoch, page-level checkpoints and fail-closed coherence checks.

## Hard boundaries

```text
public pages only
no authentication bypass
no CAPTCHA bypass
no anti-bot circumvention
no canonical H-ID allocation
no authority promotion
no outbound
```

A successful capture is source evidence, not operational authority.

## Extraction model

The parser deliberately avoids dependency on one CSS class. A property record is recognized by a HotellerieSuisse entity-detail URL under either:

```text
.../mitgliederverzeichnis/hotel-...
.../liste-des-membres/hotel-...
```

`hotel-page-N` pagination URLs are excluded.

For each property the adapter resolves:

```text
name
city
detail_url
page source URL
evidence_ref
```

The city is extracted from the rendered Swiss postal-address context. Missing name, city or detail records fail the page capture.

## Coherent capture rules

The complete route requires:

```text
one capture_id
one provider
one surface
one locale
one bounded capture interval
expected page count resolved
reported record count resolved
all page positions captured
no count/page drift during the run
no override conflict
one or more records per page
valid page checkpoint hashes
```

Any drift changes the capture to:

```text
LIVE_PARTIAL
coverage_claim = PARTIAL
```

MDMA-1.0 then refuses `coverage_complete`.

## Resume and recovery

Every page is persisted atomically:

```text
<out-dir>/pages/page-0001.json
<out-dir>/pages/page-0002.json
...
```

A checkpoint is reused only when these match:

```text
capture_id
locale
source_url
non-empty records
records_sha256
```

The root page is reread on resume to reconstruct current count/page context. Invalid/tampered checkpoints are refetched.

Final outputs:

```text
<out-dir>/capture.json
<out-dir>/member-directory-manifest.json
```

## CLI

```bash
PYTHONPATH=src python -m swiss_os.hotelleriesuisse_capture_cli \
  --locale de \
  --capture-id HS-DE-<UTC-EPOCH> \
  --out-dir /private/path/hs-capture
```

Optional explicit expectations:

```bash
--expected-pages N
--reported-records N
```

Overrides remain subject to conflict detection against rendered observations.

Operational controls:

```bash
--delay 0.5
--timeout 45
--retries 3
--no-resume
```

Default behavior is sequential, bounded and resumable. The adapter does not parallelize aggressively or claim an always-on crawler.

## Route integration

```text
HSLCA-1.0 current rendered capture
→ MDMA-1.0 coherent manifest
→ SSR-1.0 vs discover.swiss capture
→ FROZEN_CANDIDATE
→ candidate export
→ mass CRM staging
```

If the structured discover.swiss key is unavailable, HSLCA/MDMA work still advances the directory side. SSR remains blocked until both sides exist or every source-only delta has an evidence-backed explanation.

## Safety outputs

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```
