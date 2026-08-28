from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class CoverageTask:
    task_key: str
    locale: str
    epoch: str
    page: int
    priority: int
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "task_key": self.task_key,
            "locale": self.locale,
            "epoch": self.epoch,
            "page": self.page,
            "priority": self.priority,
            "reason": self.reason,
        }


def build_directory_coverage_plan(
    observations: Iterable[Mapping[str, Any]],
    *,
    locale: str,
    epoch: str,
    expected_pages: int,
    conflict_pages: Iterable[int] = (),
) -> dict[str, object]:
    locale = locale.strip().lower()
    epoch = epoch.strip()
    if not locale or not epoch:
        raise ValueError("locale and epoch are required")
    if expected_pages <= 0:
        raise ValueError("expected_pages must be positive")

    observed_pages: set[int] = set()
    foreign_scope = 0
    for item in observations:
        item_locale = str(item.get("locale", "") or "").strip().lower()
        item_epoch = str(item.get("epoch", "") or "").strip()
        raw_page = item.get("page")
        if raw_page in (None, ""):
            continue
        page = int(raw_page)
        if page <= 0:
            raise ValueError("page must be positive")
        if item_locale == locale and item_epoch == epoch:
            observed_pages.add(page)
        else:
            foreign_scope += 1

    invalid_observed = sorted(p for p in observed_pages if p > expected_pages)
    observed_pages = {p for p in observed_pages if p <= expected_pages}
    conflicts = sorted({int(p) for p in conflict_pages if int(p) > 0 and int(p) <= expected_pages})
    missing = sorted(set(range(1, expected_pages + 1)).difference(observed_pages))

    tasks: list[CoverageTask] = []
    for page in conflicts:
        tasks.append(CoverageTask(
            task_key=f"DIRECTORY:{epoch}:{locale}:PAGE:{page}:CONFLICT",
            locale=locale,
            epoch=epoch,
            page=page,
            priority=950,
            reason="SNAPSHOT_CONFLICT_EXACT_CURRENT_REFRESH",
        ))
    for page in missing:
        if page in conflicts:
            continue
        tasks.append(CoverageTask(
            task_key=f"DIRECTORY:{epoch}:{locale}:PAGE:{page}:MISSING",
            locale=locale,
            epoch=epoch,
            page=page,
            priority=900,
            reason="MISSING_PAGE_EXACT_CURRENT_REFRESH",
        ))

    tasks.sort(key=lambda task: (-task.priority, task.page, task.task_key))
    return {
        "locale": locale,
        "epoch": epoch,
        "expected_pages": expected_pages,
        "observed_pages": len(observed_pages),
        "missing_pages": missing,
        "conflict_pages": conflicts,
        "invalid_observed_pages": invalid_observed,
        "foreign_scope_observations": foreign_scope,
        "coverage_pct": round((len(observed_pages) / expected_pages) * 100.0, 4),
        "complete": len(missing) == 0 and len(conflicts) == 0 and not invalid_observed,
        "tasks": [task.as_dict() for task in tasks],
    }
