# PIE-1.0 — Provider Identity Enrichment

Status: read-only evidence extraction; pre-authority; review-only.

PIE enriches a bounded SRET review batch from the current HotellerieSuisse member-detail page with identity candidates that may support later human/agent review. It does **not** decide identity.

## Evidence extracted

- response SHA-256 and final provider URL;
- external HTTP(S) link candidates, excluding the provider itself and common social/infrastructure hosts;
- Hotel/LodgingBusiness/Organization/LocalBusiness JSON-LD name, URL, telephone and structured address candidates when the provider page exposes them.

All extracted values are candidates, not assertions. An external link is labeled `EXTERNAL_LINK_CANDIDATE_ONLY`; structured JSON-LD is labeled `STRUCTURED_PROVIDER_CANDIDATE_ONLY`.

## Hard invariants

Input work packets MUST NOT contain `canonical_hotel_id`, `matched_hotel_id` or `allocated_hotel_id`. Output packets never create any of those fields. Every result carries `identity_decision=NONE_REVIEW_ONLY`, `terminal_mapping_allowed=false`, `canonical_id_reservation_allowed=false`, `authority_action=NONE`.

Packet invariants: `authority_advanced=false`, `h_id_allocations=0`, `crm_universe_complete=false`, `OUTBOUND=CLOSED`, `send_allowed=0`.

PIE does not infer distinctness from domain absence or domain difference. An extracted domain/address can only become SRR evidence after independent corroboration against the canonical property's current identity. Similarity remains review-space reduction only.

## Run

```bash
python -m swiss_os.provider_identity_enrichment run \
  docs/state/PROVIDER_IDENTITY_WORK_0001_33206402141.json \
  --out /tmp/provider-identity-enrichment.json

python -m swiss_os.provider_identity_enrichment validate \
  /tmp/provider-identity-enrichment.json
```

A main-branch work packet matching `docs/state/PROVIDER_IDENTITY_WORK_*.json` triggers the read-only GitHub Actions canary. The Actions artifact is evidence only and cannot mutate repository state or authority.
