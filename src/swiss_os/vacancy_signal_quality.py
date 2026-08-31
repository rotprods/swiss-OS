from __future__ import annotations

import re
from datetime import datetime, time, timezone
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

SCHEMA_VERSION = "VACANCY-SIGNAL-QUALITY-3.1"

JOB_URL_RE = re.compile(
    r"/(?:jobs?|careers?|career|karriere|stellen(?:angebote)?|offene-stellen|vacanc(?:y|ies)|"
    r"emploi|emplois|offres?-d?-?emploi|recrutement)(?:/|\?|$)|_j_\d+",
    re.I,
)
GENERIC_ROLE_RE = re.compile(
    r"^(?:opening crew position(?:en|s)?|open positions?|offene stellen|stellenangebote|"
    r"jobs?|careers?|career opportunities|join (?:our )?team|bewerben|apply now)$",
    re.I,
)
NAVIGATION_TITLE_RE = re.compile(
    r"^(?:restaurants?(?:\s*&\s*bars?)?|bars?|weitere restaurants?\s*&\s*bars?|"
    r"signature restaurant|florhof bar\s*&\s*brasserie|tisch reservieren|reservation|"
    r"barrierefrei(?:heit)?|accessibility|menu|menus|rooms?|zimmer|spa|wellness|events?|"
    r"unsere küche|unsere kueche|about us|über uns|ueber uns|benefits?|was wir bieten)$",
    re.I,
)

SEMANTIC_ALLOWED = {
    "CURRENT_STRUCTURED_JOBPOSTING",
    "CURRENT_PAGE_HEADING",
    "CURRENT_PAGE_TITLE",
    "CURRENT_PAGE_ROLE_LINK",
    "CURRENT_ROLE_LIKE_ROUTE",
}


def _parse_dt(value: Any, *, date_only_end_of_day: bool = False) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            day = datetime.strptime(text, "%Y-%m-%d").date()
            dt = datetime.combine(day, time.max if date_only_end_of_day else time.min)
        else:
            dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def canonical_url(url: str) -> str:
    parts = urlsplit(str(url or "").strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host if not port or (scheme == "https" and port == 443) else f"{host}:{port}"
    path = re.sub(r"/+", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def normalized_title(title: str) -> str:
    return re.sub(r"\s+", " ", str(title or "").strip()).casefold()


def vacancy_identity_key(title: str, source_url: str) -> tuple[str, str]:
    return canonical_url(source_url), normalized_title(title)


def temporal_quality(signal: Mapping[str, Any], observed_at: Any) -> dict[str, Any]:
    observed = _parse_dt(observed_at) or datetime.now(timezone.utc)
    posted = _parse_dt(signal.get("date_posted"))
    valid_through = _parse_dt(signal.get("valid_through"), date_only_end_of_day=True)
    reasons: list[str] = []

    if posted and valid_through and posted > valid_through:
        reasons.append("DATE_POSTED_AFTER_VALID_THROUGH")
    if posted and posted.date() > observed.date():
        reasons.append("DATE_POSTED_IN_FUTURE_AT_OBSERVATION")
    if valid_through and valid_through < observed:
        reasons.append("VALID_THROUGH_EXPIRED_AT_OBSERVATION")

    if reasons:
        state = "TEMPORAL_CONFLICT_OR_EXPIRED"
        current = False
    elif posted or valid_through:
        state = "TEMPORAL_CURRENT"
        current = True
    else:
        state = "TEMPORAL_UNBOUNDED_CURRENT_PAGE_SIGNAL"
        current = True

    return {
        "state": state,
        "current": current,
        "date_posted": signal.get("date_posted"),
        "valid_through": signal.get("valid_through"),
        "observed_at": str(observed_at or ""),
        "reasons": reasons,
    }


def semantic_quality(signal: Mapping[str, Any], route: Mapping[str, Any]) -> dict[str, Any]:
    title = re.sub(r"\s+", " ", str(signal.get("title") or "").strip())
    source_url = str(signal.get("source_url") or route.get("final_url") or route.get("requested_url") or "").strip()
    evidence_type = str(signal.get("evidence_type") or "").strip()
    reasons: list[str] = []

    if not title or not source_url:
        reasons.append("ROLE_TITLE_OR_SOURCE_URL_MISSING")
    if evidence_type not in SEMANTIC_ALLOWED:
        reasons.append("UNSUPPORTED_ROLE_EVIDENCE_TYPE")
    if GENERIC_ROLE_RE.match(title):
        reasons.append("GENERIC_VACANCY_BUCKET_NOT_EXACT_ROLE")
    if NAVIGATION_TITLE_RE.match(title):
        reasons.append("NAVIGATION_OR_VENUE_LABEL_NOT_ROLE")

    joblike_url = bool(JOB_URL_RE.search(source_url))
    if evidence_type in {"CURRENT_PAGE_ROLE_LINK", "CURRENT_ROLE_LIKE_ROUTE"} and not joblike_url:
        reasons.append("ROLE_LINK_URL_NOT_JOBLIKE")
    if evidence_type in {"CURRENT_PAGE_HEADING", "CURRENT_PAGE_TITLE"}:
        route_url = str(route.get("final_url") or route.get("requested_url") or source_url)
        if not JOB_URL_RE.search(route_url):
            reasons.append("ROLE_TEXT_NOT_ON_JOBLIKE_ROUTE")

    return {
        "state": "ROLE_SEMANTIC_VALID" if not reasons else "ROLE_SEMANTIC_REJECTED",
        "valid": not reasons,
        "title": title,
        "source_url": source_url,
        "joblike_url": joblike_url,
        "reasons": reasons,
    }


def evaluate_signal(signal: Mapping[str, Any], route: Mapping[str, Any], observed_at: Any) -> dict[str, Any]:
    semantic = semantic_quality(signal, route)
    temporal = temporal_quality(signal, observed_at)
    eligible = bool(semantic["valid"] and temporal["current"])
    reasons = list(semantic["reasons"]) + list(temporal["reasons"])
    return {
        "schema_version": SCHEMA_VERSION,
        "semantic": semantic,
        "temporal": temporal,
        "signal_eligible_before_owner_scope": eligible,
        "reasons": reasons,
    }
