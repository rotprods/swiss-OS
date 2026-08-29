# ASR SQLite repair execution V1 — issue #89

Status: **CANARY_PASS_NON_AUTHORITY**

SRS-1.0 was executed against a fresh copy of the physically verified V13 parent and the issue #89 repair canary.

## Source

```text
parent                      OPERATIONAL_DB_SHADOW_MANIFEST_V13
source SQLite SHA-256       0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
repair target               ASR_REPAIR_CANARY_2026-08-28_V2
```

## Result

```text
repair spec built                 PASS
exact source SHA gate             PASS
schema signature gate             PASS
BEGIN IMMEDIATE transaction       PASS
exact-row preconditions           PASS
post-table count/hash gates       PASS
SQLite integrity                  ok
FK violations                     0
logical differences vs canary     0
second execution                  NOOP_ALREADY_APPLIED
backup created                    PASS
```

The spec and execution receipt are persisted outside the public repository because they contain complete operational row payloads:

```text
ASR_SQLITE_REPAIR_SPEC_V13_TO_V2.json
ASR_SQLITE_REPAIR_EXECUTION_RECEIPT_V1.json
ASR_SQLITE_REPAIR_REPLAY_V1.sqlite
ASR_SQLITE_REPAIR_REPLAY_V1_SOURCE_BACKUP.sqlite
```

## Authority boundary

This proves the constrained SQLite migration is deterministic and replay-safe. It does not repair HOTELS_MASTER, Intelligence, Operational Graph or observability and therefore cannot publish the projected repaired denominator.

```text
authority_advanced = false
canonical H-ID allocations = 0
CRM_UNIVERSE_COMPLETE = false
OUTBOUND = CLOSED
send_allowed = 0
```
