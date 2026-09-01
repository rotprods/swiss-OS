# W5.1 — TARGET-BOUND APPLICATION READINESS

Status: implementation candidate / NO-SEND.

## Why

W5 correctly separated stable application identity from version-specific packet identity, but its initial compiler only required Candidate Truth + approved lane assets. It did not consume AAG-3.1 and therefore could compile a packet for an arbitrary `opportunity_id` without proving vacancy semantic validity, temporal validity, employer/property scope, mandatory-requirement extraction or application-route correctness.

Two replay gaps also existed:

1. an AAG-3.1 READY receipt was not bound to a specific organization/opportunity/lane/channel;
2. even after target binding, the same receipt could become stale if Candidate Truth, vacancy evidence or the evaluated CV/portfolio/case-study set changed.

## W5.1 contract

Before `compile_packet()` can succeed it requires a `TARGET-BOUND-APPLICATION-READINESS-1.0` receipt built from:

- exact organization ID;
- exact opportunity ID;
- exact lane;
- exact selected channel;
- exact target role;
- exact HTTPS vacancy URL;
- exact private Candidate Truth snapshot SHA-256;
- exact vacancy-evidence bundle SHA-256;
- exact public-safe evaluated asset-set SHA-256;
- exact full AAG-3.1 receipt SHA-256.

The AAG receipt must be `APPLICATION_READY_NO_SEND` or `ELITE_MATCH`, contain no blockers, preserve `OUTBOUND=CLOSED` / `send_allowed=0`, and prove the complete AAG-3.1 16-hard-gate set as terminal PASS.

Any target or input mismatch fails closed. The packet compiler recomputes the selected asset-set digest and rejects a readiness receipt evaluated against an older CV/portfolio/case-study version. Candidate Truth and vacancy-evidence digests are opaque content-addressed references supplied by the private/evidence control planes and must match exactly.

W5.1 requires an exact opportunity ID; generic/spontaneous applications require a separately explicit policy/compiler rather than silently sharing vacancy-specific semantics.

## Identity model

`application_id` / `idempotency_key` remain stable over:

```text
organization + opportunity + lane + channel
```

They intentionally do NOT include CV revision, Candidate Truth revision, vacancy-evidence refresh or AAG refresh. Revalidation therefore cannot authorize a duplicate application.

`packet_id` is the sole version identity and is content-addressed over:

```text
stable application key
+ target/input-bound readiness binding
+ exact primary asset identity/version/hash
+ exact supplemental asset identities/version/hashes
```

A legitimate Candidate Truth/evidence/AAG/asset refresh may produce a new packet version while preserving the same application identity. An old readiness receipt may not be reused after any evaluated input changes.

## Asset invariant

`APPROVED` candidate assets must carry a valid `content_sha256`. Draft/QA-pending assets may remain unhashed, but an approved unhashed asset is invalid and cannot enter packet compilation.

## Persistence

`applications_v2` remains the stable target/idempotency ledger. Its selected-asset fields are compatibility summary metadata; exact packet provenance lives in the packet receipt ledger.

`application_packet_receipts_v1` stores exact version-specific provenance:

- packet ID and stable application ID;
- readiness binding SHA and AAG receipt SHA;
- Candidate Truth snapshot SHA;
- vacancy-evidence bundle SHA;
- evaluated asset-set SHA;
- target role / vacancy URL;
- primary asset manifest ID + version + SHA-256;
- selected channel;
- deterministic public-safe JSON of supplemental asset IDs/types/versions/SHA-256 values;
- `PACKET_COMPILED_NO_SEND` state.

`packet_id` is the table primary key and the only packet-version uniqueness boundary. A refreshed AAG, CV, portfolio or case study can therefore produce another auditable packet version without changing the stable application or authorizing a second outbound action.

No private storage refs, message body, raw Candidate Truth, PII, Gmail mutation or outbound action is persisted by this module.

## Safety

```text
PACKET_COMPILED != SEND_AUTHORIZED
OUTBOUND = CLOSED
send_allowed = 0
final_send_ready = FALSE
hotel authority writes = 0
H-ID allocation/reservation = 0
```

## NEXT after merge

1. Candidate Asset Manifest approval drift has been reconciled from final QA receipts: `CV_ENTRY_V2` and `CV_HYBRID_V2` are explicitly `APPROVED_ASSET_V2` on the private control plane.
2. Recompile the recovered 436-hotel vacancy evidence through Wave 3.1/3.2 and select a real ENTRY target after first-party ownership/requirements/channel recheck.
3. Produce exact Candidate Truth, vacancy-evidence and selected-asset digests and build AAG-3.1 for that target.
4. Perform one private ENTRY dry-run through W5.1, persisting only public-safe receipt metadata and no outbound.
5. Then execute W6 Response/Outcome Engine over historical Swiss replies.
