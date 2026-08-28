from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from urllib.parse import urlsplit

from .snapshot_freeze import SnapshotSourceRecord, build_snapshot_record_id, normalize_text, normalize_url


ACTIVE_MATCH = "ACTIVE_MATCH"
ALIAS_MATCH = "ALIAS_MATCH"
TRUE_MISSING = "TRUE_MISSING"
CONFLICT = "CONFLICT"
EXCLUSION_CANDIDATE = "EXCLUSION_CANDIDATE"

STAGING_CLASSES = {ACTIVE_MATCH, ALIAS_MATCH, TRUE_MISSING, CONFLICT, EXCLUSION_CANDIDATE}


@dataclass(frozen=True)
class CanonicalIdentity:
    hotel_id: str
    canonical_name: str
    city: str
    canonical_domain: str = ""


@dataclass(frozen=True)
class AliasIdentity:
    canonical_hotel_id: str
    alias_name: str
    alias_city: str = ""


@dataclass(frozen=True)
class IngestDecision:
    snapshot_record_id: str
    snapshot_id: str
    source_record_key: str
    staging_class: str
    matched_hotel_id: str | None
    reason_code: str
    normalized_name: str
    normalized_city: str
    normalized_detail_url: str

    def as_dict(self) -> dict[str, object]:
        return {
            "snapshot_record_id": self.snapshot_record_id,
            "snapshot_id": self.snapshot_id,
            "source_record_key": self.source_record_key,
            "staging_class": self.staging_class,
            "matched_hotel_id": self.matched_hotel_id,
            "reason_code": self.reason_code,
            "normalized_name": self.normalized_name,
            "normalized_city": self.normalized_city,
            "normalized_detail_url": self.normalized_detail_url,
        }


def _hostname(url: str) -> str:
    normalized = normalize_url(url)
    if not normalized:
        return ""
    host = urlsplit(normalized).hostname or ""
    return host.removeprefix("www.").casefold()


def _canonical_indexes(canonical: list[CanonicalIdentity]) -> tuple[dict[str, set[str]], dict[tuple[str, str], set[str]]]:
    by_domain: dict[str, set[str]] = {}
    by_name_city: dict[tuple[str, str], set[str]] = {}
    for row in canonical:
        domain = row.canonical_domain.strip().casefold().removeprefix("www.")
        if domain:
            by_domain.setdefault(domain, set()).add(row.hotel_id)
        key = (normalize_text(row.canonical_name), normalize_text(row.city))
        by_name_city.setdefault(key, set()).add(row.hotel_id)
    return by_domain, by_name_city


def _alias_index(aliases: list[AliasIdentity]) -> dict[tuple[str, str], set[str]]:
    result: dict[tuple[str, str], set[str]] = {}
    for row in aliases:
        key = (normalize_text(row.alias_name), normalize_text(row.alias_city))
        result.setdefault(key, set()).add(row.canonical_hotel_id)
    return result


