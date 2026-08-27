#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


def norm_text(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.casefold().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def domain(value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    host = (urlparse(value).hostname or "").casefold()
    return host.removeprefix("www.")


def url_path(value: str | None) -> str:
    if not value:
        return ""
    return urlparse(value).path.rstrip("/").casefold()


def detail_slug(value: str | None) -> str:
    path = url_path(value)
    if not path:
        return ""
    slug = path.rsplit("/", 1)[-1]
    return slug if slug.startswith("hotel-") and not slug.startswith("hotel-page-") else ""


def load_canonical(db_path: Path):
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    aliases = {r["alias_hotel_id"]: r["canonical_hotel_id"] for r in con.execute("select alias_hotel_id, canonical_hotel_id from hotel_aliases")}
    hotels = [dict(r) for r in con.execute("select * from hotels order by hotel_id")]
    con.close()
    active = [h for h in hotels if h["hotel_id"] not in aliases and not str(h.get("state") or "").startswith("SUPERSEDED_DUPLICATE")]
    return hotels, active, aliases


def build_indexes(active):
    by_path = defaultdict(list)
    by_slug = defaultdict(list)
    by_domain = defaultdict(list)
    by_name_city = defaultdict(list)
    by_name = defaultdict(list)
    for h in active:
        hp = url_path(h.get("hotelleriesuisse_url"))
        hs = detail_slug(h.get("hotelleriesuisse_url"))
        if hp:
            by_path[hp].append(h)
        if hs:
            by_slug[hs].append(h)
        d = domain(h.get("canonical_domain") or h.get("official_website"))
        if d:
            by_domain[d].append(h)
        n = norm_text(h.get("canonical_name"))
        c = norm_text(h.get("city"))
        if n:
            by_name[n].append(h)
        if n and c:
            by_name_city[(n, c)].append(h)
    return by_path, by_slug, by_domain, by_name_city, by_name


def reconcile(row, indexes):
    by_path, by_slug, by_domain, by_name_city, by_name = indexes
    name = row.get("canonical_name_candidate", "")
    city = row.get("city_candidate", "")
    detail = row.get("detail_url", "")
    official = row.get("official_website", "")
    matches = []
    reasons = []

    p = url_path(detail)
    s = detail_slug(detail)
    if p and by_path.get(p):
        matches.extend(by_path[p]); reasons.append("EXACT_T1_DETAIL_PATH")
    if s and by_slug.get(s):
        matches.extend(by_slug[s]); reasons.append("EXACT_T1_DETAIL_SLUG")
    d = domain(official)
    if d and by_domain.get(d):
        matches.extend(by_domain[d]); reasons.append("EXACT_DOMAIN")
    key = (norm_text(name), norm_text(city))
    if key[0] and key[1] and by_name_city.get(key):
        matches.extend(by_name_city[key]); reasons.append("EXACT_NORMALIZED_NAME_CITY")

    dedup = {m["hotel_id"]: m for m in matches}
    if len(dedup) == 1:
        h = next(iter(dedup.values()))
        return "MATCHED_EXISTING_CANONICAL", h["hotel_id"], "|".join(sorted(set(reasons))), 1.0
    if len(dedup) > 1:
        return "ALIAS_OR_DUPLICATE_REVIEW", "|".join(sorted(dedup)), "MULTIPLE_STRONG_KEYS", 0.4

    name_matches = by_name.get(norm_text(name), []) if name else []
    if name_matches:
        cities = sorted({m.get("city") or "" for m in name_matches})
        return "ALIAS_OR_DUPLICATE_REVIEW", "|".join(m["hotel_id"] for m in name_matches), "NAME_COLLISION_OTHER_CITY:" + ";".join(cities), 0.6

    return "NEW_ENTITY_CANDIDATE", "", "NO_STRONG_CANONICAL_MATCH", 0.9


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discovery", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    discovery_path = Path(args.discovery)
    db_path = Path(args.db)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    _, active, aliases = load_canonical(db_path)
    indexes = build_indexes(active)
    rows = list(csv.DictReader(discovery_path.open(encoding="utf-8")))
    resolved = []
    counts = Counter()
    reason_counts = Counter()
    for row in rows:
        state, canonical_id, reason, confidence = reconcile(row, indexes)
        counts[state] += 1
        for reason_key in reason.split("|") if reason else []:
            reason_counts[reason_key.split(":",1)[0]] += 1
        resolved.append({
            **row,
            "entity_resolution_state": state,
            "canonical_match_id": canonical_id,
            "resolution_reason": reason,
            "resolution_confidence": confidence,
        })

    fields = list(resolved[0].keys()) if resolved else []
    with (out / "discovery_reconciled.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(resolved)

    manifest = {
        "schema": "SWISS_OS_DISCOVERY_RECONCILIATION_V1_1",
        "discovery_rows": len(rows),
        "active_canonical_rows": len(active),
        "alias_rows": len(aliases),
        "resolution_counts": dict(counts),
        "resolution_reason_counts": dict(reason_counts),
        "new_entities_are_not_promoted": True,
        "route_prefix_migration_tolerated_by_detail_slug": True,
        "outbound": "CLOSED",
    }
    (out / "reconciliation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
