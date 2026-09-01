from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

LANE_REQUIREMENTS: dict[str, frozenset[str]] = {
    "ENTRY": frozenset({"contact.email", "contact.phone", "language.wording", "availability.start", "asset.cv"}),
    "HYBRID": frozenset({"contact.email", "contact.phone", "language.wording", "availability.start", "social.linkedin", "asset.cv", "asset.portfolio", "asset.case_studies"}),
    "CREATIVE": frozenset({"contact.email", "contact.phone", "language.wording", "availability.start", "social.linkedin", "asset.cv", "asset.portfolio", "asset.case_studies"}),
    "PORTAL": frozenset({"contact.email", "contact.phone", "language.wording", "availability.start", "asset.cv"}),
}

ALLOWED_TRUTH_STATES = frozenset({"VERIFIED", "UNKNOWN", "CONFLICT"})


@dataclass(frozen=True)
class CandidateField:
    key: str
    truth_state: str
    approved: bool
    external_allowed: bool
    private_reference: bool = False

    def validate(self) -> None:
        if not self.key.strip():
            raise ValueError("candidate field key required")
        if self.truth_state not in ALLOWED_TRUTH_STATES:
            raise ValueError(f"invalid truth state: {self.truth_state}")
        if self.truth_state != "VERIFIED" and self.external_allowed:
            raise ValueError("unverified/conflicted fields cannot be externally allowed")
        if self.external_allowed and not self.approved:
            raise ValueError("external field must be approved")


@dataclass(frozen=True)
class LaneGateResult:
    lane: str
    ready: bool
    missing: tuple[str, ...]
    blocked: tuple[str, ...]


def evaluate_lane(lane: str, fields: Iterable[CandidateField]) -> LaneGateResult:
    if lane not in LANE_REQUIREMENTS:
        raise ValueError(f"unknown lane: {lane}")
    by_key = {f.key: f for f in fields}
    for f in by_key.values():
        f.validate()

    missing: list[str] = []
    blocked: list[str] = []
    for key in sorted(LANE_REQUIREMENTS[lane]):
        field = by_key.get(key)
        if field is None:
            missing.append(key)
            continue
        if field.truth_state != "VERIFIED" or not field.approved or not field.external_allowed:
            blocked.append(key)

    return LaneGateResult(
        lane=lane,
        ready=not missing and not blocked,
        missing=tuple(missing),
        blocked=tuple(blocked),
    )


def claim_is_renderable(field: CandidateField) -> bool:
    field.validate()
    return field.truth_state == "VERIFIED" and field.approved and field.external_allowed


def public_safe_summary(fields: Iterable[CandidateField]) -> dict[str, int]:
    rows = list(fields)
    for f in rows:
        f.validate()
    return {
        "total": len(rows),
        "verified": sum(f.truth_state == "VERIFIED" for f in rows),
        "unknown": sum(f.truth_state == "UNKNOWN" for f in rows),
        "conflict": sum(f.truth_state == "CONFLICT" for f in rows),
        "externally_allowed": sum(f.external_allowed for f in rows),
        "private_reference_count": sum(f.private_reference for f in rows),
    }
