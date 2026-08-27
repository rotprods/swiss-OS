# SV2-059 / V16 — 25-Entity Exact-Detail Canary

Status: **VALIDATED LOCAL CANARY — NON-AUTHORITATIVE**  
Authoritative control-plane state remains **E4 / 686 active / H-0691 next**.  
Outbound remains **CLOSED** and `send_allowed = 0`.

## Why this exists

The Drive/Sheets write plane became unavailable before Batch05 could be committed through the complete synchronization contract. Work therefore continued as a constrained local acceleration artifact only. No local ID is reserved and no authoritative counter is advanced.

## Batch05 exact-detail set

```text
H-0691  Hotel City Inn — Basel
H-0692  Hotel City Zürich — Zürich
H-0693  Hotel City Lugano - Hospitality & design — Lugano
H-0694  Hotel Continental — Zermatt
H-0695  Hotel Crowne Plaza — Zürich
H-0696  Hotel Crusch Alba — Zernez
H-0697  Hotel Crusch Alva — Zuoz
H-0698  Hotel Crystal — Interlaken
H-0699  Hotel Crystal — St. Moritz
H-0700  Hotel Crystal Engelberg — Engelberg
H-0701  Hôtel d'Allèves — Genève
H-0702  Hotel Daniela — Zermatt
H-0703  Hotel David 22 — St. Gallen
H-0704  Hôtel D'Angleterre — Genève
H-0705  Hotel Des Alpes — Flims Waldhaus
H-0706  Hotel des Alpes — Adelboden
H-0707  Hotel des Alpes — Luzern
H-0708  Hotel des Alpes by Bruno Kernen — Saanenmöser
H-0709  Hotel Derby Interlaken - Action & Relax Hub — Interlaken
H-0710  Hôtel des Arts — Neuchâtel
H-0711  Hôtel des Horlogers - Vallée de Joux — Le Brassus
H-0712  Hôtel des Innovations — Marly
H-0713  Hôtel des Patients de Lausanne — Lausanne
H-0714  Hotel Delfino Lugano — Lugano
H-0715  Hôtel de la Rose — Fribourg
```

Every row is explicitly `CANARY_CURRENT_RECONCILED_NOT_AUTHORITATIVE` in the local constrained database.

## V16 validation

```text
physical rows                                  715
candidate entities excluding four aliases     711
Batch05 exact-detail candidates                 25
aliases                                           4
SQLite integrity_check                          ok
foreign-key violations                            0
physical ID gaps                                  0
normalized name+city duplicates                   0
non-empty canonical-domain duplicates             0
idempotency replay new inserts                     0
external actions                                  0
send_allowed                                      0
restore operational tables compared              63
restore logical differences                        0
```

V16 canary SHA-256:

`8fc0b8201f7ff7b1885b143c9ce5d8b16218c7934d2ea4daad3f5ccd6c3b8350`

V16 restore SHA-256:

`fb1c6fa5304af7a2cba66c730196f2bb97a69045438d2f36385c3db09e7d4b63`

The binary SHAs may differ because physical SQLite page serialization is not the restore-equivalence invariant. Logical restore equivalence is zero-difference across all 63 operational tables.

## Authority projection — informational only

If the live Drive authority is later re-read, none of these identities collide with an intervening commit, and the full synchronized commit succeeds, the resulting projection would be:

```text
active canonical        711
physical rows           715
CP-0750                 711 / 750
remaining                39
next physical ID        H-0716
```

**These are projection values, not current authority.**

## Deliberately unresolved fields

For `H-0704..H-0715`, canonical domains are left unresolved unless an exact property website was explicitly recovered. A generic `Website` label on a source page is not enough to infer a domain.

Crowne Plaza Zürich retains the earlier field-level quarantine for conflicting room counts across localized HotellerieSuisse pages. Identity remains resolved while the disputed field remains unset.

## Required commit chain

Before any promotion:

```text
REHYDRATE LIVE DRIVE/SHEETS
→ ANTI-JOIN ALL 25 IDENTITIES + ALIASES + DOMAINS
→ REALLOCATE IDs IF NECESSARY
→ CONSTRAINED DB COMMIT
→ SHEETS PK MIRROR
→ INTELLIGENCE L1
→ GRAPH V2
→ ENTITY EPOCH
→ METRICS / HEALTH / SLO
→ CHECKPOINT / SCHEDULER
→ STATE TRANSITIONS / RUN LOG
→ PERSISTENT HANDOFF
```

If another agent has consumed `H-0691+`, this local allocation is stale. Reuse of provisional IDs without rehydration is forbidden.
