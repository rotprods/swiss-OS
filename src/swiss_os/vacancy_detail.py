from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.parse
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping, Sequence

from .market_enrichment import (
    HttpResearchClient,
    NO_OPENINGS_RE,
    HOUSING_RE,
    canonical_json,
    extract_jobpostings,
    same_site,
    validate_public_https_url,
)

SCHEMA_VERSION = "VACANCY-DETAIL-RESOLUTION-1.0"
MAX_ROUTES_PER_HOTEL = 8
MAX_SIGNALS_PER_ROUTE = 25

GENERIC_ROUTE_RE = re.compile(
    r"^(?:jobs?|careers?|karriere|stellen(?:angebote)?|offene stellen|emploi|emplois|carriere|carrière|"
    r"work with us|join us|join our team|alle stellenangebote|ausbildung|information|benefits?|destination)$",
    re.I,
)

ROLE_SIGNAL_RE = re.compile(
    r"(?:"
    r"housekeep|zimmerm(?:ä|ae)dchen|roomboy|room attendant|reinigung|cleaner|"
    r"service|chef de rang|commis de rang|food runner|restaurant|frühstück|breakfast|bar(?:keeper|tender)?|"
    r"küche|kueche|kitchen|koch|köchin|cook|chef|steward|spül|spuel|dishwasher|"
    r"reception|reserv|front office|guest|concierge|empfang|"
    r"marketing|social media|content|communication|e-?commerce|photo|video|design|creative|"
    r"wellness|spa|massage|therap|house technician|haustechnik|maintenance|technik|"
    r"night audit|portier|bell|driver|chauffeur|logistik|logistics|"
    r"manager|leitung|leiter|supervisor|assistant|praktik|intern|trainee|lehrstelle|apprentice"
    r")",
    re.I,
)

LANGUAGE_SIGNAL_RE = re.compile(
    r".{0,90}(?:Deutsch|German|Englisch|English|Französisch|French|Italienisch|Italian|"
    r"Sprachkenntnisse|language skills|languages?).{0,140}",
    re.I | re.S,
)
EXPERIENCE_SIGNAL_RE = re.compile(
    r".{0,90}(?:Berufserfahrung|Erfahrung|experience|Ausbildung|Lehre|apprenticeship|"
    r"qualification|Qualifikation|Quereinsteiger|career changer).{0,160}",
    re.I | re.S,
)
START_SIGNAL_RE = re.compile(
    r".{0,80}(?:ab sofort|per sofort|sofort|immediately|start date|Eintritt|ab [0-9]{1,2}[.]?\s*"
    r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)|"
    r"Winter(?:saison)?\s*20[0-9]{2}|Sommer(?:saison)?\s*20[0-9]{2}).{0,120}",
    re.I | re.S,
)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _clean_text(value: str, limit: int = 500) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()[:limit]


class VacancyTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.headings: list[str] = []
        self.links: list[dict[str, str]] = []
        self.text_parts: list[str] = []
        self._title = False
        self._heading: str | None = None
        self._heading_parts: list[str] = []
        self._href: str | None = None
        self._anchor_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): (value or "") for key, value in attrs}
        if tag == "title":
            self._title = True
        if tag in {"h1", "h2", "h3"}:
            self._heading = tag
            self._heading_parts = []
        if tag == "a":
            self._href = attrs_dict.get("href") or None
            self._anchor_parts = [attrs_dict.get("aria-label", ""), attrs_dict.get("title", "")]

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._title = False
        if tag == self._heading:
            text = _clean_text(" ".join(self._heading_parts), 300)
            if text:
                self.headings.append(text)
            self._heading = None
            self._heading_parts = []
        if tag == "a" and self._href:
            text = _clean_text(" ".join(self._anchor_parts), 300)
            self.links.append({"href": self._href, "text": text})
            self._href = None
            self._anchor_parts = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self.text_parts.append(text)
        if self._title:
            self.title_parts.append(text)
        if self._heading:
            self._heading_parts.append(text)
        if self._href is not None:
            self._anchor_parts.append(text)

    @property
    def title(self) -> str | None:
        text = _clean_text(" ".join(self.title_parts), 300)
        return text or None

    @property
    def visible_text(self) -> str:
        return _clean_text(" ".join(self.text_parts), 100_000)


def _specific_role_text(value: str | None) -> str | None:
    text = _clean_text(value or "", 300)
    if not text or GENERIC_ROUTE_RE.fullmatch(text):
        return None
    if not ROLE_SIGNAL_RE.search(text):
        return None
    return text


def _route_role_hint(url: str) -> str | None:
    parts = urllib.parse.urlsplit(url)
    decoded = urllib.parse.unquote(parts.path).replace("-", " ").replace("_", " ").replace("/", " ")
    decoded = _clean_text(decoded, 300)
    if not decoded or GENERIC_ROUTE_RE.fullmatch(decoded):
        return None
    return decoded if ROLE_SIGNAL_RE.search(decoded) else None


