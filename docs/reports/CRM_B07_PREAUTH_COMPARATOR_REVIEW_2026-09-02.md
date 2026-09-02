# CRM B07 preauthority comparator review — 2026-09-02

Status: **RESEARCH-ONLY / NON-AUTHORITATIVE**

This report advances the current `CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION` route without mutating hotel authority, entity-resolution state, H-ID allocation, outbound state, or any canonical sheet. It consumes the already-persisted B07 current-evidence packet and performs a fresh read-only comparison against the canonical `HOTELS_V2` / `HOTEL_GROUPS_V2` / `ENTITY_RESOLUTION` surfaces in Drive plus selected first-party current sources.

## Safety boundary

- Source universe remains `HS-MEMBER-DE-33339392661` — 2061 records / 172 pages.
- E4 authority remains 690 active canonical entities.
- `H-0691` remains unallocated.
- `CRM_UNIVERSE_COMPLETE = FALSE`.
- `OUTBOUND = CLOSED`; `send_allowed = 0`.
- This file creates **no** SRR disposition, terminal mapping, canonical reservation, H-ID, Sheet mutation, or authority advancement.
- Only a later fenced CRM writer may persist formal `MATCH_EXISTING / RELATIONSHIP / NEW_CANONICAL / UNRESOLVED` decisions.

## Inputs

- `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B06_2026-08-31.json`
- `docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B07_EVIDENCE_PACKET_2026-09-01.json`
- Drive `HOTELS_MASTER` / `HOTELS_V2` / `HOTEL_GROUPS_V2` / `ENTITY_RESOLUTION`, read-only on 2026-09-02.

The canonical comparison scanned `HOTELS_V2!A1:T1000`. This covers the complete 690-entity E4 population and additional historical/reconcile rows. Absence from the scan is therefore strong negative evidence for an existing canonical candidate, but never by itself authorizes creation.

## B07 comparator result

| source_record_key | property | locality | pre-review result | comparator / EGR notes |
|---|---|---|---|---|
| `MD-21cc675b7ddb4fb39c9a` | Hotel Restaurant Hammer | Eigenthal | `NEW_CANONICAL_PREAUTH_CANDIDATE` | No `Hammer` canonical candidate found. Existing first-party B07 evidence confirms an operating Eigenthal property. |
| `MD-21d80dc6cd95557824af` | Panoramahotel Braunwald | Braunwald | `NEW_CANONICAL_PREAUTH_CANDIDATE` | No Braunwald canonical candidate found. Current B07 evidence identifies the property in the 2026 Glarnerland accommodation directory. |
| `MD-2371d6a62dfb46d25297` | Hotel Nidwaldnerhof direkt am See Swiss Quality | Beckenried | `NEW_CANONICAL_PREAUTH_CANDIDATE` | No `Nidwaldnerhof` or Beckenried canonical candidate found. First-party address/booking evidence is distinct. |
| `MD-23cc9ed081909afb8a76` | Hôtel de La Vue-des-Alpes | La Vue-des-Alpes | `NEW_CANONICAL_PREAUTH_CANDIDATE` | No Vue-des-Alpes canonical candidate found. Current first-party + destination evidence agrees on locality/property. |
| `MD-23d989d03ab52258efd9` | Hotel Münsterhof | Müstair | `NEW_CANONICAL_PREAUTH_CANDIDATE` | No `Münsterhof` or Müstair canonical candidate found. Preserve Val Müstair locality semantics during formal SRR review. |
| `MD-246d25ab845005abc642` | CIP Hôtel | Tramelan | `NEW_CANONICAL_PREAUTH_CANDIDATE` | No Tramelan canonical candidate found. A raw `CIP` substring search produced a false positive on `PARK HOTEL PRINCIPE`, demonstrating why substring/fuzzy matching cannot bind identity. |
| `MD-2503eb358ae6e9c901a7` | Ô Pied-à-Terre Motel-Résidence Sàrl | Poliez-Pittet | `NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED` | No Poliez-Pittet canonical candidate found. First-party site explicitly describes a bookable **Motel Résidence** with equipped rooms. Treat as `ACCOMMODATION/MOTEL_RESIDENCE`; do not coerce to conventional hotel identity. |
| `MD-262dc840666b01355485` | Boutique Hôtel Corbetta | Les Paccots | `NEW_CANONICAL_PREAUTH_CANDIDATE` | No `Corbetta` or Les Paccots canonical candidate found. B07 first-party + Fribourg tourism evidence identifies one current property. |
| `MD-2646d4114c7721222c87` | Mövenpick Hôtel Genève | Genève 15 Aéroport | `NEW_CANONICAL_PREAUTH_CANDIDATE + GROUP_RELATION_REVIEW` | `HOTELS_V2` contains `H-0614 Mövenpick Hotel Lausanne`, not Genève. First-party Mövenpick/Accor pages show distinct addresses: Route de Pré-Bois 20, Geneva vs Avenue de Rhodanie 4, Lausanne. Never alias them. Candidate shared brand/operator relation should be modeled separately. |
| `MD-267556b17b23beb697d5` | Hotel Nessi | Locarno | `NEW_CANONICAL_PREAUTH_CANDIDATE + GROUP_RELATION_REVIEW` | No Nessi canonical candidate or existing ENTITY_RESOLUTION row found. First-party site states Hotel Nessi is part of **La Rocca Living Hotel Group** and names Boutique Hotel La Rocca / Parkhotel Emmaus as other group facilities. Create property identity separately from group/operator relation. |

## Aggregate pre-review

```text
B07 input                                  10
existing canonical property matches        0
new canonical preauth candidates            9
new accommodation / EGR-required            1
candidate group/operator relations           2
terminal mappings created                    0
H-ID allocations / reservations              0
Drive / Sheets writes                        0
authority advanced                           FALSE
```

## Important negative evidence

- `HOTELS_V2` contains many Geneva hotels, but no Mövenpick Geneva. The only Mövenpick canonical row found is `H-0614` in Lausanne.
- A locality search found no canonical rows for Beckenried, Müstair, Les Paccots, Tramelan, Poliez-Pittet or Braunwald in the E4 scan.
- Locarno search surfaces `@Home Hotel Locarno` in Muralto; this is not evidence that Hotel Nessi is the same property.
- `HOTEL_GROUPS_V2` did not yet contain a Mövenpick or La Rocca group record in the bounded scan, suggesting two group-graph enrichment gaps, not property aliases.
- `ENTITY_RESOLUTION` spot checks for Mövenpick and Nessi returned no prior resolution rows.

## Formal next action

A future eligible CRM claim should consume this report together with the B07 evidence packet and execute a **bounded SRR/EGR materialization wave**:

1. re-read live main, E4 authority and current source snapshot;
2. re-check all ten source identities against current canonical state;
3. preserve Mövenpick/La Rocca as relationship candidates, never alias evidence;
4. preserve Ô Pied-à-Terre as a non-conventional accommodation entity type;
5. persist typed preauthority decisions only;
6. allocate/reserve no H-ID;
7. update terminal mappings only through the separately authorized DB-first cross-plane transaction;
8. keep outbound closed.

This report is intentionally safe to discard/recompute if a newer authority snapshot contradicts it.
