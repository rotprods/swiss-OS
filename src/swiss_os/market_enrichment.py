from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import ipaddress
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "MARKET-ENRICHMENT-2061-1.0"
SOURCE_SNAPSHOT_ID = "HS-MEMBER-DE-33206402141"
USER_AGENT = "SWITZERLAND_JOB_OS-market-enrichment/1.0 (+read-only-research)"
MAX_BYTES = 1_500_000
TIMEOUT = 6

WEBSITE_RE = re.compile(r"(?:website|webseite|homepage|site web|sito web|internet|zur website|visit website)", re.I)
SPONTANEOUS_RE = re.compile(r"(?:spontaneous application|unsolicited application|initiativbewerbung|spontanbewerbung|candidature spontan(?:e|ée)|candidatura spontanea)", re.I)

CAREER_RE = re.compile(
    r"(?:career|careers|job|jobs|karriere|stellen|stellenangebote|emploi|emplois|carriere|carrière|"
    r"offres?-d.?emploi|lavora|lavoro|posizioni|work-with-us|join-us|join-our-team)", re.I
)
TEAM_RE = re.compile(r"(?:team|about-us|ueber-uns|über-uns|management|direction|equipe|équipe|chi-siamo)", re.I)
HOUSING_RE = re.compile(
    r"(?:staff[-_/ ]?(?:housing|accommodation)|employee[-_/ ]?housing|mitarbeiter[-_/ ]?(?:unterkunft|wohnung)|"
    r"personal[-_/ ]?unterkunft|logement[-_/ ]?(?:du[-_/ ]?)?personnel|alloggio[-_/ ]?personale)", re.I
)
NO_OPENINGS_RE = re.compile(
    r"(?:no (?:current )?(?:open positions|vacancies|jobs)|currently no (?:open positions|vacancies|jobs)|"
    r"keine (?:offenen )?stellen|derzeit keine stellen|aucune offre|pas de poste|nessuna posizione)", re.I
)
EXTERNAL_DENY_HOST_FRAGMENTS = (
    "facebook.", "instagram.", "linkedin.", "youtube.", "youtu.be", "tiktok.", "tripadvisor.",
    "booking.", "expedia.", "google.", "maps.", "hotelleriesuisse.ch", "hotelleriesuisse.com",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def host_is_public(hostname: str) -> bool:
    host = hostname.rstrip(".").lower()
    if not host or host == "localhost" or host.endswith(".local"):
        return False
    try:
        ips = {ipaddress.ip_address(host.strip("[]"))}
    except ValueError:
        try:
            ips = {ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
        except (socket.gaierror, ValueError):
            return False
    return bool(ips) and all(ip.is_global for ip in ips)


def validate_public_https_url(url: str) -> urllib.parse.SplitResult:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme.lower() != "https" or not parts.hostname:
        raise ValueError("only public HTTPS URLs are allowed")
    if parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError("URL credentials/non-standard ports are forbidden")
    if not host_is_public(parts.hostname):
        raise ValueError("hostname must resolve only to public addresses")
    return parts


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_https_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass(frozen=True)
class FetchResult:
    requested_url: str
    final_url: str | None
    state: str
    http_status: int | None
    body_sha256: str | None
    body_text: str | None
    error_type: str | None


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.title_parts: list[str] = []
        self._in_title = False
        self._anchor_href: str | None = None
        self._anchor_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "title":
            self._in_title = True
        elif tag.lower() == "a":
            self._anchor_href = attrs_dict.get("href") or None
            self._anchor_parts = [attrs_dict.get("aria-label", ""), attrs_dict.get("title", "")]

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        elif tag.lower() == "a" and self._anchor_href:
            self.links.append({"href": self._anchor_href, "text": " ".join(self._anchor_parts).strip()})
            self._anchor_href = None
            self._anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._anchor_href is not None:
            self._anchor_parts.append(data)

    @property
    def title(self) -> str | None:
        value = re.sub(r"\s+", " ", " ".join(self.title_parts)).strip()
        return value[:300] or None


def parse_links(text: str) -> LinkParser:
    parser = LinkParser()
    parser.feed(text)
    return parser


def same_site(host_a: str | None, host_b: str | None) -> bool:
    if not host_a or not host_b:
        return False
    a = host_a.lower().removeprefix("www.")
    b = host_b.lower().removeprefix("www.")
    return a == b or a.endswith("." + b) or b.endswith("." + a)


def external_official_candidates(detail_url: str, html_text: str) -> list[str]:
    parser = parse_links(html_text)
    detail_host = urllib.parse.urlsplit(detail_url).hostname
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()
    for link in parser.links:
        href = urllib.parse.urljoin(detail_url, link["href"].strip())
        parts = urllib.parse.urlsplit(href)
        if parts.scheme != "https" or not parts.hostname or same_site(parts.hostname, detail_host):
            continue
        host = parts.hostname.lower()
        if any(fragment in host for fragment in EXTERNAL_DENY_HOST_FRAGMENTS):
            continue
        clean = urllib.parse.urlunsplit(("https", parts.netloc, parts.path or "/", parts.query, ""))
        if clean in seen:
            continue
        seen.add(clean)
        label = f"{link['text']} {href}".lower()
        score = 100 if WEBSITE_RE.search(label) else 0
        if score and parts.path in ("", "/"):
            score += 10
        if score:
            scored.append((score, clean))
    return [url for _, url in sorted(scored, key=lambda item: (-item[0], item[1]))[:5]]


def route_candidates(base_url: str, html_text: str, pattern: re.Pattern[str], limit: int = 5) -> list[str]:
    parser = parse_links(html_text)
    base_host = urllib.parse.urlsplit(base_url).hostname
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()
    for link in parser.links:
        href = urllib.parse.urljoin(base_url, link["href"].strip())
        parts = urllib.parse.urlsplit(href)
        if parts.scheme != "https" or not parts.hostname or not same_site(parts.hostname, base_host):
            continue
        signal = f"{link['text']} {parts.path}"
        if not pattern.search(signal):
            continue
        clean = urllib.parse.urlunsplit(("https", parts.netloc, parts.path or "/", parts.query, ""))
        if clean in seen:
            continue
        seen.add(clean)
        score = 100 if pattern.search(link["text"]) else 50
        scored.append((score, clean))
    return [url for _, url in sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]]


def _jobposting_nodes(value: Any) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        types = value.get("@type")
        if isinstance(types, str):
            types = [types]
        if isinstance(types, list) and any(str(t).lower() == "jobposting" for t in types):
            found.append(value)
        for child in value.values():
            found.extend(_jobposting_nodes(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_jobposting_nodes(child))
    return found


JSONLD_RE = re.compile(r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.I | re.S)


def extract_jobpostings(html_text: str, source_url: str) -> list[dict[str, Any]]:
    postings: list[dict[str, Any]] = []
    for match in JSONLD_RE.finditer(html_text):
        raw = html.unescape(match.group(1)).strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in _jobposting_nodes(payload):
            posting = {
                "title": str(node.get("title") or "").strip()[:300] or None,
                "date_posted": str(node.get("datePosted") or "").strip()[:64] or None,
                "valid_through": str(node.get("validThrough") or "").strip()[:64] or None,
                "employment_type": node.get("employmentType"),
                "source_url": source_url,
            }
            postings.append(posting)
    unique: dict[tuple[str | None, str], dict[str, Any]] = {}
    for posting in postings:
        unique[(posting["title"], posting["source_url"])] = posting
    return list(unique.values())[:25]


class HttpResearchClient:
    def __init__(self, *, timeout: int = TIMEOUT, max_bytes: int = MAX_BYTES) -> None:
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.opener = urllib.request.build_opener(SafeRedirect())
        self.robots_cache: dict[str, tuple[urllib.robotparser.RobotFileParser | None, str]] = {}

    def _robots_allowed(self, url: str) -> tuple[bool, str]:
        parts = validate_public_https_url(url)
        host = parts.hostname or ""
        cached = self.robots_cache.get(host)
        if cached is not None:
            parser, state = cached
            if state.endswith("_BLOCK"):
                return (False, state)
            return ((True if parser is None else parser.can_fetch(USER_AGENT, url)), state)
        robots_url = f"https://{parts.netloc}/robots.txt"
        try:
            request = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT}, method="GET")
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read(300_000).decode("utf-8", errors="replace")
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.parse(body.splitlines())
            self.robots_cache[host] = (rp, "ROBOTS_PARSED")
            return (rp.can_fetch(USER_AGENT, url), "ROBOTS_PARSED")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self.robots_cache[host] = (None, "ROBOTS_404_NO_POLICY")
                return (True, "ROBOTS_404_NO_POLICY")
            state = f"ROBOTS_HTTP_{exc.code}_BLOCK"
            self.robots_cache[host] = (None, state)
            return (False, state)
        except Exception as exc:
            state = f"ROBOTS_{type(exc).__name__}_BLOCK"
            self.robots_cache[host] = (None, state)
            return (False, state)

    def fetch(self, url: str, *, respect_robots: bool = True) -> FetchResult:
        try:
            validate_public_https_url(url)
            if respect_robots:
                allowed, robots_state = self._robots_allowed(url)
                if not allowed:
                    return FetchResult(url, None, f"ROBOTS_BLOCKED:{robots_state}", None, None, None, None)
            request = urllib.request.Request(
                url,
                method="GET",
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"},
            )
            with self.opener.open(request, timeout=self.timeout) as response:
                final_url = response.geturl()
                validate_public_https_url(final_url)
                body = response.read(self.max_bytes + 1)
                if len(body) > self.max_bytes:
                    return FetchResult(url, final_url, "RESPONSE_TOO_LARGE", getattr(response, "status", None), None, None, None)
                content_type = response.headers.get("Content-Type", "")
                if "html" not in content_type.lower() and "text" not in content_type.lower():
                    return FetchResult(url, final_url, "NON_HTML", getattr(response, "status", None), hashlib.sha256(body).hexdigest(), None, None)
                text = body.decode("utf-8", errors="replace")
                return FetchResult(url, final_url, "FETCHED", getattr(response, "status", None), hashlib.sha256(body).hexdigest(), text, None)
        except urllib.error.HTTPError as exc:
            return FetchResult(url, None, f"HTTP_{exc.code}", exc.code, None, None, "HTTPError")
        except Exception as exc:
            return FetchResult(url, None, "FETCH_FAILED", None, None, None, type(exc).__name__)


