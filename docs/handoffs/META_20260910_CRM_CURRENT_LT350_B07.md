# META — CRM CURRENT <0.35 B07 — 2026-09-10

Authority: `HS_ENTITY_EPOCH_2026-08-25_E4` / `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`  
Claim: `CLAIM-CRM-ENTITY-RESOLUTION-016` / fencing token 16  
Execution mode: PREAUTH SRR decision only  
Hotel authority effect: NONE  
Outbound: CLOSED

## Material result

B07 consumed the durable current-evidence packet and the 2026-09-02 comparator review.

```text
B07 reviewed                                      10
NEW_CANONICAL_PREAUTH                              9
NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED             1
relationship candidates preserved separately       2
terminal mapping delta                              0
H-ID allocation / reservation                       0
current <0.35 reviewed cumulative                  70
cumulative NEW_CANONICAL preauthority             183
historical <0.35 tail remaining                  1219
zero-exact-city lane remaining                    415
terminal source mappings                          658
RECONCILE_REQUIRED                               1403
```

All ten rows remain `RECONCILE_REQUIRED`. `NEW_CANONICAL_PREAUTH` is a typed preauthority identity decision, not permission to create a canonical row.

## EGR / relationship exceptions

- `Ô Pied-à-Terre Motel-Résidence Sàrl` is preserved as `ACCOMMODATION_MOTEL_RESIDENCE`; conventional-hotel coercion is forbidden.
- `Mövenpick Hôtel Genève` is distinct from canonical `H-0614 Mövenpick Hotel Lausanne`; shared brand/operator is relationship metadata only.
- `Hotel Nessi` preserves `La Rocca Living Hotel Group` membership separately from property identity.

## Next safe action

Recompute B08 from the frozen 2061-record source snapshot and exact E4/690 canonical catalog. Do not select B08 merely by taking the next lexical source keys because zero-same-city membership is a derived anti-join property.

Required sequence:

```text
recover frozen source snapshot
+ recover/re-read E4 canonical catalog
→ recompute zero-exact-city lane
→ subtract B01..B07 exact keys
→ select next 10 deterministically
→ current-source evidence
→ canonical comparator/locality review
→ EGR/group/operator review
→ PREAUTH decisions
→ gauntlet
```

If the E4 catalog cannot be recovered exactly, stop at `BLOCKED_COMPARATOR_AUTHORITY`; do not fabricate B08.

## Hard invariants

- `H-0691` remains unallocated.
- Authority remains E4/690.
- No canonical ID reservation.
- No terminal mapping is created by this review wave.
- `CRM_UNIVERSE_COMPLETE = FALSE`.
- `OUTBOUND = CLOSED`; `send_allowed = 0`.
- Similarity is candidate generation, never identity authority.
