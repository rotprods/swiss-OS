from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .manifest import OperationalManifest, valid_hotel_id


@dataclass(frozen=True)
class InvariantResult:
    invariant_id: str
    passed: bool
    detail: str


def duplicate_ids(ids: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in ids:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return dupes


def numeric_id_gaps(ids: Iterable[str]) -> list[str]:
    numbers = sorted(int(v[2:]) for v in set(ids) if valid_hotel_id(v))
    if not numbers:
        return []
    present = set(numbers)
    return [f"H-{n:04d}" for n in range(numbers[0], numbers[-1] + 1) if n not in present]


def active_ids(physical_ids: Iterable[str], superseded_ids: Iterable[str]) -> set[str]:
    return set(physical_ids) - set(superseded_ids)


def run_manifest_invariants(manifest: OperationalManifest) -> list[InvariantResult]:
    errors = manifest.validate()
    return [
        InvariantResult("INV-MANIFEST-SEMANTICS", not errors, "PASS" if not errors else " | ".join(errors)),
        InvariantResult(
            "INV-DB-INTEGRITY",
            manifest.sqlite_integrity_check.lower() == "ok",
            f"integrity_check={manifest.sqlite_integrity_check}",
        ),
        InvariantResult(
            "INV-FK-ZERO",
            manifest.foreign_key_violations == 0,
            f"foreign_key_violations={manifest.foreign_key_violations}",
        ),
        InvariantResult(
            "INV-ACTIVE-PHYSICAL-SEPARATION",
            manifest.active_canonical_hotels == manifest.expected_active_from_physical,
            (
                f"physical={manifest.sheet_physical_hotel_rows}; "
                f"superseded={len(set(manifest.superseded_duplicate_ids))}; "
                f"active={manifest.active_canonical_hotels}"
            ),
        ),
    ]


def require_all(results: Iterable[InvariantResult]) -> None:
    failures = [r for r in results if not r.passed]
    if failures:
        raise RuntimeError("; ".join(f"{r.invariant_id}: {r.detail}" for r in failures))
