# HSLCA → PCF CHECKPOINT PROVENANCE BRIDGE — SWITZERLAND_JOB_OS

Version: **HPCB-1.0**  
Status: **PRE-AUTHORITY PROVENANCE ADAPTER**

## Purpose

PCF-1.0 requires truthful per-page `captured_at` timestamps so a stale resumed partition cannot satisfy a new current completeness claim. HSLCA-R1.0 predates that field but atomically writes one JSON checkpoint immediately after each successfully parsed page.

HPCB-1.0 enriches a finalized HSLCA capture with per-page timestamps derived from the exact checkpoint file modification time only after proving checkpoint JSON is semantically identical to the corresponding page embedded in `capture.json`.

For each page it requires:

```text
exact positive-integer page_position
same capture_id and locale
page-NNNN.json exists
checkpoint JSON == final capture page JSON
checkpoint mtime inside capture started_at..completed_at
```

One second of boundary tolerance is permitted only for filesystem timestamp granularity. It cannot bridge an earlier run.

## Runtime chain

```text
HSLCA-R1.0
→ MDC-1.1 identity parsing
→ atomic page checkpoints
→ finalized capture
→ HPCB-1.0 checkpoint timestamp provenance
→ PCF-1.0 only when provider aggregate count is absent
→ canonical MDM
→ CMI → CWP → ECV → SMC → SRR-1.1
```

If HSLCA obtains a provider-reported count and native MDM coverage is complete, PCF is not invoked.

## Safety

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```

HPCB never mutates operational authority, HOTELS_MASTER, Intelligence, Graph or outbound state. A live source capture is evidence only until the complete CRM source-universe and later atomic authority gates pass.
