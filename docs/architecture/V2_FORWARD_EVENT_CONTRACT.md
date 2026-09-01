# V2 Forward Event Contract

Status: **ACTIVE CANDIDATE — issue #426 / fencing token11**

## Boundary

`COS-V2-EVENT-1.0` is historical replay compatibility only. Its admissible corpus is frozen at Git commit `e13b05fc24cb5b5f0883d86bddfb6d602007fb48` by `docs/state/v2/legacy-event-boundary.json`.

A 1.0 event is valid only when the same path existed at the frozen commit and the current Git blob is byte-identical. New 1.0 event paths and mutations of frozen 1.0 blobs are rejected by CI.

`COS-V2-EVENT-1.1` is the forward production contract.

## Lifecycle invariant

For `CLAIM_ACQUIRED`, `CLAIM_RELEASED`, and `CLAIM_SUPERSEDED`, a 1.1 event must contain a `causation` array with exactly one durable `claim:<claim_id>` reference. Other causation references such as `issue:<id>` may coexist.

Zero claim references fail closed. Multiple claim references fail closed. Unknown claim references fail during lifecycle reduction.

## Writer contract

New code must use `build_forward_event()` from `swiss_os.v2_coordination`. The builder always emits `COS-V2-EVENT-1.1` and refuses invalid lifecycle events. There is intentionally no canonical writer for 1.0.

## Replay contract

The reducer accepts frozen 1.0 history and 1.1 forward events in one deterministic ledger. Legacy fallback remains available only because immutable historical 1.0 records predate explicit claim causation. The forward-event CI guard prevents that fallback from becoming a production path again.

## Retirement criteria

Legacy fallback may be removed only after all durable 1.0 lifecycle history has a lossless, provenance-preserving migration accepted by a separately fenced migration wave. Chat memory, timestamps alone, or silent rewrites are not sufficient migration evidence.

## Safety

This contract has no hotel authority, CRM decision, candidate-private, H-ID, application-submission, Gmail, or outbound authority. E4/690 and `H-0691_UNALLOCATED` remain unchanged; outbound stays closed.
