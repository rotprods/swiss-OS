#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE = "https://www.hotelleriesuisse.ch"
ROBOTS = BASE + "/robots.txt"
UA = "swiss-os-public-market-research/1.0 (+https://github.com/rotprods/swiss-OS)"

TRANSIENT = {408, 425, 429, 500, 502, 503, 504}
SOCIAL_HOSTS = {"facebook.com", "instagram.com", "linkedin.com", "youtube.com", "tiktok.com", "x.com", "twitter.com"}
SPECIALISATIONS = [
    "Design", "Green Living", "Sustainable Living", "Excellent Cuisine", "Seminars",
    "Wellness", "Business", "Biking", "Hiking", "Snowsports", "Congresses",
    "Adults only", "Family", "Accessible", "Golf", "Spa", "Unique",
]


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def host(url: str) -> str:
    try:
        h = (urlparse(url).hostname or "").casefold().removeprefix("www.")
        return h
    except Exception:
        return ""


def get(session: requests.Session, url: str, retries: int = 4) -> tuple[int, str]:
    last_status = 0
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=35, headers={"User-Agent": UA, "Accept-Language": "de-CH,de;q=0.9,en;q=0.7"})
            last_status = r.status_code
            if r.status_code == 200:
                return r.status_code, r.text
            if r.status_code not in TRANSIENT:
                return r.status_code, ""
        except requests.RequestException:
            pass
        time.sleep(min(2 ** attempt, 8))
    return last_status, ""


def robots_parser(session: requests.Session) -> RobotFileParser:
    status, text = get(session, ROBOTS)
    if status != 200 or not text:
        raise RuntimeError(f"cannot evaluate robots.txt; HTTP {status}")
    rp = RobotFileParser(); rp.set_url(ROBOTS); rp.parse(text.splitlines())
    return rp


def jsonld_objects(soup: BeautifulSoup):
    out = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text()
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        if isinstance(obj, list): out.extend(x for x in obj if isinstance(x, dict))
        elif isinstance(obj, dict):
            graph = obj.get("@graph")
            if isinstance(graph, list): out.extend(x for x in graph if isinstance(x, dict))
            out.append(obj)
    return out


def address_from_jsonld(objs) -> tuple[str, str, str]:
    for obj in objs:
        addr = obj.get("address")
        if isinstance(addr, dict):
            city = clean(addr.get("addressLocality"))
            region = clean(addr.get("addressRegion"))
            country = addr.get("addressCountry")
            if isinstance(country, dict): country = country.get("name") or country.get("@id")
            country = clean(str(country or ""))
            if city or region or country:
                return city, region, country
    return "", "", ""


def scope_from_country(country: str) -> str:
    c = country.casefold()
    if c in {"ch", "che", "switzerland", "schweiz", "suisse", "svizzera"} or "switzerland" in c or "schweiz" in c:
        return "SWITZERLAND_VERIFIED"
    if c in {"li", "lie", "liechtenstein"} or "liechtenstein" in c:
        return "LIECHTENSTEIN_VERIFIED"
    return "UNKNOWN_AFTER_DETAIL_PARSE"


def external_website(soup: BeautifulSoup) -> tuple[str, str]:
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        h = host(href)
        if not href.startswith(("http://", "https://")) or not h:
            continue
        if h.endswith("hotelleriesuisse.ch") or h in SOCIAL_HOSTS or any(h.endswith("." + s) for s in SOCIAL_HOSTS):
            continue
        text = clean(a.get_text(" ", strip=True)).casefold()
        score = 0
        if any(k in text for k in ("website", "webseite", "homepage", "site internet", "sito web")): score += 10
        if a.get("target") == "_blank": score += 1
        candidates.append((score, href))
    if not candidates:
        return "", ""
    candidates.sort(key=lambda x: (-x[0], x[1]))
    score, href = candidates[0]
    return href, "EXTERNAL_WEBSITE_LABEL" if score >= 10 else "EXTERNAL_LINK_CANDIDATE"


def membership_state(text: str) -> str:
    lower = text.casefold()
    for heading in ("mitgliedschaften", "adhésions", "adesioni"):
        idx = lower.find(heading)
        if idx >= 0:
            window = lower[idx: idx + 700]
            if "hotelleriesuisse" in window:
                return "MEMBER_CURRENT_VERIFIED"
    return "UNKNOWN_AFTER_DETAIL_PARSE"


