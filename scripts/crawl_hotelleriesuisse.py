#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE = "https://www.hotelleriesuisse.ch"
DIRECTORY = f"{BASE}/de/branche-und-politik/branchenverzeichnis"
PAGE = DIRECTORY + "/hotel-page-{page}"
ROBOTS = f"{BASE}/robots.txt"
UA = "swiss-os-public-market-research/1.0 (+https://github.com/rotprods/swiss-OS)"

ENGINES = [
    "discovery_engine", "entity_resolution_engine", "evidence_engine",
    "intelligence_engine", "vacancy_engine", "housing_engine", "people_engine",
    "channel_engine", "social_engine", "digital_audit_engine", "creative_audit_engine",
    "tech_engine", "group_engine", "opportunity_engine", "scoring_engine",
    "personalization_engine", "message_engine", "qa_engine", "graph_engine",
    "ttl_engine", "export_engine", "governance_engine",
]

LIECHTENSTEIN = {
    "vaduz", "schaan", "triesen", "balzers", "triesenberg", "ruggell", "eschen",
    "mauren", "gamprin", "schellenberg", "planken", "malbun",
}

DETAIL_PATTERNS = (
    "/branche-und-politik/branchenverzeichnis/hotel-",
    "/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis/hotel-",
    "/association-et-siege-admin/membres/liste-des-membres/hotel-",
)

@dataclass(frozen=True)
class Record:
    discovery_id: str
    canonical_name_candidate: str
    city_candidate: str
    detail_url: str
    directory_page: int
    source_tier: str
    membership_state: str
    entity_resolution_state: str
    country_scope: str
    accommodation_type_hint: str
    classification_basis: str
    observed_at: str


def norm(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip(" \t\r\n-|•")


def discovery_id(name: str, city: str, url: str) -> str:
    raw = f"{norm(name)}|{norm(city)}|{urlparse(url).path}"
    return "U-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def type_hint(name: str) -> str:
    n = norm(name)
    if "hostel" in n or "jugendherberge" in n:
        return "HOSTEL"
    if "aparthotel" in n or "apartment" in n or "serviced" in n:
        return "SERVICED_APARTMENTS"
    if "guesthouse" in n or "pension" in n:
        return "GUESTHOUSE"
    if any(x in n for x in ("lodge", "chalet", "hütte", "huette", "berghaus")):
        return "LODGE_OR_SWISS_LODGE"
    if "hotel" in n or "hôtel" in n or "gasthof" in n or "auberge" in n:
        return "HOTEL"
    return "UNKNOWN_PENDING_DETAIL"


def scope(city: str) -> str:
    return "LIECHTENSTEIN_LIKELY" if norm(city) in LIECHTENSTEIN else "SWITZERLAND_OR_UNKNOWN"


def get(session: requests.Session, url: str, retries: int = 4) -> str:
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=35, headers={"User-Agent": UA, "Accept-Language": "de-CH,de;q=0.9,en;q=0.7"})
            if r.status_code == 200:
                return r.text
            last = RuntimeError(f"HTTP {r.status_code} for {url}")
            if r.status_code not in {408, 425, 429, 500, 502, 503, 504}:
                break
        except requests.RequestException as exc:
            last = exc
        time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(str(last or f"failed {url}"))


def robots_ok(session: requests.Session) -> None:
    text = get(session, ROBOTS)
    rp = RobotFileParser()
    rp.set_url(ROBOTS)
    rp.parse(text.splitlines())
    if not rp.can_fetch(UA, DIRECTORY):
        raise RuntimeError("robots.txt disallows the directory for this crawler")


