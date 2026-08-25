from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    scope_id: str
    task_type: str
    priority: int
    freshness_key: str = ""
    dependency_ids: tuple[str, ...] = ()
    reason_code: str | None = None


def has_active_task(conn: sqlite3.Connection, spec: TaskSpec) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM scheduler_tasks
        WHERE scope_id = ? AND task_type = ? AND freshness_key = ?
          AND state IN ('READY','ACTIVE')
        LIMIT 1
        """,
        (spec.scope_id, spec.task_type, spec.freshness_key),
    ).fetchone()
    return row is not None


def completed_for_freshness(conn: sqlite3.Connection, spec: TaskSpec) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM scheduler_tasks
        WHERE scope_id = ? AND task_type = ? AND freshness_key = ?
          AND state = 'COMPLETE'
        LIMIT 1
        """,
        (spec.scope_id, spec.task_type, spec.freshness_key),
    ).fetchone()
    return row is not None


def enqueue_if_needed(conn: sqlite3.Connection, spec: TaskSpec) -> bool:
    if has_active_task(conn, spec) or completed_for_freshness(conn, spec):
        return False
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO scheduler_tasks(
            task_id, scope_id, task_type, priority, state, freshness_key,
            dependency_ids_json, reason_code, created_at
        ) VALUES (?, ?, ?, ?, 'READY', ?, ?, ?, ?)
        """,
        (
            spec.task_id,
            spec.scope_id,
            spec.task_type,
            spec.priority,
            spec.freshness_key,
            json.dumps(spec.dependency_ids),
            spec.reason_code,
            now,
        ),
    )
    return True
