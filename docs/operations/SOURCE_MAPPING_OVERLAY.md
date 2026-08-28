# SOURCE MAPPING OVERLAY — SMO-1.0

Status: **PRE-AUTHORITY / REPLAYABLE TERMINAL-MAPPING DELTA**

SMO-1.0 converts explicitly reviewed `MATCH_EXISTING` source-resolution decisions into a deterministic overlay on a pinned `CRM-SOURCE-MAPPING-CANDIDATE-1.0` parent without mutating canonical authority.

## Allowed transition

```text
RECONCILE_REQUIRED -> ACTIVE_CANONICAL
```

A transition is accepted only when the review packet is `READY_FOR_SRR_APPLICATION`, the source snapshot matches, `current_evidence_verified=true`, the canonical target is a valid H-ID, evidence/reason are non-empty, and `authority_action=NONE_PREAUTH_REVIEW`.

The overlay records the parent candidate SHA, exact source keys, target H-IDs, evidence and effective source-mapping counts. It is a replayable overlay while the full 2061-record source-mapping materialization is being recovered. It does **not** rewrite the base artifact or operational authority.

## Hard invariants

```text
authority_advanced = false
h_id_allocations = 0
crm_universe_complete = false
OUTBOUND = CLOSED
send_allowed = 0
```

SMO-1.0 never supports `CREATE_NEW`, H-ID reservation, exclusion inference, alias creation, or authority promotion. New-entity and alias decisions require their own evidence and authority-eligible transaction.

## Materialization rule

`effective_terminal_mappings` and `effective_reconcile_required` are valid for the pinned base plus the validated overlay. Before source-scope completion or any authority candidate, the full source mapping must be deterministically rebuilt/replayed and validated so every frozen source record has exactly one terminal or unresolved state.

Implementation: `src/swiss_os/source_mapping_overlay.py`.
