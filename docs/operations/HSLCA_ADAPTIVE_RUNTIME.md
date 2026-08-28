# HSLCA ADAPTIVE RUNTIME — SWITZERLAND_JOB_OS

Version: **HSLCA-R1.0**  
Status: **PRE-AUTHORITY SOURCE ACCESS ACTUATOR**

## Purpose

Provide the network-policy layer for the resumable HSLCA-1.0 parser/checkpoint engine.

```text
HSLCA core
  owns: parsing + page checkpoints + resume + capture coherence + MDM bridge

HSLCA-R1.0
  owns: approved provider host boundary + robots policy + adaptive throttling
        + persistent-429 circuit stop + safe runtime CLI
```

A failed page aborts the current activation. HSLCA checkpoints already captured pages, so a later activation can resume from the same capture ID rather than requesting every subsequent page after the provider has started returning 429.

## Access policy

Only HTTP(S) hosts within `hotelleriesuisse.ch` are accepted. Lookalike domains are rejected.

Before a directory URL is accepted, its origin robots policy is fetched and evaluated for the SWITZERLAND_JOB_OS user-agent. A definite robots `404` is treated as absence of a robots policy. Robots throttling/server/network failure fails closed rather than becoming permission to continue.

Redirects outside the approved provider host boundary are rejected. When a redirect changes HotellerieSuisse subdomain, the destination robots policy is checked before the response body is accepted for directory processing.

## Rate-limit policy

Retryable classes:

```text
HTTP 429
HTTP 5xx
network / timeout / OS transport failures
```

Policy:

```text
Retry-After when supplied
otherwise exponential backoff
base default = 15 s
cap default  = 120 s
attempts default = 6
page cadence default = 6 s
```

Non-retryable 4xx fails immediately.

Persistent 429 does **not** advance to page N+1. The fetch raises a typed `HSLCAAccessError`; previously validated page checkpoints remain resumable evidence.

## CLI

```bash
python -m swiss_os.hotelleriesuisse_capture_runtime capture \
  --capture-id HS-MEMBER-DE-<epoch> \
  --root-url https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis \
  --locale de \
  --out-dir <private-output-dir>
```

Re-use the same capture ID and output directory to resume the same coherent capture. Do not combine pages from different epochs/locales/capture IDs.

## Completion semantics

Runtime success is not CRM completion. The source capture must still pass the HSLCA/MDM coherence gates, source-scope reconciliation, CMI/CWP/ECV/SMC/SRR, the bounded authority transaction, DB ↔ Sheets ↔ Intelligence ↔ Operational Graph reconciliation and CUP final validation.

Hard outputs remain:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```

Historical cache and partial runtime checkpoints never become source authority merely because they are persisted.
