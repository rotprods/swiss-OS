from __future__ import annotations

import hashlib
import sqlite3

from .mass_ingest import CONFLICT, EXCLUSION_CANDIDATE, TRUE_MISSING, IngestDecision
from .scheduler import TaskSpec, enqueue_if_needed

TASK_BY_CLASS = {
    TRUE_MISSING: ("REFRESH_EXACT_CURRENT", 900, "TRUE_MISSING_REQUIRES_CURRENT_EVIDENCE"),
    CONFLICT: ("ENTITY_RESOLUTION", 950, "INGEST_IDENTITY_CONFLICT"),
    EXCLUSION_CANDIDATE: ("EXCLUSION_REVIEW", 850, "INGEST_EXCLUSION_CANDIDATE"),
}

def _task_id(snapshot_id: str, snapshot_record_id: str, task_type: str) -> str:
    digest = hashlib.sha256(f"{snapshot_id}|{snapshot_record_id}|{task_type}".encode()).hexdigest()[:20]
    return f"CRM-{digest}"

def task_for_decision(decision: IngestDecision) -> TaskSpec | None:
    config = TASK_BY_CLASS.get(decision.staging_class)
    if config is None:
        return None
    task_type, priority, reason_code = config
    return TaskSpec(task_id=_task_id(decision.snapshot_id, decision.snapshot_record_id, task_type), scope_id=decision.snapshot_record_id, task_type=task_type, priority=priority, freshness_key=decision.snapshot_id, reason_code=reason_code)

def enqueue_ingest_work(conn: sqlite3.Connection, decisions: list[IngestDecision]) -> dict[str, int]:
    created = skipped = no_task = 0
    by_type: dict[str, int] = {}
    for decision in decisions:
        spec = task_for_decision(decision)
        if spec is None:
            no_task += 1
            continue
        if enqueue_if_needed(conn, spec):
            created += 1
            by_type[spec.task_type] = by_type.get(spec.task_type, 0) + 1
        else:
            skipped += 1
    conn.commit()
    return {"CREATED": created, "SKIPPED_EXISTING_OR_COMPLETE": skipped, "NO_TASK_REQUIRED": no_task, **{f"CREATED_{k}": v for k, v in sorted(by_type.items())}}
