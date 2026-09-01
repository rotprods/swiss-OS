# W5.1 — TARGET-BOUND APPLICATION READINESS

Status: implementation candidate / NO-SEND.

## Why

W5 correctly separated stable application identity from version-specific packet identity, but its initial compiler only required Candidate Truth + approved lane assets. It did not consume AAG-3.1 and therefore could compile a packet for an arbitrary `opportunity_id` without proving vacancy semantic validity, temporal validity, employer/property scope, mandatory-requirement extraction or application-route correctness.

A second gap existed in AAG itself: an AAG-3.1 receipt was not target-bound. A READY receipt could theoretically be replayed against another organization/opportunity/lane/channel.

## W5.1 contract

Before `compile_packet()` can succeed it now requires a `TARGET-BOUND-APPLICATION-READINESS-1.0` receipt built from:

- exact organization ID;
- exact opportunity ID;
- exact lane;
- exact selected channel;
- exact target role;
- exact HTTPS vacancy URL;
- exact full AAG-3.1 receipt SHA-256.

The AAG receipt must be `APPLICATION_READY_NO_SEND` or `ELITE_MATCH`, contain no blockers, preserve `OUTBOUND=CLOSED` / `send_allowed=0`, and prove the complete AAG-3.1 16-hard-gate set as terminal PASS.

Any target mismatch fails closed. W5.1 requires an exact opportunity ID; generic/spontaneous applications require a separately explicit policy/compiler rather than silently sharing vacancy-specific semantics.

## Identity model

`application_id` / `idempotency_key` remain stable over:

```text
organization + opportunity + lane + channel
```

They intentionally do NOT include CV revision, AAG refresh or packet assets. Revalidating AAG or replacing a CV therefore cannot authorize a duplicate application.

`packet_id` is the sole version identity and is content-addressed over:

```text
stable application key
+ target-bound readiness binding
+ exact primary asset identity/version/hash
+ exact supplemental asset identities/version/hashes
```

A new AAG evaluation, CV revision, portfolio revision or case-study revision may produce a new packet version while preserving the same application identity. No secondary uniqueness constraint is allowed to collapse distinct packet versions.

## Persistence

`applications_v2` remains the stable target/idempotency ledger. Its selected-asset fields are compatibility summary metadata; the exact packet version is reconstructed from the packet receipt ledger.

`application_packet_receipts_v1` is additive and stores exact version-specific packet/readiness provenance:

- packet ID;
- application ID;
- readiness binding SHA;
- AAG receipt SHA;
- target role / vacancy URL;
- primary asset manifest ID + version + SHA-256;
- selected channel;
- deterministic public-safe JSON of supplemental asset IDs/types/versions/SHA-256 values;
- `PACKET_COMPILED_NO_SEND` state.

`packet_id` is the table primary key and the only packet-version uniqueness boundary. This permits a refreshed AAG, portfolio or case-study to produce a new auditable packet without changing the stable application or authorizing a second outbound action.

No private storage refs, message body, PII, Gmail mutation or outbound action is persisted by this module.

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

1. Candidate Asset Manifest approval drift has been reconciled from final QA receipts: `CV_ENTRY_V2` and `CV_HYBRID_V2` are now explicitly `APPROVED_ASSET_V2` on the private control plane.
2. Recompile the recovered 436-hotel vacancy evidence through Wave 3.1/3.2 and select a real ENTRY target after first-party ownership/requirements/channel recheck.
3. Build AAG-3.1 for that exact target.
4. Perform one private ENTRY dry-run through W5.1, persisting only public-safe receipt metadata and no outbound.
5. Then execute W6 Response/Outcome Engine over historical Swiss replies.