def classification(text: str) -> tuple[str, str]:
    patterns = [
        r"\b([1-5])\s*(?:sterne|stars?|étoiles?|stelle)(?:\s+(superior))?\b",
        r"\b(swiss\s+lodge)\b",
        r"\b(hostel)\b",
        r"\b(serviced\s+apartments?)\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if not m: continue
        if m.lastindex and m.group(1).isdigit():
            return f"{m.group(1)} STAR" + (" SUPERIOR" if m.lastindex >= 2 and m.group(2) else ""), "DETAIL_TEXT_REGEX"
        return clean(m.group(1)).upper(), "DETAIL_TEXT_REGEX"
    return "", "UNKNOWN_AFTER_DETAIL_PARSE"


def rooms(text: str) -> tuple[str, str]:
    for pat in (r"\b(\d{1,4})\s+(?:zimmer|rooms?|chambres?|camere)\b", r"(?:zimmer|rooms?|chambres?|camere)\s*[:\-]?\s*(\d{1,4})\b"):
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1), "DETAIL_TEXT_REGEX"
    return "", "UNKNOWN_AFTER_DETAIL_PARSE"


def specialisations(text: str) -> str:
    found = []
    lower = text.casefold()
    for s in SPECIALISATIONS:
        if s.casefold() in lower:
            found.append(s)
    return "|".join(found)


def parse_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = clean(soup.get_text(" ", strip=True))
    objs = jsonld_objects(soup)
    city, region, country = address_from_jsonld(objs)
    website, website_basis = external_website(soup)
    cls, cls_basis = classification(text)
    room_count, rooms_basis = rooms(text)
    return {
        "detail_name": clean((soup.find("h1") or {}).get_text(" ", strip=True) if soup.find("h1") else ""),
        "detail_city": city,
        "detail_region": region,
        "detail_country": country,
        "country_scope": scope_from_country(country),
        "official_website_candidate": website,
        "website_basis": website_basis,
        "membership_state": membership_state(text),
        "classification": cls,
        "classification_basis": cls_basis,
        "rooms": room_count,
        "rooms_basis": rooms_basis,
        "specialisations": specialisations(text),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard-index", type=int, default=0)
    ap.add_argument("--shard-count", type=int, default=1)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if args.shard_count < 1 or not (0 <= args.shard_index < args.shard_count):
        raise SystemExit("invalid shard parameters")

    rows = list(csv.DictReader(Path(args.input).open(encoding="utf-8")))
    shard = [r for i, r in enumerate(rows) if i % args.shard_count == args.shard_index]
    if args.limit is not None: shard = shard[:args.limit]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    session = requests.Session(); rp = robots_parser(session)
    observed_at = datetime.now(timezone.utc).isoformat()
    results = []
    counts = Counter()

    for pos, row in enumerate(shard):
        url = row["detail_url"]
        result = {**row, "detail_observed_at": observed_at}
        if not rp.can_fetch(UA, url):
            result.update({"detail_fetch_state": "ROBOTS_BLOCKED", "http_status": "", "membership_state_detail": "UNKNOWN_NOT_FETCHED"})
            counts["ROBOTS_BLOCKED"] += 1; results.append(result); continue
        status, html = get(session, url)
        result["http_status"] = status
        if status != 200 or not html:
            result.update({"detail_fetch_state": f"HTTP_{status or 'ERROR'}", "membership_state_detail": "UNKNOWN_NOT_FETCHED"})
            counts[result["detail_fetch_state"]] += 1; results.append(result)
        else:
            parsed = parse_detail(html)
            result.update(parsed)
            result["membership_state_detail"] = parsed.pop("membership_state") if "membership_state" in parsed else "UNKNOWN_AFTER_DETAIL_PARSE"
            result["detail_fetch_state"] = "PARSED_T1_DETAIL"
            counts["PARSED_T1_DETAIL"] += 1; results.append(result)
        if pos + 1 < len(shard): time.sleep(max(args.delay, 0.5))

    fields = sorted({k for r in results for k in r.keys()})
    path = out / f"detail_enrichment_shard_{args.shard_index:02d}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(results)
    manifest = {
        "schema": "SWISS_OS_DETAIL_ENRICHMENT_V1",
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "input_rows": len(rows),
        "processed_rows": len(results),
        "fetch_state_counts": dict(counts),
        "classification_is_evidence_backed_only_when_basis_is_DETAIL_TEXT_REGEX": True,
        "membership_unknown_is_not_non_member": True,
        "outbound": "CLOSED"
    }
    (out / f"detail_enrichment_shard_{args.shard_index:02d}.manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
