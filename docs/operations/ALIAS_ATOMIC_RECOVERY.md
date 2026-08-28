# ALIAS ATOMIC RECOVERY — SWITZERLAND_JOB_OS

Version: **AAR-1.0**  
Status: **RECOVERY / PRE-AUTHORITY HARD GATE**

## Objective

Repair issue `#89` without mutating the immutable parent, guessing a denominator, reusing an H-ID, or partially updating one persistence plane.

The recovery target is the four semantically invalid persisted edges:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

ASR-1.0 proves that each alias H-ID belongs to a different real-world hotel than its target.

## Immutable inputs

```text
OPERATIONAL_DB_SHADOW_MANIFEST_V13
SQLite SHA-256:
0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5

HOTELS_MASTER exact pre-repair backup/export
issue #89 lineage evidence
ASR_REPAIR_CANARY_2026-08-28_V1
docs/state/ASR_REPAIR_PLAN_V1.json
```

The parent database and original Sheet are rollback evidence. A canary is always written to a new path/file.

## Executable SQLite canary

```bash
swiss-os alias-repair sqlite-canary \
  switzerland_job_os_operational_shadow_v13.sqlite \
  docs/state/ASR_REPAIR_PLAN_V1.json \
  --out switzerland_job_os_operational_shadow_v14_alias_repair_canary.sqlite \
  --manifest asr_sqlite_canary_manifest.json
```

The command:

1. verifies the immutable parent SHA;
2. runs SQLite integrity and FK checks;
3. checks the exact four hotel states and alias edges;
4. copies the parent to a new file;
5. restores the four unrelated hotel rows;
6. deletes only the four exact invalid alias rows;
7. reruns integrity/FK;
8. replays the repair and requires zero further writes;
9. requires logical differences only in `hotels` and `hotel_aliases`;
10. emits no authority, H-ID or outbound permission.

It never edits the source database.

## Required live write surface

The live recovery is one bounded logical transaction:

```text
constrained DB
→ HOTELS_V2
→ HOTEL_INTELLIGENCE_V1
→ GRAPH_NODES_V2
→ GRAPH_EDGES_V2
→ ENTITY_RESOLUTION correction semantics
→ STATE_TRANSITIONS
→ GOAL_STATE / CHECKPOINT_REGISTRY
→ ENGINE_METRICS / ENGINE_HEALTH / SLO
→ EXECUTION_SCHEDULER_V2
→ RUN_LOG / recovery manifests
```

Required PK-keyed semantics:

- restore `H-0610`, `H-0624`, `H-0629`, `H-0630`;
- tombstone/remove only the four invalid `ALIASES_TO` edges;
- restore the four HOTEL→INTELLIGENCE relations;
- preserve `ER-CP0650-001..004` as research anti-join evidence while retracting the unrelated physical-H-ID supersession assertion;
- append corrective transitions rather than rewriting history;
- recompute every affected denominator from physical state.

Blind row-offset writes are prohibited.

## Promotion gate

`COMPLETE_AUTHORITY` requires all of:

```text
fresh GitHub ancestry
fresh V13 SHA verification
exact HOTELS_MASTER rollback artifact
all required write planes available
PK-keyed concurrency check immediately before write
ASR-1.0 alias_semantics_state = EXACT
SQLite integrity_check = ok
FK violations = 0
physical rows = 690
active invalid alias edges = 0
active HOTEL nodes = corrected active denominator
active INTEL nodes = corrected active denominator
active HAS_INTELLIGENCE edges = corrected active denominator
DB ↔ HOTELS_MASTER affected PKs = exact
metrics/checkpoints/scheduler/health/SLO = reconciled
restore/replay/idempotency = PASS
GitHub + Drive + Library recovery pointers = persisted
```

`690` is a canary prediction until that full gate passes.

## Fail-closed behavior

If any parent, rollback artifact, required plane, concurrency check or invariant fails:

```text
no partial live write
no numeric authority promotion
canonical H-ID allocation forbidden
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

Continue non-destructive preflight, lineage reconstruction and source-universe research under MEP fallback routes.

## Relationship to the wider CRM chain

After issue #89 is atomically repaired:

```text
fresh coherent HSLCA capture
→ PCF when provider count is absent
→ MDM
→ discover.swiss / SSR when credential exists
→ CMI
→ CWP
→ ECV
→ SMC
→ SRR
→ terminal source mappings
→ unmapped = 0
→ RECONCILE_REQUIRED = 0
→ CRM_UNIVERSE_COMPLETE
```

Outbound remains separately gated even after CRM completion.
