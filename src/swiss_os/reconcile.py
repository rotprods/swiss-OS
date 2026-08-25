from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .invariants import active_ids, duplicate_ids, numeric_id_gaps


@dataclass(frozen=True)
class ReconciliationReport:
    physical_count: int
    physical_unique: int
    active_count: int
    db_active_count: int
    duplicates: tuple[str, ...]
    missing_in_db: tuple[str, ...]
    extra_in_db: tuple[str, ...]
    physical_id_gaps: tuple[str, ...]
    superseded_missing_from_physical: tuple[str, ...]

    @property
    def exact(self) -> bool:
        return not any(
            (
                self.duplicates,
                self.missing_in_db,
                self.extra_in_db,
                self.physical_id_gaps,
                self.superseded_missing_from_physical,
            )
        ) and self.active_count == self.db_active_count


def reconcile_ids(
    physical_ids: Iterable[str],
    db_active_ids: Iterable[str],
    superseded_ids: Iterable[str] = (),
) -> ReconciliationReport:
    physical_list = list(physical_ids)
    physical_set = set(physical_list)
    superseded_set = set(superseded_ids)
    expected_active = active_ids(physical_set, superseded_set)
    db_set = set(db_active_ids)
    return ReconciliationReport(
        physical_count=len(physical_list),
        physical_unique=len(physical_set),
        active_count=len(expected_active),
        db_active_count=len(db_set),
        duplicates=tuple(sorted(duplicate_ids(physical_list))),
        missing_in_db=tuple(sorted(expected_active - db_set)),
        extra_in_db=tuple(sorted(db_set - expected_active)),
        physical_id_gaps=tuple(numeric_id_gaps(physical_set)),
        superseded_missing_from_physical=tuple(sorted(superseded_set - physical_set)),
    )