def _snippets(pattern: re.Pattern[str], text: str, limit: int = 5) -> list[str]:
    found: list[str] = []
    for match in pattern.finditer(text):
        value = _clean_text(match.group(0), 300)
        if value and value not in found:
            found.append(value)
        if len(found) >= limit:
            break
    return found


def _same_site_child_roles(base_url: str, parser: VacancyTextParser) -> list[dict[str, Any]]:
    host = urllib.parse.urlsplit(base_url).hostname
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for link in parser.links:
        role = _specific_role_text(link.get("text"))
        if not role:
            continue
        href = urllib.parse.urljoin(base_url, link.get("href") or "")
        parts = urllib.parse.urlsplit(href)
        if parts.scheme != "https" or not parts.hostname or not same_site(parts.hostname, host):
            continue
        clean = urllib.parse.urlunsplit(("https", parts.netloc, parts.path or "/", parts.query, ""))
        key = (role.casefold(), clean)
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "title": role,
                "source_url": clean,
                "evidence_type": "CURRENT_PAGE_ROLE_LINK",
                "requires_requirement_detail": True,
            }
        )
        if len(results) >= MAX_SIGNALS_PER_ROUTE:
            break
    return results


def resolve_route(client: HttpResearchClient, route_url: str, observed_at: str) -> dict[str, Any]:
    validate_public_https_url(route_url)
    result = client.fetch(route_url)
    output: dict[str, Any] = {
        "requested_url": route_url,
        "final_url": result.final_url,
        "fetch_state": result.state,
        "http_status": result.http_status,
        "body_sha256": result.body_sha256,
        "observed_at": observed_at,
        "role_signals": [],
        "language_signal_snippets": [],
        "experience_signal_snippets": [],
        "start_signal_snippets": [],
        "housing_signal": False,
        "contact_emails": [],
        "no_openings_explicit": False,
        "authority_effect": "NONE",
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    if not result.body_text or result.state != "FETCHED":
        output["resolution_state"] = "ROUTE_FETCH_FAILED_OR_BLOCKED"
        return output

    parser = VacancyTextParser()
    parser.feed(result.body_text)
    visible = parser.visible_text
    structured = extract_jobpostings(result.body_text, result.final_url or route_url)
    signals: list[dict[str, Any]] = []
    for posting in structured:
        if posting.get("title"):
            signals.append({**posting, "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING", "requires_requirement_detail": False})

    for heading in parser.headings:
        role = _specific_role_text(heading)
        if role:
            signals.append(
                {
                    "title": role,
                    "source_url": result.final_url or route_url,
                    "evidence_type": "CURRENT_PAGE_HEADING",
                    "requires_requirement_detail": True,
                }
            )

    title_role = _specific_role_text(parser.title)
    if title_role:
        signals.append(
            {
                "title": title_role,
                "source_url": result.final_url or route_url,
                "evidence_type": "CURRENT_PAGE_TITLE",
                "requires_requirement_detail": True,
            }
        )

    route_hint = _route_role_hint(result.final_url or route_url)
    if route_hint:
        signals.append(
            {
                "title": route_hint,
                "source_url": result.final_url or route_url,
                "evidence_type": "CURRENT_ROLE_LIKE_ROUTE",
                "requires_requirement_detail": True,
            }
        )

    signals.extend(_same_site_child_roles(result.final_url or route_url, parser))
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for signal in signals:
        key = (str(signal.get("title") or "").casefold(), str(signal.get("source_url") or ""))
        if key[0] and key not in unique:
            unique[key] = signal
    output["role_signals"] = list(unique.values())[:MAX_SIGNALS_PER_ROUTE]
    output["language_signal_snippets"] = _snippets(LANGUAGE_SIGNAL_RE, visible)
    output["experience_signal_snippets"] = _snippets(EXPERIENCE_SIGNAL_RE, visible)
    output["start_signal_snippets"] = _snippets(START_SIGNAL_RE, visible)
    output["housing_signal"] = bool(HOUSING_RE.search(visible))
    output["contact_emails"] = sorted(set(EMAIL_RE.findall(visible)))[:10]
    output["no_openings_explicit"] = bool(NO_OPENINGS_RE.search(visible))
    if output["role_signals"]:
        output["resolution_state"] = "CURRENT_ROLE_SIGNALS_FOUND"
    elif output["no_openings_explicit"]:
        output["resolution_state"] = "CURRENT_NO_OPENINGS_EXPLICIT"
    else:
        output["resolution_state"] = "CURRENT_ROUTE_FETCHED_ROLE_UNRESOLVED"
    return output


def opening_route_workset(aggregate: Mapping[str, Any]) -> list[dict[str, Any]]:
    if aggregate.get("source_records") != 2061:
        raise ValueError("expected exact 2061-record market aggregate")
    safety = aggregate.get("safety") or {}
    if safety.get("authority_advanced") is not False or safety.get("outbound") != "CLOSED" or safety.get("send_allowed") != 0:
        raise ValueError("market aggregate safety lock mismatch")
    selected: list[dict[str, Any]] = []
    for record in aggregate.get("records") or []:
        routes = list((record.get("e07_vacancy") or {}).get("opening_routes") or [])[:MAX_ROUTES_PER_HOTEL]
        if not routes:
            continue
        selected.append(
            {
                "record_id": record.get("record_id"),
                "name": record.get("name"),
                "city": record.get("city"),
                "opening_routes": routes,
            }
        )
    selected.sort(key=lambda item: str(item.get("record_id") or ""))
    return selected


def compile_shard(
    aggregate: Mapping[str, Any], *, shard_index: int, shard_count: int, observed_at: str,
    client: HttpResearchClient | None = None,
) -> dict[str, Any]:
    workset = opening_route_workset(aggregate)
    if not (0 <= shard_index < shard_count):
        raise ValueError("invalid shard index")
    assigned = [item for index, item in enumerate(workset) if index % shard_count == shard_index]
    client = client or HttpResearchClient()
    records: list[dict[str, Any]] = []
    for item in assigned:
        route_results = [resolve_route(client, route, observed_at) for route in item["opening_routes"]]
        signals = [signal for result in route_results for signal in result.get("role_signals") or []]
        records.append(
            {
                **item,
                "routes": route_results,
                "role_signal_count": len(signals),
                "current_role_signal_titles": sorted({str(signal.get("title")) for signal in signals if signal.get("title")})[:50],
                "no_openings_explicit": bool(route_results) and all(bool(result.get("no_openings_explicit")) for result in route_results),
                "authority_effect": "NONE",
                "outbound": "CLOSED",
                "send_allowed": 0,
            }
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_market_aggregate_sha256": sha256_value(aggregate),
        "source_snapshot_id": aggregate.get("source_snapshot_id"),
        "workset_total": len(workset),
        "workset_sha256": sha256_value(workset),
        "shard_index": shard_index,
        "shard_count": shard_count,
        "observed_at": observed_at,
        "records": records,
        "record_ids_sha256": sha256_value([record["record_id"] for record in records]),
        "authority_advanced": False,
        "canonical_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }
    return payload


def aggregate_shards(aggregate: Mapping[str, Any], shards: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    workset = opening_route_workset(aggregate)
    expected_ids = [item["record_id"] for item in workset]
    records: list[Mapping[str, Any]] = []
    shard_indexes: set[int] = set()
    for shard in shards:
        if shard.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unexpected vacancy-detail shard schema")
        if shard.get("authority_advanced") is not False or shard.get("outbound") != "CLOSED" or shard.get("send_allowed") != 0:
            raise ValueError("vacancy-detail shard safety mismatch")
        shard_indexes.add(int(shard["shard_index"]))
        records.extend(shard.get("records") or [])
    records = sorted(records, key=lambda item: str(item.get("record_id") or ""))
    ids = [record.get("record_id") for record in records]
    if ids != expected_ids or len(ids) != len(set(ids)):
        raise ValueError("vacancy-detail coverage mismatch")
    states: dict[str, int] = {}
    role_signal_hotels = 0
    role_signal_total = 0
    for record in records:
        if record.get("role_signal_count", 0):
            role_signal_hotels += 1
            role_signal_total += int(record.get("role_signal_count", 0))
        for route in record.get("routes") or []:
            state = str(route.get("resolution_state") or "UNKNOWN")
            states[state] = states.get(state, 0) + 1
    result = {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": aggregate.get("source_snapshot_id"),
        "source_market_aggregate_sha256": sha256_value(aggregate),
        "workset_total": len(workset),
        "workset_sha256": sha256_value(workset),
        "records": records,
        "resolved_record_ids_sha256": sha256_value(ids),
        "role_signal_hotels": role_signal_hotels,
        "role_signal_total": role_signal_total,
        "route_resolution_states": dict(sorted(states.items())),
        "shards_observed": sorted(shard_indexes),
        "authority_advanced": False,
        "canonical_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }
    result["payload_sha256"] = sha256_value({key: value for key, value in result.items() if key != "payload_sha256"})
    return result


def _load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    shard = sub.add_parser("run-shard")
    shard.add_argument("--aggregate", type=Path, required=True)
    shard.add_argument("--shard-index", type=int, required=True)
    shard.add_argument("--shard-count", type=int, required=True)
    shard.add_argument("--observed-at", required=True)
    shard.add_argument("--out", type=Path, required=True)
    agg = sub.add_parser("aggregate")
    agg.add_argument("--market-aggregate", type=Path, required=True)
    agg.add_argument("--input-dir", type=Path, required=True)
    agg.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    market = _load(args.aggregate if args.command == "run-shard" else args.market_aggregate)
    if args.command == "run-shard":
        payload = compile_shard(market, shard_index=args.shard_index, shard_count=args.shard_count, observed_at=args.observed_at)
    else:
        shards = [_load(path) for path in sorted(args.input_dir.glob("vacancy-detail-shard-*.json"))]
        payload = aggregate_shards(market, shards)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(payload.get("records") or []), "outbound": payload["outbound"], "send_allowed": payload["send_allowed"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
