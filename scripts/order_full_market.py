#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

SCOPE_ORDER = {
    "SWITZERLAND_VERIFIED": 0,
    "SWITZERLAND_OR_UNKNOWN": 1,
    "UNKNOWN_AFTER_DETAIL_PARSE": 2,
    "LIECHTENSTEIN_LIKELY": 8,
    "LIECHTENSTEIN_VERIFIED": 9,
    "OUT_OF_SCOPE_VERIFIED": 10,
}
RESOLUTION_ORDER = {
    "MATCHED_EXISTING_CANONICAL": 0,
    "NEW_ENTITY_CANDIDATE": 1,
    "PENDING_CANONICAL_ANTIJOIN": 2,
    "ALIAS_OR_DUPLICATE_REVIEW": 3,
    "QUARANTINED": 9,
}
TYPE_ORDER = {
    "HOTEL": 0,
    "LODGE_OR_SWISS_LODGE": 1,
    "SERVICED_APARTMENTS": 2,
    "HOSTEL": 3,
    "GUESTHOUSE": 4,
    "UNKNOWN_PENDING_DETAIL": 5,
}


def rank_key(r):
    return (
        SCOPE_ORDER.get(r.get("country_scope", ""), 5),
        RESOLUTION_ORDER.get(r.get("entity_resolution_state", ""), 5),
        TYPE_ORDER.get(r.get("accommodation_type_hint", ""), 5),
        (r.get("canonical_name_candidate") or "").casefold(),
        (r.get("city_candidate") or "").casefold(),
        r.get("discovery_id") or "",
    )


def band(r) -> str:
    scope = r.get("country_scope", "")
    resolution = r.get("entity_resolution_state", "")
    typ = r.get("accommodation_type_hint", "")
    if scope.startswith("LIECHTENSTEIN") or scope == "OUT_OF_SCOPE_VERIFIED": return "P4_SCOPE_REVIEW"
    if resolution == "QUARANTINED": return "P4_QUARANTINE"
    if resolution == "ALIAS_OR_DUPLICATE_REVIEW": return "P2_IDENTITY_REVIEW"
    if resolution == "MATCHED_EXISTING_CANONICAL": return "P0_EXISTING_CANONICAL"
    if resolution == "NEW_ENTITY_CANDIDATE" and typ == "HOTEL": return "P0_NEW_HOTEL_CANDIDATE"
    if resolution == "NEW_ENTITY_CANDIDATE": return "P1_NEW_ACCOMMODATION_CANDIDATE"
    return "P1_RESOLUTION_PENDING"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = list(csv.DictReader(Path(args.input).open(encoding="utf-8")))
    rows.sort(key=rank_key)
    for i, row in enumerate(rows, 1):
        row["market_order"] = i
        row["priority_band"] = band(row)
        row["priority_semantics"] = "OPERATING_ORDER_NOT_HIRING_PROBABILITY"
    fields = list(rows[0].keys()) if rows else []
    with Path(args.out).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"ordered_entities={len(rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