def load_manifest(path: Path, expected_records: int | None = None) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records")
    if not isinstance(records, list):
        raise ValueError("manifest records missing")
    if expected_records is not None and len(records) != expected_records:
        raise ValueError(f"manifest count mismatch: {len(records)} != {expected_records}")
    keys = [record.get("record_id") for record in records]
    if not all(isinstance(key, str) and key for key in keys) or len(keys) != len(set(keys)):
        raise ValueError("manifest record_id set is invalid")
    if data.get("authority_advanced") is not False or data.get("send_allowed") != 0:
        raise ValueError("source manifest violates fail-closed contract")
    return data


def shard(records: Sequence[Mapping[str, Any]], index: int, count: int) -> list[Mapping[str, Any]]:
    if count < 1 or index < 0 or index >= count:
        raise ValueError("invalid shard")
    n = len(records)
    start = (n * index) // count
    end = (n * (index + 1)) // count
    return list(records[start:end])


def explicit_no_openings(text: str) -> bool:
    return bool(NO_OPENINGS_RE.search(re.sub(r"\s+", " ", text)))


def _proposal_seed(record: Mapping[str, Any], jobs: Sequence[Mapping[str, Any]], careers_url: str | None) -> dict[str, Any]:
    name = str(record.get("name") or "el hotel")
    city = str(record.get("city") or "Suiza")
    if jobs:
        titles = ", ".join(str(j.get("title") or "posición").strip() for j in jobs[:3])
        hook = f"He revisado las vacantes actuales de {name} en {city}, incluida(s) {titles}."
    elif careers_url:
        hook = f"He revisado la vía oficial de carreras de {name} en {city}; mi candidatura se adaptaría a las necesidades actuales del equipo."
    else:
        hook = f"He revisado la presencia actual de {name} en {city} y prepararía una candidatura espontánea específica para la propiedad."
    return {
        "hotel_specific_hook": hook,
        "subject_seed": f"Candidatura para {name} — {city}",
        "candidate_truth_block_required": True,
        "candidate_truth_required_fields": ["target_role", "experience", "languages", "availability", "mobility", "contact_identity"],
        "final_send_ready": False,
        "draft_template": f"Equipo de {name}: {hook} [CANDIDATE_TRUTH_BLOCK_REQUIRED]",
    }