def classify_source_record(
    snapshot_id: str,
    record: SnapshotSourceRecord,
    canonical: list[CanonicalIdentity],
    aliases: list[AliasIdentity],
) -> IngestDecision:
    """Classify one source record without allocating a canonical H-ID.

    Precedence is deterministic and fail-closed:
    exact domain -> exact canonical name+city -> exact alias -> true missing.
    Multiple distinct candidates at any matching layer become CONFLICT.
    """
    snapshot_record_id = build_snapshot_record_id(snapshot_id, record)
    source_record_key = record.stable_source_record_key()
    name = normalize_text(record.raw_name)
    city = normalize_text(record.raw_city)
    detail = normalize_url(record.detail_url)

    if not name:
        return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, EXCLUSION_CANDIDATE, None, "EMPTY_NORMALIZED_NAME", name, city, detail)

    by_domain, by_name_city = _canonical_indexes(canonical)
    aliases_by_name_city = _alias_index(aliases)

    domain = _hostname(record.detail_url)
    if domain and domain in by_domain:
        candidates = by_domain[domain]
        if len(candidates) == 1:
            hotel_id = next(iter(candidates))
            return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, ACTIVE_MATCH, hotel_id, "EXACT_CANONICAL_DOMAIN", name, city, detail)
        return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, CONFLICT, None, "AMBIGUOUS_CANONICAL_DOMAIN", name, city, detail)

    key = (name, city)
    canonical_candidates = by_name_city.get(key, set())
    if canonical_candidates:
        if len(canonical_candidates) == 1:
            hotel_id = next(iter(canonical_candidates))
            return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, ACTIVE_MATCH, hotel_id, "EXACT_CANONICAL_NAME_CITY", name, city, detail)
        return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, CONFLICT, None, "AMBIGUOUS_CANONICAL_NAME_CITY", name, city, detail)

    alias_candidates = aliases_by_name_city.get(key, set())
    if alias_candidates:
        if len(alias_candidates) == 1:
            hotel_id = next(iter(alias_candidates))
            return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, ALIAS_MATCH, hotel_id, "EXACT_ALIAS_NAME_CITY", name, city, detail)
        return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, CONFLICT, None, "AMBIGUOUS_ALIAS_NAME_CITY", name, city, detail)

    return IngestDecision(snapshot_record_id, snapshot_id, source_record_key, TRUE_MISSING, None, "NO_EXACT_IDENTITY_MATCH", name, city, detail)


def load_identity_reference(conn: sqlite3.Connection) -> tuple[list[CanonicalIdentity], list[AliasIdentity]]:
    canonical = [
        CanonicalIdentity(
            hotel_id=str(r[0]), canonical_name=str(r[1]), city=str(r[2]), canonical_domain=str(r[3] or "")
        )
        for r in conn.execute(
            "SELECT hotel_id, canonical_name, city, canonical_domain FROM canonical_hotels WHERE state = 'ACTIVE'"
        )
    ]
    aliases = [
        AliasIdentity(str(r[0]), str(r[1]), str(r[2] or ""))
        for r in conn.execute(
            "SELECT canonical_hotel_id, alias_name, alias_city FROM entity_aliases"
        )
    ]
    return canonical, aliases


def classify_batch(conn: sqlite3.Connection, snapshot_id: str, records: list[SnapshotSourceRecord]) -> list[IngestDecision]:
    canonical, aliases = load_identity_reference(conn)
    return [classify_source_record(snapshot_id, record, canonical, aliases) for record in records]


def stage_decisions(conn: sqlite3.Connection, decisions: list[IngestDecision], observed_at: str) -> None:
    """Persist non-authoritative staging decisions idempotently by snapshot record PK."""
    for d in decisions:
        if d.staging_class not in STAGING_CLASSES:
            raise ValueError(f"invalid staging class: {d.staging_class}")
        conn.execute(
            """
            INSERT INTO crm_ingest_staging (
                snapshot_record_id, snapshot_id, source_record_key, staging_class,
                matched_hotel_id, reason_code, normalized_name, normalized_city,
                normalized_detail_url, observed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_record_id) DO UPDATE SET
                staging_class = excluded.staging_class,
                matched_hotel_id = excluded.matched_hotel_id,
                reason_code = excluded.reason_code,
                normalized_name = excluded.normalized_name,
                normalized_city = excluded.normalized_city,
                normalized_detail_url = excluded.normalized_detail_url,
                observed_at = excluded.observed_at
            """,
            (
                d.snapshot_record_id, d.snapshot_id, d.source_record_key, d.staging_class,
                d.matched_hotel_id, d.reason_code, d.normalized_name, d.normalized_city,
                d.normalized_detail_url, observed_at,
            ),
        )
    conn.commit()


def staging_metrics(decisions: list[IngestDecision]) -> dict[str, int]:
    metrics = {name: 0 for name in sorted(STAGING_CLASSES)}
    for d in decisions:
        metrics[d.staging_class] += 1
    metrics["TOTAL"] = len(decisions)
    metrics["H_ID_ALLOCATIONS"] = 0
    return metrics
