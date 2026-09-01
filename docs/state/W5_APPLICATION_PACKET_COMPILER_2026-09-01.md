# W5 — APPLICATION PACKET COMPILER

Status: implementation candidate; outbound remains CLOSED.

## Contract

The compiler is a metadata/state compiler, not a sender. It converts an organization/opportunity + lane + verified candidate fields + approved private asset manifests + selected channel into one deterministic application packet identity.

It reuses existing W3 contracts instead of defining parallel truth semantics:
- `candidate_truth.evaluate_lane()` is the lane gate.
- `candidate_assets.AssetManifest` is the asset authority contract.
- `applications_v2` is the persistence target.

## Selection

- ENTRY -> exactly one approved `CV_ENTRY`.
- PORTAL -> exactly one approved `CV_ENTRY`.
- HYBRID -> exactly one approved `CV_HYBRID` + one approved PORTFOLIO + one approved CASE_STUDY.
- CREATIVE -> exactly one approved `CV_CREATIVE` + one approved PORTFOLIO + one approved CASE_STUDY.

Multiple approved primary assets fail closed. The compiler never invents a 'latest version' rule from version strings.

## Idempotency

Application identity is a SHA-256 over organization, optional opportunity, lane, primary asset, supplemental assets and channel. Recompiling the same input yields the same packet/application/idempotency identity.

`persist_application()` writes metadata only to `applications_v2`; it performs no rendering, Gmail mutation, browser action or outbound send. A repeated identical idempotency key is a no-op.

## Current real-world gate

Private `CV_ENTRY_V2` and `CV_HYBRID_V2` have passed PDF QA. HYBRID remains intentionally blocked for real packet compilation until an approved claim-linked portfolio and case-study asset exist. ENTRY can be dry-run compiled once the approved private asset manifests are represented to the compiler by the runtime.

## Safety

- Public PII: 0
- Sends: 0
- Gmail mutations: 0
- Hotel authority writes: 0
- Outbound: CLOSED
