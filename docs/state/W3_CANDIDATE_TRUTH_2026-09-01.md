# W3 — CANDIDATE TRUTH / ASSET FOUNDATION — 2026-09-01

Closure state: **COMPLETE_READ_ONLY FOUNDATION / ASSET BUILD NEXT**

## Live Candidate Canon observation

Re-read from `HOTELS_MASTER/CANDIDATE_CANON_V2` on 2026-09-01:
- 21 canonical fields present (CF01..CF21)
- email approved for external use
- phone stored as verified private reference, external use approved without public value exposure
- exact language wording approved
- relocation/start availability approved
- LinkedIn URL approved with recheck-before-render semantics
- founder/operator assertion remains evidence-gated and externally disallowed

No private phone value or other private Candidate Canon payload is persisted in this public repository.

## Implemented

- `src/swiss_os/candidate_truth.py`
  - executable lane requirements for ENTRY/HYBRID/CREATIVE/PORTAL
  - truth states VERIFIED/UNKNOWN/CONFLICT
  - external claim/approval invariants
  - lane gate result with exact missing/blocked keys
  - public-safe aggregate summary
- `src/swiss_os/candidate_assets.py`
  - versioned asset manifest contract
  - CV_MASTER/CV_ENTRY/CV_HYBRID/CV_CREATIVE/PORTFOLIO/CASE_STUDY types
  - DRAFT/QA_PENDING/APPROVED/DEPRECATED states
  - content SHA-256 support
  - public-safe receipts that never expose private storage references
- adversarial unittest coverage for ENTRY independence from creative assets, missing CV blocker, HYBRID asset requirements, unverified claim rejection, private-reference safety, invalid hash rejection and deterministic manifests.

## Current operational interpretation

Candidate factual readiness is materially stronger than historical handoffs suggested. For ENTRY, core factual inputs are present; the principal remaining candidate-side gate is creation, QA and approval of the final `CV_ENTRY_V2` asset. HYBRID/CREATIVE additionally require their portfolio/case-study asset stack.

This is a control-plane interpretation only. Do not open outbound until all independent market/channel/suppression/idempotency/authorization gates pass.

## Next route

1. reconstruct private candidate evidence needed for CV content without copying PII into public GitHub;
2. compile `CV_MASTER_V2` content model;
3. derive ENTRY/HYBRID/CREATIVE variants;
4. render in private artifact storage;
5. extracted-text/ATS/link/visual QA;
6. register hashes/manifests;
7. mark lane asset gates only after approval;
8. proceed to Email Identity OS / HTML signature.

Safety delta: no outbound; no Gmail mutation; no authority hotel mutation; no private PII committed.
