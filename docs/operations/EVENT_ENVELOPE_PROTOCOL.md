# EVENT ENVELOPE PROTOCOL — EEP-2.0

Status: **V2 CANDIDATE CONTRACT**

Every material coordination event has one canonical envelope containing `event_id`, `event_type`, timestamp, full session identity, `correlation_id`, optional `causation_id`, current `main_sha`, authority epoch/parent, projection revision, event watermark, fencing token, aggregate type/id, expected aggregate version, payload and schema version.

## Invariants

- `event_id` is globally unique.
- events are append-only; correction uses a new event and `SUPERSEDES` semantics.
- aggregate expected-version mismatch rejects mutation.
- an event may describe intended authority work but cannot bypass WOP promotion gates.
- watermark advances only after durable append semantics of the owning store.
- replayed event IDs never cause a second side effect.
- causation/correlation lineage is preserved.
- historical events are never rewritten to make present state look cleaner.

## Incremental adoption

Existing operational tables are **not** retroactively relabeled as event-sourced. V2 adopts event-first semantics for session/claim/coordination state and for future migrations where replay value justifies it. Current constrained tables remain authority under WOP until an explicit migration passes canary, restore and cross-plane reconciliation.

## Projection

Reducers may derive state, graph and observability projections from accepted events. Those projections are caches/views unless the governing authority contract explicitly promotes them. The event ledger never becomes a second independent authority plane by implication.