def observed_counts(html: str) -> tuple[int | None, int | None]:
    text = clean(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    result_count = None
    page_count = None
    for pat in (r"([0-9][0-9.'’\s]{2,})\s+(?:Ergebnisse|Resultate|results)", r"(?:Ergebnisse|Resultate|results)\s*[:\-]?\s*([0-9][0-9.'’\s]{2,})"):
        m = re.search(pat, text, re.I)
        if m:
            result_count = int(re.sub(r"\D", "", m.group(1)))
            break
    nums = []
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        m = re.search(r"/hotel-page-(\d+)", a["href"])
        if m:
            nums.append(int(m.group(1)))
    if nums:
        page_count = max(nums)
    return result_count, page_count


def is_detail(href: str) -> bool:
    path = urlparse(urljoin(BASE, href)).path
    if "/hotel-page-" in path:
        return False
    return any(p in path for p in DETAIL_PATTERNS)


def split_anchor(anchor) -> tuple[str, str]:
    name = clean(anchor.get_text(" ", strip=True))
    city = ""
    for key in ("data-city", "data-location", "data-ort"):
        if anchor.has_attr(key) and clean(anchor.get(key)):
            city = clean(anchor.get(key))
            break
    if not city:
        parent = anchor
        for _ in range(4):
            parent = parent.parent if parent else None
            if not parent:
                break
            txt = clean(parent.get_text(" | ", strip=True))
            if not name or len(txt) > 450:
                continue
            parts = [clean(p) for p in txt.split("|") if clean(p)]
            for p in parts:
                if p == name or len(p) > 80 or "http" in p.lower():
                    continue
                if re.search(r"\b\d{4}\b", p):
                    candidate = clean(re.sub(r".*?\b\d{4}\b", "", p))
                    if candidate:
                        city = candidate
                        break
            if city:
                break
    return name, city


def extract_page(html: str, page: int, observed_at: str) -> list[Record]:
    soup = BeautifulSoup(html, "html.parser")
    by_url: dict[str, Record] = {}
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not is_detail(href):
            continue
        url = urljoin(BASE, href).split("#", 1)[0]
        name, city = split_anchor(a)
        if not name or len(name) < 2:
            slug = urlparse(url).path.rsplit("/", 1)[-1]
            slug = re.sub(r"^hotel-", "", slug)
            name = clean(slug.replace("-", " ").title())
        rec = Record(
            discovery_id=discovery_id(name, city, url),
            canonical_name_candidate=name,
            city_candidate=city,
            detail_url=url,
            directory_page=page,
            source_tier="T1_OFFICIAL_DIRECTORY_LISTING",
            membership_state="UNKNOWN_PENDING_DETAIL",
            entity_resolution_state="PENDING_CANONICAL_ANTIJOIN",
            country_scope=scope(city),
            accommodation_type_hint=type_hint(name),
            classification_basis="NAME_HEURISTIC",
            observed_at=observed_at,
        )
        by_url[url] = rec
    return list(by_url.values())


def engine_states() -> dict[str, str]:
    states = {e: "PENDING_ENTITY_RESOLUTION" for e in ENGINES}
    states.update({
        "discovery_engine": "DISCOVERED_T1_LISTING",
        "entity_resolution_engine": "PENDING_CANONICAL_ANTIJOIN",
        "evidence_engine": "T1_LISTING_ONLY",
        "opportunity_engine": "PENDING_DEPENDENCIES",
        "scoring_engine": "PENDING_DEPENDENCIES",
        "personalization_engine": "PENDING_DEPENDENCIES",
        "message_engine": "PENDING_DEPENDENCIES",
        "qa_engine": "PENDING_DEPENDENCIES",
        "graph_engine": "PENDING_ENTITY_RESOLUTION",
        "ttl_engine": "LISTING_OBSERVATION_TIMESTAMPED",
        "export_engine": "DISCOVERY_EXPORT_READY",
        "governance_engine": "OUTBOUND_CLOSED",
    })
    return states


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_outputs(out: Path, records: list[Record], manifest: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rows = [asdict(r) for r in records]
    csv_path = out / "hotelleriesuisse_universe_discovery.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    json_path = out / "hotelleriesuisse_universe_discovery.json"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    matrix_path = out / "engine_matrix.csv"
    states = engine_states()
    with matrix_path.open("w", newline="", encoding="utf-8") as f:
        fields = ["discovery_id", "canonical_name_candidate", "city_candidate"] + ENGINES
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in records:
            w.writerow({"discovery_id": r.discovery_id, "canonical_name_candidate": r.canonical_name_candidate, "city_candidate": r.city_candidate, **states})
    manifest["files"] = {}
    for p in (csv_path, json_path, matrix_path):
        manifest["files"][p.name] = {"sha256": sha256(p), "bytes": p.stat().st_size}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="artifacts/full_market")
    ap.add_argument("--delay", type=float, default=0.75)
    ap.add_argument("--allow-partial", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    observed_at = datetime.now(timezone.utc).isoformat()
    session = requests.Session()
    robots_ok(session)

    first = get(session, DIRECTORY)
    result_count, page_count = observed_counts(first)
    if not page_count:
        page_count = 374

    all_records: dict[str, Record] = {}
    page_errors: list[dict] = []
    page_cardinality: dict[str, int] = {}
    for page in range(1, page_count + 1):
        try:
            html = first if page == 1 else get(session, PAGE.format(page=page))
            recs = extract_page(html, page, observed_at)
            page_cardinality[str(page)] = len(recs)
            if len(recs) < 5 or len(recs) > 30:
                page_errors.append({"page": page, "kind": "SUSPICIOUS_CARDINALITY", "count": len(recs)})
            for r in recs:
                all_records.setdefault(r.discovery_id, r)
        except Exception as exc:
            page_errors.append({"page": page, "kind": "FETCH_OR_PARSE_ERROR", "error": str(exc)})
        if page != page_count:
            time.sleep(max(args.delay, 0.2))

    records = sorted(all_records.values(), key=lambda r: (r.directory_page, norm(r.canonical_name_candidate), r.discovery_id))
    collisions = Counter((norm(r.canonical_name_candidate), norm(r.city_candidate)) for r in records)
    name_city_collisions = sum(1 for _, count in collisions.items() if count > 1)
    coverage = (len(records) / result_count) if result_count else None
    hard_errors = []
    if len(records) < 2000:
        hard_errors.append(f"only {len(records)} unique entities extracted; minimum is 2000")
    if result_count and coverage is not None and coverage < 0.90:
        hard_errors.append(f"coverage {coverage:.4f} is below 0.90 of observed result count {result_count}")
    if page_errors and not args.allow_partial:
        hard_errors.append(f"{len(page_errors)} page QA/fetch anomalies present")

    manifest = {
        "schema": "SWISS_OS_FULL_MARKET_DISCOVERY_V1",
        "generated_at": observed_at,
        "source": DIRECTORY,
        "robots_checked": True,
        "observed_result_count": result_count,
        "observed_page_count": page_count,
        "unique_discovery_entities": len(records),
        "coverage_ratio": coverage,
        "page_errors": page_errors,
        "page_cardinality": page_cardinality,
        "name_city_collision_keys": name_city_collisions,
        "type_hint_counts": dict(Counter(r.accommodation_type_hint for r in records)),
        "country_scope_counts": dict(Counter(r.country_scope for r in records)),
        "engine_contract": engine_states(),
        "hard_errors": hard_errors,
        "outbound": "CLOSED",
    }
    if records:
        write_outputs(out, records, manifest)
    else:
        out.mkdir(parents=True, exist_ok=True)
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps({"unique": len(records), "observed": result_count, "pages": page_count, "coverage": coverage, "errors": len(page_errors), "hard_errors": hard_errors}, indent=2))
    return 1 if hard_errors else 0

if __name__ == "__main__":
    sys.exit(main())
