# ECV provider-record-change semantics

Status: active only after the defining PR is merged.

The exact-current verifier distinguishes transient acquisition failure from deterministic provider-record change without promoting either class into CRM authority.

## Normalized states

`CURRENT_DETAIL_VERIFIED` remains the only fully identity-verified detail state.

`CURRENT_DETAIL_URL_NOT_FOUND` means that the exact detail URL returned HTTP 404 on every bounded fetch attempt in the raw ECV packet. It is evidence about the provider detail URL only. It is **not** evidence that the hotel no longer exists, is novel to the CRM, should be excluded, should be aliased, or should receive a canonical H-ID.

`CURRENT_DETAIL_NAME_ONLY`, `CURRENT_DETAIL_CITY_ONLY`, and `CURRENT_DETAIL_MISMATCH` are deterministic identity-drift evidence when a current provider page responds but does not reproduce the expected name/city identity tuple.

Deterministic provider-record-change states route to `PROVIDER_RECORD_CHANGE_REVIEW`. Genuine transient or mixed fetch failures remain `FETCH_FAILED` and route to `REQUEUE_EXACT_CURRENT`.

## Terminal evidence vs verified identity

The additive field `all_terminal` answers whether every work item has a non-transient exact-current evidence state. It does not mean every hotel identity is verified and it does not imply source-to-canonical reconciliation is complete.

`all_verified` retains its original strict meaning: every item is `CURRENT_DETAIL_VERIFIED`.

Provider-record-change states may therefore permit the immutable exact-current scan to continue while those records remain in a separate entity/provider-change review queue.

## Authority locks

The normalizer rejects any packet that attempts to change these invariants:

```text
authority_advanced = false
h_id_allocations = 0
OUTBOUND = CLOSED
send_allowed = 0
```

No canonical IDs may be reserved from staging or provider evidence. No cache/canary state may advance authority. Provider-record-change evidence has no terminal canonical-mapping effect until entity resolution proves one.

## Bounded normalization rule

Only an error whose bounded fetch-attempt components are all explicit `HTTP Error 404: Not Found` responses is normalized to `CURRENT_DETAIL_URL_NOT_FOUND`. Mixed 404 + timeout, rate-limit, transport, robots or other errors remain transient failures.

Identity drift is normalized only from already typed successful-page states. The original response/error evidence is retained in the artifact.

## Pipeline

```text
raw exact-current fetch
→ EXACT-CURRENT-VERIFY-1.0 raw packet
→ ECV-PROVIDER-EVIDENCE-1.0 normalizer
→ existing packet validator + safety assertions
→ durable evidence artifact
→ provider-record-change review / entity resolution
```

The normalizer recomputes `counts_by_state`, `all_verified`, `all_terminal`, `terminal_evidence_count`, `provider_record_change_count`, and the canonical packet SHA-256. Existing `EXACT-CURRENT-VERIFY-1.0` schema and fail-closed authority locks remain intact.
