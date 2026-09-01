from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3

NICHE_ID = "NICHE-001"


@dataclass(frozen=True)
class ProjectionRow:
    hotel_id: str
    organization_id: str
    canonical_name: str
    city: str
    canton: str | None
    country: str
    canonical_domain: str | None
    state: str
    source_ref: str
    identity_confidence: float | None

    @property
    def fingerprint(self) -> str:
        payload = {
            "hotel_id": self.hotel_id,
            "organization_id": self.organization_id,
            "canonical_name": self.canonical_name,
            "city": self.city,
            "canton": self.canton or "",
            "country": self.country,
            "canonical_domain": (self.canonical_domain or "").lower(),
            "state": self.state,
            "source_ref": self.source_ref,
            "identity_confidence": self.identity_confidence,
        }
        raw = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
        return hashlib.sha256(raw).hexdigest()


def organization_id_for_hotel(hotel_id: str) -> str:
    if len(hotel_id) != 6 or not hotel_id.startswith("H-") or not hotel_id[2:].isdigit():
        raise ValueError(f"invalid hotel id: {hotel_id}")
    return f"ORG-HOTEL-{hotel_id[2:]}"


def project_rows(conn: sqlite3.Connection) -> list[ProjectionRow]:
    rows = conn.execute(
        """SELECT hotel_id, canonical_name, city, canton, country,
                  canonical_domain, state, source_ref, identity_confidence
           FROM canonical_hotels
           ORDER BY hotel_id"""
    ).fetchall()
    return [
        ProjectionRow(
            hotel_id=r[0],
            organization_id=organization_id_for_hotel(r[0]),
            canonical_name=r[1],
            city=r[2],
            canton=r[3],
            country=r[4],
            canonical_domain=r[5],
            state=r[6],
            source_ref=r[7],
            identity_confidence=r[8],
        )
        for r in rows
    ]


def _organization_state(hotel_state: str) -> str:
    if hotel_state == "ACTIVE":
        return "ACTIVE"
    if hotel_state == "SUPERSEDED_DUPLICATE":
        return "SUPERSEDED"
    if hotel_state == "REMOVED_OR_STALE":
        return "REMOVED_OR_STALE"
    return "QUARANTINED"


def materialize_canary(conn: sqlite3.Connection, evidence_ref: str) -> int:
    """Materialize a deterministic, non-authoritative NICHE-001 projection.

    INSERT OR IGNORE is deliberate: reruns are idempotent, while pre-existing divergent
    rows are preserved so semantic_mismatches() exposes drift rather than overwriting it.
    """
    rows = project_rows(conn)
    for r in rows:
        conn.execute(
            """INSERT OR IGNORE INTO organizations(
                 organization_id, canonical_name, organization_type, canonical_domain,
                 country, state, source_ref, identity_confidence
               ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                r.organization_id,
                r.canonical_name,
                "HOTEL",
                r.canonical_domain,
                r.country,
                _organization_state(r.state),
                r.source_ref,
                r.identity_confidence,
            ),
        )
        conn.execute(
            """INSERT OR IGNORE INTO organization_niches(
                 organization_id,niche_id,relation_type,evidence_ref
               ) VALUES(?,?,?,?)""",
            (r.organization_id, NICHE_ID, "PRIMARY", evidence_ref),
        )
        conn.execute(
            """INSERT OR IGNORE INTO organization_locations(
                 location_id,organization_id,city,canton,country,evidence_ref
               ) VALUES(?,?,?,?,?,?)""",
            (
                f"LOC-{r.organization_id}",
                r.organization_id,
                r.city,
                r.canton,
                r.country,
                evidence_ref,
            ),
        )
        conn.execute(
            """INSERT OR IGNORE INTO legacy_hotel_org_bridge(
                 hotel_id,organization_id,bridge_state,evidence_ref
               ) VALUES(?,?,?,?)""",
            (r.hotel_id, r.organization_id, "CANARY", evidence_ref),
        )
    return len(rows)


def semantic_mismatches(conn: sqlite3.Connection) -> list[dict[str, str]]:
    query = """
    SELECT h.hotel_id,
           CASE
             WHEN b.hotel_id IS NULL THEN 'MISSING_BRIDGE'
             WHEN o.organization_id IS NULL THEN 'MISSING_ORGANIZATION'
             WHEN o.canonical_name <> h.canonical_name THEN 'NAME'
             WHEN COALESCE(l.city,'') <> COALESCE(h.city,'') THEN 'CITY'
             WHEN COALESCE(l.canton,'') <> COALESCE(h.canton,'') THEN 'CANTON'
             WHEN COALESCE(o.country,'') <> COALESCE(h.country,'') THEN 'COUNTRY'
             WHEN lower(COALESCE(o.canonical_domain,'')) <> lower(COALESCE(h.canonical_domain,'')) THEN 'DOMAIN'
             WHEN COALESCE(o.source_ref,'') <> COALESCE(h.source_ref,'') THEN 'SOURCE_REF'
             WHEN o.state <> CASE
                 WHEN h.state='ACTIVE' THEN 'ACTIVE'
                 WHEN h.state='SUPERSEDED_DUPLICATE' THEN 'SUPERSEDED'
                 WHEN h.state='REMOVED_OR_STALE' THEN 'REMOVED_OR_STALE'
                 ELSE 'QUARANTINED'
               END THEN 'STATE'
             ELSE NULL
           END mismatch
    FROM canonical_hotels h
    LEFT JOIN legacy_hotel_org_bridge b ON b.hotel_id=h.hotel_id
    LEFT JOIN organizations o ON o.organization_id=b.organization_id
    LEFT JOIN organization_locations l ON l.organization_id=o.organization_id
    ORDER BY h.hotel_id
    """
    return [
        {"hotel_id": hotel_id, "mismatch": mismatch}
        for hotel_id, mismatch in conn.execute(query)
        if mismatch
    ]


def compatibility_receipt(conn: sqlite3.Connection) -> dict[str, object]:
    hotels = conn.execute("SELECT COUNT(*) FROM canonical_hotels").fetchone()[0]
    orgs = conn.execute(
        """SELECT COUNT(*)
           FROM organizations o
           JOIN organization_niches n USING(organization_id)
           WHERE n.niche_id='NICHE-001'"""
    ).fetchone()[0]
    bridges = conn.execute("SELECT COUNT(*) FROM legacy_hotel_org_bridge").fetchone()[0]
    duplicate_targets = conn.execute(
        """SELECT COUNT(*) FROM (
             SELECT organization_id, COUNT(*) c
             FROM legacy_hotel_org_bridge
             GROUP BY organization_id HAVING c>1
           )"""
    ).fetchone()[0]
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk_violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    mismatches = semantic_mismatches(conn)
    return {
        "legacy_hotels": hotels,
        "niche001_organizations": orgs,
        "bridge_rows": bridges,
        "duplicate_bridge_targets": duplicate_targets,
        "semantic_mismatch_count": len(mismatches),
        "semantic_mismatches": mismatches,
        "integrity_check": integrity,
        "fk_violations": fk_violations,
        "pass": (
            hotels == orgs == bridges
            and duplicate_targets == 0
            and not mismatches
            and integrity == "ok"
            and fk_violations == 0
        ),
    }