def enrich_record(record: Mapping[str, Any], client: HttpResearchClient, observed_at: str) -> dict[str, Any]:
    detail_url = str(record.get("detail_url") or "")
    base = {
        "record_id": record.get("record_id"),
        "name": record.get("name"),
        "city": record.get("city"),
        "source_detail_url": detail_url,
        "observed_at": observed_at,
    }
    detail = client.fetch(detail_url, respect_robots=True)
    official_candidates = external_official_candidates(detail.final_url or detail_url, detail.body_text or "") if detail.body_text else []
    official_url = official_candidates[0] if official_candidates else None
    official = client.fetch(official_url, respect_robots=True) if official_url else None
    official_html = official.body_text if official and official.body_text else ""
    careers = route_candidates(official.final_url or official_url or "https://example.invalid/", official_html, CAREER_RE, limit=4) if official_html else []
    team_routes = route_candidates(official.final_url or official_url or "https://example.invalid/", official_html, TEAM_RE, limit=3) if official_html else []
    housing_routes = route_candidates(official.final_url or official_url or "https://example.invalid/", official_html, HOUSING_RE, limit=3) if official_html else []

    postings: list[dict[str, Any]] = []
    career_evidence: list[dict[str, Any]] = []
    opening_routes: list[str] = []
    no_openings_proof = False
    spontaneous_application = False
    for url in careers[:3]:
        fetched = client.fetch(url, respect_robots=True)
        career_evidence.append({
            "url": url,
            "state": fetched.state,
            "http_status": fetched.http_status,
            "body_sha256": fetched.body_sha256,
        })
        if fetched.body_text:
            postings.extend(extract_jobpostings(fetched.body_text, fetched.final_url or url))
            no_openings_proof = no_openings_proof or explicit_no_openings(fetched.body_text)
            spontaneous_application = spontaneous_application or bool(SPONTANEOUS_RE.search(fetched.body_text))
            for candidate in route_candidates(fetched.final_url or url, fetched.body_text, CAREER_RE, limit=12):
                if candidate != url and candidate not in careers and candidate not in opening_routes:
                    opening_routes.append(candidate)
    unique_jobs: dict[tuple[Any, str], dict[str, Any]] = {}
    for job in postings:
        unique_jobs[(job.get("title"), job.get("source_url") or "")] = job
    jobs = list(unique_jobs.values())[:25]

    if jobs:
        vacancy_state = "CURRENT_STRUCTURED_OPENINGS_FOUND_T1"
    elif opening_routes:
        vacancy_state = "CURRENT_OPENING_ROUTES_FOUND_T1"
    elif careers and no_openings_proof:
        vacancy_state = "CURRENT_NO_OPENINGS_EXPLICIT_T1"
    elif careers:
        vacancy_state = "CAREERS_ROUTE_FOUND_OPENINGS_UNKNOWN_T1"
    elif official_url:
        vacancy_state = "CAREERS_ROUTE_NOT_DISCOVERED"
    else:
        vacancy_state = "OFFICIAL_SITE_NOT_DISCOVERED"

    score = 0
    score += 15 if official_url else 0
    score += 25 if careers else 0
    score += 45 if jobs else (30 if opening_routes else 0)
    score += 5 if team_routes else 0
    score += 5 if housing_routes else 0
    score -= 10 if vacancy_state == "CURRENT_NO_OPENINGS_EXPLICIT_T1" else 0
    score = max(0, min(100, score))

    proposal = _proposal_seed(record, jobs, careers[0] if careers else None)
    result = {
        **base,
        "source_detail_fetch": {
            "state": detail.state,
            "final_url": detail.final_url,
            "http_status": detail.http_status,
            "body_sha256": detail.body_sha256,
        },
        "official_site": {
            "url": official_url,
            "candidate_urls": official_candidates,
            "state": official.state if official else "NOT_DISCOVERED",
            "body_sha256": official.body_sha256 if official else None,
        },
        "e07_vacancy": {
            "state": vacancy_state,
            "careers_routes": careers,
            "career_evidence": career_evidence,
            "structured_openings": jobs,
            "structured_openings_count": len(jobs),
            "opening_routes": opening_routes[:25],
            "opening_routes_count": len(opening_routes[:25]),
            "explicit_no_openings_proof": no_openings_proof,
        },
        "e08_housing": {
            "state": "STAFF_HOUSING_ROUTE_FOUND" if housing_routes else "STAFF_HOUSING_RESEARCH_PENDING",
            "routes": housing_routes,
        },
        "e09_people": {
            "state": "TEAM_ROUTE_FOUND" if team_routes else "PEOPLE_RESEARCH_PENDING",
            "routes": team_routes,
            "personal_contacts_persisted": False,
        },
        "e10_channel": {
            "state": "DIRECT_CAREERS_ROUTE" if careers else ("OFFICIAL_SITE_ONLY" if official_url else "CHANNEL_RESEARCH_PENDING"),
            "primary_route": careers[0] if careers else official_url,
            "spontaneous_application_policy": "ACCEPTED_T1" if spontaneous_application else "NOT_OBSERVED",
        },
        "e11_intelligence": {
            "freshness_observed_at": observed_at,
            "vacancy_ttl_days": 7,
            "identity_ttl_days": 30,
            "evidence_scope": "PUBLIC_WEB_READ_ONLY",
        },
        "e12_graph": {
            "subject_node": f"SOURCE:{record.get('record_id')}",
            "edges": [
                {"type": "HAS_SOURCE_DETAIL", "target": detail_url},
                *([{"type": "HAS_OFFICIAL_SITE", "target": official_url}] if official_url else []),
                *([{"type": "HAS_CAREERS_ROUTE", "target": url} for url in careers]),
            ],
            "authority_effect": "NONE",
        },
        "e14_scheduler": {
            "vacancy_recheck_days": 7,
            "identity_recheck_days": 30,
            "priority": "P0" if jobs or opening_routes else ("P1" if careers else "P2"),
        },
        "e15_score": {
            "market_readiness_score": score,
            "explain": {
                "official_site": bool(official_url),
                "careers_route": bool(careers),
                "structured_openings": len(jobs),
                "opening_routes": len(opening_routes),
                "team_route": bool(team_routes),
                "housing_route": bool(housing_routes),
            },
        },
        "e16_candidate_truth": {
            "state": "PRIVATE_CANDIDATE_TRUTH_JOIN_REQUIRED",
            "pii_persisted": False,
        },
        "e17_application": proposal,
        "e18_qa": {
            "terminal_claims_from_similarity": False,
            "general_contact_promoted_to_recruitment": False,
            "explicit_no_openings_required_for_negative_claim": True,
        },
        "e19_observability": {
            "source_fetch_ok": detail.state == "FETCHED",
            "official_site_found": bool(official_url),
            "careers_route_found": bool(careers),
            "opening_evidence_found": bool(jobs or opening_routes),
        },
        "e20_recovery": {
            "source_snapshot_id": SOURCE_SNAPSHOT_ID,
            "source_record_id": record.get("record_id"),
        },
        "e21_delivery": {
            "execution_surface": "GITHUB_ACTIONS",
            "artifact_only": True,
        },
        "e22_security": {
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
        "safety": {
            "authority_advanced": False,
            "canonical_id_allocations": 0,
            "canonical_id_reservations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
    }
    result["record_sha256"] = sha256_value({k: v for k, v in result.items() if k != "record_sha256"})
    return result


def run_shard(manifest: Mapping[str, Any], shard_index: int, shard_count: int, observed_at: str, sleep_seconds: float = 0.8) -> dict[str, Any]:
    records = shard(manifest["records"], shard_index, shard_count)
    client = HttpResearchClient()
    out: list[dict[str, Any]] = []
    for i, record in enumerate(records):
        out.append(enrich_record(record, client, observed_at))
        if sleep_seconds and i + 1 < len(records):
            time.sleep(sleep_seconds)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": manifest.get("snapshot_id") or SOURCE_SNAPSHOT_ID,
        "source_records_sha256": manifest.get("records_sha256"),
        "observed_at": observed_at,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "records": out,
        "records_sha256": sha256_value(out),
        "safety": {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0, "irreversible_external_actions": 0},
    }
    payload["packet_sha256"] = sha256_value({k: v for k, v in payload.items() if k != "packet_sha256"})
    return payload


def aggregate(manifest: Mapping[str, Any], shard_payloads: Sequence[Mapping[str, Any]], observed_at: str) -> tuple[dict[str, Any], dict[str, Any]]:
    expected_ids = [r["record_id"] for r in manifest["records"]]
    by_id: dict[str, Mapping[str, Any]] = {}
    for packet in shard_payloads:
        if packet.get("source_records_sha256") != manifest.get("records_sha256"):
            raise ValueError("shard source lineage mismatch")
        for record in packet.get("records", []):
            rid = record.get("record_id")
            if rid in by_id:
                raise ValueError(f"duplicate record in shards: {rid}")
            by_id[rid] = record
    if set(by_id) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(by_id))[:10]
        extra = sorted(set(by_id) - set(expected_ids))[:10]
        raise ValueError(f"aggregate coverage mismatch missing={missing} extra={extra}")
    records = [by_id[rid] for rid in expected_ids]
    vacancy = Counter(r["e07_vacancy"]["state"] for r in records)
    housing = Counter(r["e08_housing"]["state"] for r in records)
    people = Counter(r["e09_people"]["state"] for r in records)
    channels = Counter(r["e10_channel"]["state"] for r in records)
    openings = sum(r["e07_vacancy"]["structured_openings_count"] for r in records)
    aggregate_payload = {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": manifest.get("snapshot_id") or SOURCE_SNAPSHOT_ID,
        "source_records": len(records),
        "source_records_sha256": manifest.get("records_sha256"),
        "observed_at": observed_at,
        "records": records,
        "records_sha256": sha256_value(records),
        "safety": {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0, "irreversible_external_actions": 0},
    }
    aggregate_payload["aggregate_sha256"] = sha256_value({k: v for k, v in aggregate_payload.items() if k != "aggregate_sha256"})
    summary = {
        "schema_version": "MARKET-ENRICHMENT-SUMMARY-1.0",
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": aggregate_payload["source_snapshot_id"],
        "source_records": len(records),
        "source_records_sha256": manifest.get("records_sha256"),
        "observed_at": observed_at,
        "aggregate_sha256": aggregate_payload["aggregate_sha256"],
        "vacancy_states": dict(sorted(vacancy.items())),
        "structured_openings_total": openings,
        "hotels_with_structured_openings": sum(1 for r in records if r["e07_vacancy"]["structured_openings_count"]),
        "hotels_with_opening_routes": sum(1 for r in records if r["e07_vacancy"].get("opening_routes")),
        "hotels_with_careers_route": sum(1 for r in records if r["e07_vacancy"]["careers_routes"]),
        "hotels_accepting_spontaneous_applications": sum(1 for r in records if r["e10_channel"].get("spontaneous_application_policy") == "ACCEPTED_T1"),
        "hotels_with_official_site": sum(1 for r in records if r["official_site"]["url"]),
        "housing_states": dict(sorted(housing.items())),
        "people_states": dict(sorted(people.items())),
        "channel_states": dict(sorted(channels.items())),
        "personalized_application_seeds": len(records),
        "candidate_truth_blocks_required": sum(1 for r in records if r["e17_application"]["candidate_truth_block_required"]),
        "authority_advanced": False,
        "canonical_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }
    summary["summary_sha256"] = sha256_value({k: v for k, v in summary.items() if k != "summary_sha256"})
    return aggregate_payload, summary


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-shard")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--expected-records", type=int, default=2061)
    run.add_argument("--shard-index", type=int, required=True)
    run.add_argument("--shard-count", type=int, required=True)
    run.add_argument("--observed-at", required=True)
    run.add_argument("--sleep-seconds", type=float, default=0.8)
    run.add_argument("--out", type=Path, required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--manifest", type=Path, required=True)
    agg.add_argument("--expected-records", type=int, default=2061)
    agg.add_argument("--input-dir", type=Path, required=True)
    agg.add_argument("--observed-at", required=True)
    agg.add_argument("--out", type=Path, required=True)
    agg.add_argument("--summary", type=Path, required=True)

    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest, args.expected_records)
    if args.cmd == "run-shard":
        payload = run_shard(manifest, args.shard_index, args.shard_count, args.observed_at, args.sleep_seconds)
        _write(args.out, payload)
        print(json.dumps({"records": len(payload["records"]), "packet_sha256": payload["packet_sha256"]}, sort_keys=True))
        return 0

    packets = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(args.input_dir.glob("market-enrichment-shard-*.json"))]
    if not packets:
        raise ValueError("no shard packets found")
    aggregate_payload, summary = aggregate(manifest, packets, args.observed_at)
    _write(args.out, aggregate_payload)
    _write(args.summary, summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
