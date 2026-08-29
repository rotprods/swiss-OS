# PIE-1.1 — Provider Identity Enrichment

Status: read-only evidence extraction; pre-authority; review-only.

PIE enriches bounded SRET review packets from current HotellerieSuisse member-detail pages. It extracts candidate identity signals for later SRR review; it never decides canonical identity.

## Extracted evidence

- HTTP status, final provider URL and response SHA-256;
- external HTTP(S) link candidates, excluding provider/social/infrastructure hosts;
- Hotel/LodgingBusiness/Organization/LocalBusiness JSON-LD name, URL, telephone and structured address candidates.

Every extracted value remains a candidate. PIE does not label a domain as official and does not treat domain absence/difference as proof of novelty.

## Trust boundary

Input `detail_url` must be HTTPS on `hotelleriesuisse.ch`. Redirects are accepted only while remaining on that HTTPS provider origin; cross-origin redirects fail closed. Responses are capped at 2 MB. Work packets may not contain `canonical_hotel_id`, `matched_hotel_id` or `allocated_hotel_id`.

## Hard invariants

Every result carries `identity_decision=NONE_REVIEW_ONLY`, `terminal_mapping_allowed=false`, `canonical_id_reservation_allowed=false`, `authority_action=NONE`.

Packet invariants: `authority_advanced=false`, `h_id_allocations=0`, `crm_universe_complete=false`, `OUTBOUND=CLOSED`, `send_allowed=0`.

PIE evidence may support a later explicit SRR only after independent comparison with the canonical property's current identity. Similarity is review-space reduction, never authority.

## Run

```bash
python -m swiss_os.provider_identity_enrichment run docs/state/PROVIDER_IDENTITY_WORK_0001_33206402141.json --out provider-identity-enrichment.json
python -m swiss_os.provider_identity_enrichment validate provider-identity-enrichment.json
```

The GitHub Actions canary is read-only (`contents: read`) and uploads evidence artifacts only. It cannot mutate repository state or operational authority.
