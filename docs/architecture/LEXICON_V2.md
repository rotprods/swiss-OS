# LEXICON V2 — AUTHORITY VOCABULARY

Status: **V2 CANDIDATE CANONICAL LEXICON**

| Term | Canonical meaning | Anti-example |
|---|---|---|
| PROPOSED | Designed, not executed. | Calling a plan implemented. |
| IMPLEMENTED | Code/contract exists. | Claiming runtime effect. |
| EXECUTED | Operation ran. | Claiming correctness. |
| VERIFIED | Named invariant/test passed. | Claiming user/business success. |
| EMPIRICALLY_QUALIFIED | Outcome evidence supports behavior. | Unit-test pass. |
| AUTHORITY_ELIGIBLE | Promotion gates are satisfied/evaluable. | Valid local canary. |
| AUTHORITATIVE | Fully synchronized promoted operational state. | Staging/cache/Library. |
| PREAUTHORITY | Evidence/mapping can inform promotion but cannot mutate authority. | Canonical ID allocation. |
| COMPLETE_READ_ONLY | Bounded non-authority wave completed. | Authority advanced. |
| COMPLETE_AUTHORITY | Cross-plane authority promotion reconciled. | DB-only write. |
| RECONCILE_REQUIRED | Truth cannot safely advance yet. | “Probably fine”. |
| CONTEXT_FRESH | ContextPack fence exactly equals live fence. | Recently generated pack. |
| CLAIMED | Session owns a valid scope lease. | Branch exists. |
| FENCED | Writer token equals current fencing token. | Lease timestamp alone. |
| SUPERSEDED | Historical truth replaced prospectively, lineage retained. | Deleting history. |
| READY | Named prerequisites for a specific layer passed. | Global send authorization. |
| OUTBOUND_CLOSED | Irreversible external action forbidden. | Research forbidden. |

Bare `complete`, `ready`, `verified` and `active` are deprecated in architecture/operating contracts unless the object and authority layer are explicit.