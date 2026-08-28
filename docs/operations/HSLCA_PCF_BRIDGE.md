# HSLCA → PCF CHECKPOINT PROVENANCE BRIDGE — SWITZERLAND_JOB_OS

Version: **HPCB-1.0**  
Status: **PRE-AUTHORITY PROVENANCE ADAPTER**

## Problem

PCF-1.0 correctly refuses to treat an old resumed partition as part of a new current completeness claim. It therefore requires `captured_at` on each page and checks that every timestamp belongs to the current capture window.

HSLCA-1.0 predates that field. It does, however, atomically write one JSON checkpoint immediately after each successfully parsed page.

## Contract

HPCB-1.0 enriches an HSLCA capture with truthful per-page timestamps derived from the corresponding checkpoint file modification time **only after** the checkpoint JSON is proven semantically identical to the page embedded in `capture.json`.

For every page it requires:

```text
exact page_position
same capture_id
same locale
checkpoint page-NNNN.json exists
checkpoint JSON == capture page JSON
checkpoint mtime >= capture started_at - 1 second
checkpoint mtime <= capture completed_at + 1 second
```

The one-second boundary allowance is only filesystem timestamp granularity tolerance. It cannot bridge minutes, hours or a prior activation.

A stale resumed checkpoint therefore fails PCF current-run coherence rather than silently becoming a fresh observation.

## CLI

```bash
python -m swiss_os.hslca_pcf_bridge bridge \
  <capture.json> \
  --pages-dir <capture-dir>/pages \
  --out <capture-with-checkpoint-times.json>

python -m swiss_os.partition_count_finalizer build \
  <capture-with-checkpoint-times.json> \
  --out <partition-count-finalizer.json>
```

PCF remains the only denominator finalizer. HPCB does not define a second completeness method.

## Live execution path

```text
HSLCA-R1.0
→ atomic page checkpoints
→ final HSLCA capture
→ HPCB-1.0 timestamp provenance
→ PCF-1.0 when REPORTED_RECORDS_UNRESOLVED is the sole capture violation
→ canonical MDM compiler
→ downstream pre-authority CMI/CWP/ECV/SMC/SRR
```

If HSLCA obtains a provider-reported count and its native manifest is complete, PCF is not invoked.

## Hard locks

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```

HPCB never mutates the operational DB, HOTELS_MASTER, Intelligence, Operational Graph or outbound state.
