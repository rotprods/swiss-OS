from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit


_WS_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return _WS_RE.sub(" ", value.strip()).casefold()


def normalize_url(value: str) -> str:
    """Normalize a source/detail URL without treating page number as identity."""

    raw = value.strip()
    if not raw:
        return ""
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, parts.query, ""))


@dataclass(frozen=True)
class SnapshotSourceRecord:
    source_url: str
    raw_name: str
    raw_city: str
    detail_url: str = ""
    provider_record_key: str = ""

    def stable_source_record_key(self) -> str:
        """Return a snapshot-scoped record key seed.

        Prefer an explicit provider key, then an exact detail URL. If neither exists,
        use source surface + normalized name/city. Page position alone is never used.
        """

        provider_key = self.provider_record_key.strip()
        if provider_key:
            return f"provider:{provider_key}"

        detail = normalize_url(self.detail_url)
        if detail:
            return f"detail:{detail}"

        surface = normalize_url(self.source_url)
        name = normalize_text(self.raw_name)
        city = normalize_text(self.raw_city)
        if not surface or not name:
            raise ValueError(
                "record needs provider_record_key, detail_url, or source_url + non-empty name"
            )
        return f"fallback:{surface}|{name}|{city}"


def build_snapshot_record_id(snapshot_id: str, record: SnapshotSourceRecord) -> str:
    snapshot = snapshot_id.strip()
    if not snapshot:
        raise ValueError("snapshot_id is required")
    seed = f"{snapshot}|{record.stable_source_record_key()}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()[:24]
    return f"SR-{digest}"


@dataclass(frozen=True)
class SnapshotFreezeCandidate:
    snapshot_id: str
    locale: str
    source_url: str
    expected_pages: int
    observed_pages: int
    declared_raw_records: int
    materialized_records: int
    duplicate_source_record_keys: int = 0
    unresolved_snapshot_conflicts: int = 0
    missing_record_identity: int = 0


@dataclass(frozen=True)
class SnapshotFreezeResult:
    eligible: bool
    violations: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"eligible": self.eligible, "violations": list(self.violations)}


def validate_snapshot_freeze(candidate: SnapshotFreezeCandidate) -> SnapshotFreezeResult:
    """Fail-closed eligibility check for promoting a snapshot to FROZEN_VERIFIED.

    This validates structural completeness only. A caller must still persist the
    snapshot and evidence lineage through the authority-eligible wave contract.
    """

    violations: list[str] = []
    if not candidate.snapshot_id.strip():
        violations.append("snapshot_id is required")
    if not candidate.locale.strip():
        violations.append("locale is required")
    if not normalize_url(candidate.source_url):
        violations.append("source_url is required")

    for name, value in {
        "expected_pages": candidate.expected_pages,
        "observed_pages": candidate.observed_pages,
        "declared_raw_records": candidate.declared_raw_records,
        "materialized_records": candidate.materialized_records,
        "duplicate_source_record_keys": candidate.duplicate_source_record_keys,
        "unresolved_snapshot_conflicts": candidate.unresolved_snapshot_conflicts,
        "missing_record_identity": candidate.missing_record_identity,
    }.items():
        if value < 0:
            violations.append(f"{name} must be non-negative")

    if candidate.expected_pages <= 0:
        violations.append("expected_pages must be greater than zero")
    if candidate.declared_raw_records <= 0:
        violations.append("declared_raw_records must be greater than zero")
    if candidate.observed_pages != candidate.expected_pages:
        violations.append("all pages in the selected snapshot must be observed")
    if candidate.materialized_records != candidate.declared_raw_records:
        violations.append("materialized source records must equal declared raw records")
    if candidate.duplicate_source_record_keys != 0:
        violations.append("duplicate source record keys must be zero")
    if candidate.unresolved_snapshot_conflicts != 0:
        violations.append("unresolved snapshot conflicts must be zero")
    if candidate.missing_record_identity != 0:
        violations.append("every source record must have stable snapshot-scoped identity")

    return SnapshotFreezeResult(eligible=not violations, violations=tuple(violations))
