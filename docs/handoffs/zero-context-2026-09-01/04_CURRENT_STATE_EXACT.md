# CURRENT STATE — EXACT HANDOFF SNAPSHOT

## Git
Repository: `rotprods/swiss-OS`  
Main SHA: `6ca946e61d6145424ff06754831a567d6e2b2f3e`  
Latest main merge: PR #405 — AAG-3.1 vacancy-provenance hard gates.

## Hotel authority
Authority epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`  
Authority SHA: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`

```text
physical HOTELS rows     690
active canonical         690
next ID                  H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE    FALSE
OUTBOUND                 CLOSED
send_allowed             0
```

## Current coherent source
```text
snapshot                 HS-MEMBER-DE-33339392661
run                      33339392661
artifact                 9740219406
records                  2061
pages                    172
coverage_complete        TRUE
terminal mappings        658
unique canonical targets 656
RECONCILE_REQUIRED       1403
reverse authority gaps   34
```

## Entity-resolution frontier
```text
candidate lineage                    1438/1438
current <0.35 reviewed               60
historical <0.35 remaining           1229
zero-city lane remaining             425
NEW_CANONICAL_PREAUTH cumulative     174
H-ID allocations                     0
H-ID reservations                    0
```

## Durable NEXT on main
Route: `CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B07`

Exact source keys:
- MD-21cc675b7ddb4fb39c9a
- MD-21d80dc6cd95557824af
- MD-2371d6a62dfb46d25297
- MD-23cc9ed081909afb8a76
- MD-23d989d03ab52258efd9
- MD-246d25ab845005abc642
- MD-2503eb358ae6e9c901a7
- MD-262dc840666b01355485
- MD-2646d4114c7721222c87
- MD-267556b17b23beb697d5

## Concurrency
PR #404 is open. It claims B07/token7 work but is not authority. Revalidate against fresh main before merge or rebuild.

## Application state
Merged application work includes PRs #395, #397, #398, #399, #400, #401, #403 and #405.

```text
market records             2061
official sites             1705
careers routes              611
current-opening hotels      436
spontaneous signals         121
explicit no-openings          9
vacancy detail coverage     436/436
AAG-3.1 hard gates           16/16 required
```

## Safety
```text
CRM_UNIVERSE_COMPLETE      FALSE
OUTBOUND                   CLOSED
send_allowed               0
irreversible actions       0
```
