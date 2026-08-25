from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


class ManifestError(ValueError):
    """Raised when a persisted operational manifest violates declared semantics."""


@dataclass(frozen=True)
class OperationalManifest:
    release: str
    generated_at: str
    run_id: str
    sheet_physical_hotel_rows: int
    superseded_duplicate_ids: tuple[str, ...]
    active_canonical_hotels: int
    identity_registry_rows: int | None
    sqlite_integrity_check: str
    foreign_key_violations: int
    checkpoint_id: str | None
    checkpoint_target: int | None
    checkpoint_current: int | None
    checkpoint_state: str | None
    outbound: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "OperationalManifest":
        checkpoint_raw = raw.get("checkpoint")
        checkpoint = checkpoint_raw if isinstance(checkpoint_raw, dict) else {}
        return cls(
            release=str(raw.get("release", "")),
            generated_at=str(raw.get("generated_at", "")),
            run_id=str(raw.get("run_id", "")),
            sheet_physical_hotel_rows=int(raw.get("sheet_physical_hotel_rows", raw.get("checks", {}).get("sheets_canonical_count", 0))),
            superseded_duplicate_ids=tuple(raw.get("superseded_duplicate_ids") or ()),
            active_canonical_hotels=int(raw.get("active_canonical_hotels", raw.get("checks", {}).get("canonical_unique", 0))),
            identity_registry_rows=(int(raw["identity_registry_rows"]) if raw.get("identity_registry_rows") is not None else None),
            sqlite_integrity_check=str(raw.get("sqlite_integrity_check", raw.get("checks", {}).get("integrity_check", ""))),
            foreign_key_violations=int(raw.get("foreign_key_violations", raw.get("checks", {}).get("foreign_key_violations", 0))),
            checkpoint_id=checkpoint.get("id") if checkpoint else (str(checkpoint_raw) if checkpoint_raw else None),
            checkpoint_target=(int(checkpoint["target"]) if checkpoint.get("target") is not None else None),
            checkpoint_current=(int(checkpoint["current"]) if checkpoint.get("current") is not None else None),
            checkpoint_state=checkpoint.get("state"),
            outbound=raw.get("outbound"),
        )

    @classmethod
    def load(cls, path: str | Path) -> "OperationalManifest":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def expected_active_from_physical(self) -> int:
        return self.sheet_physical_hotel_rows - len(set(self.superseded_duplicate_ids))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.release:
            errors.append("release is required")
        if not self.run_id:
            errors.append("run_id is required")
        if self.sheet_physical_hotel_rows < 0 or self.active_canonical_hotels < 0:
            errors.append("hotel counts cannot be negative")
        if len(self.superseded_duplicate_ids) != len(set(self.superseded_duplicate_ids)):
            errors.append("superseded_duplicate_ids contains duplicate IDs")
        for hotel_id in self.superseded_duplicate_ids:
            if not valid_hotel_id(hotel_id):
                errors.append(f"invalid superseded hotel_id: {hotel_id}")
        if self.active_canonical_hotels != self.expected_active_from_physical:
            errors.append(
                "active canonical count does not reconcile with physical rows minus superseded duplicates: "
                f"{self.active_canonical_hotels} != {self.sheet_physical_hotel_rows} - "
                f"{len(set(self.superseded_duplicate_ids))}"
            )
        if self.identity_registry_rows is not None and self.identity_registry_rows != self.active_canonical_hotels:
            errors.append(
                f"identity_registry_rows={self.identity_registry_rows} != active_canonical_hotels={self.active_canonical_hotels}"
            )
        if self.sqlite_integrity_check.lower() != "ok":
            errors.append(f"sqlite integrity_check is not ok: {self.sqlite_integrity_check}")
        if self.foreign_key_violations != 0:
            errors.append(f"foreign key violations: {self.foreign_key_violations}")
        if self.checkpoint_current is not None and self.checkpoint_current != self.active_canonical_hotels:
            errors.append(
                f"checkpoint current={self.checkpoint_current} != active canonical={self.active_canonical_hotels}"
            )
        return errors

    def require_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise ManifestError("; ".join(errors))

    def public_summary(self) -> dict[str, Any]:
        return {
            "release": self.release,
            "generated_at": self.generated_at,
            "run_id": self.run_id,
            "physical_rows": self.sheet_physical_hotel_rows,
            "active_canonical": self.active_canonical_hotels,
            "superseded_duplicate_ids": list(self.superseded_duplicate_ids),
            "integrity_check": self.sqlite_integrity_check,
            "foreign_key_violations": self.foreign_key_violations,
            "checkpoint": {
                "id": self.checkpoint_id,
                "current": self.checkpoint_current,
                "target": self.checkpoint_target,
                "state": self.checkpoint_state,
            },
        }


def valid_hotel_id(value: str) -> bool:
    if not isinstance(value, str) or not value.startswith("H-"):
        return False
    suffix = value[2:]
    return len(suffix) == 4 and suffix.isdigit()
