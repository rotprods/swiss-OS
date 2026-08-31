from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .application_learning import build_vacancy_first_seed, recruiter_10_second_gate

SCHEMA_VERSION = "APPLICATION-WAVE-2.0"

ENTRY_SIGNAL_RE = re.compile(
    r"(?:helper|hilfe|mitarbeiter|mitarbeiterin|allrounder|crew|runner|steward|housekeep|zimmer|"
    r"roomboy|room attendant|reinigung|service|commis|kitchen|küche|kueche|spül|spuel|dish|"
    r"junior|trainee|praktik|entry|quereinsteiger|career changer|content|social media|marketing)",
    re.I,
)
SENIOR_SIGNAL_RE = re.compile(
    r"(?:director|direktor|head of|geschäftsführ|geschaeftsfuehr|general manager|executive|"
    r"chef de cuisine|küchenchef|kuechenchef|sous chef|leiter(?:in)?\b|leitung\b)",
    re.I,
)
EVIDENCE_PRIORITY = {
    "CURRENT_STRUCTURED_JOBPOSTING": 500,
    "CURRENT_PAGE_HEADING": 380,
    "CURRENT_PAGE_ROLE_LINK": 350,
    "CURRENT_PAGE_TITLE": 300,
    "CURRENT_ROLE_LIKE_ROUTE": 220,
}


def _validate_market_record(record: Mapping[str, Any]) -> None:
    safety = record.get("safety") or {}
    if safety.get("authority_advanced") is not False:
        raise ValueError("market record advanced authority")
    if safety.get("outbound") != "CLOSED" or safety.get("send_allowed") != 0:
        raise ValueError("market record violates outbound lock")
    if safety.get("canonical_id_allocations") != 0 or safety.get("canonical_id_reservations") != 0:
        raise ValueError("market record violates canonical-id lock")


def _validate_market_aggregate(aggregate: Mapping[str, Any]) -> None:
    records = aggregate.get("records")
    if not isinstance(records, list):
        raise ValueError("market aggregate records missing")
    aggregate_safety = aggregate.get("safety") or {}
    if aggregate_safety.get("authority_advanced") is not False:
        raise ValueError("market aggregate advanced authority")
    if aggregate_safety.get("outbound") != "CLOSED" or aggregate_safety.get("send_allowed") != 0:
        raise ValueError("market aggregate outbound lock violated")


def vacancy_priority(record: Mapping[str, Any]) -> int:
    """Rank current exact-vacancy evidence ahead of generic careers presence."""
    vacancy = record.get("e07_vacancy") or {}
    score = int((record.get("e15_score") or {}).get("market_readiness_score") or 0)
    jobs = vacancy.get("structured_openings") or []
    opening_routes = vacancy.get("opening_routes") or []
    careers = vacancy.get("careers_routes") or []
    housing_state = str((record.get("e08_housing") or {}).get("state") or "")
    if jobs:
        score += 1000
    elif opening_routes:
        score += 250
    elif careers:
        score += 50
    if housing_state == "STAFF_HOUSING_ROUTE_FOUND":
        score += 20
    if vacancy.get("explicit_no_openings_proof"):
        score -= 1000
    return score


def role_accessibility_score(title: str) -> int:
    """Generic first-screen accessibility only; private Candidate Truth remains authoritative."""
    score = 0
    if ENTRY_SIGNAL_RE.search(title):
        score += 120
    if SENIOR_SIGNAL_RE.search(title):
        score -= 250
    return score


def public_seed(record: Mapping[str, Any]) -> dict[str, Any]:
    _validate_market_record(record)
    vacancy = record.get("e07_vacancy") or {}
    jobs = vacancy.get("structured_openings") or []
    careers = vacancy.get("careers_routes") or []
    seed = build_vacancy_first_seed(record, jobs, careers[0] if careers else None)
    return {
        "record_id": record.get("record_id"),
        "hotel_name": record.get("name"),
        "city": record.get("city"),
        "observed_at": record.get("observed_at"),
        "vacancy_state": vacancy.get("state"),
        "market_priority": vacancy_priority(record),
        "source_openings": jobs,
        "opening_routes": vacancy.get("opening_routes") or [],
        "careers_routes": careers,
        "housing_state": (record.get("e08_housing") or {}).get("state"),
        "strategy": seed,
        "candidate_private_truth_embedded": False,
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def compile_top_exact_vacancy_seeds(
    aggregate: Mapping[str, Any], *, limit: int = 25
) -> dict[str, Any]:
    _validate_market_aggregate(aggregate)
    seeds = [public_seed(record) for record in aggregate["records"]]
    exact = [seed for seed in seeds if seed["strategy"]["application_mode"] == "PRIMARY_EXACT_VACANCY"]
    exact.sort(key=lambda seed: (-int(seed["market_priority"]), str(seed.get("record_id") or "")))
    selected = exact[:limit]
    return {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": aggregate.get("source_snapshot_id"),
        "market_observed_at": aggregate.get("observed_at"),
        "requested_limit": limit,
        "exact_vacancy_seed_count": len(exact),
        "selected_count": len(selected),
        "selected": selected,
        "selection_policy": "EXACT_CURRENT_STRUCTURED_VACANCY_FIRST_THEN_MARKET_PRIORITY",
        "candidate_truth_join": "PRIVATE_REQUIRED_BEFORE_APPLICATION_READY",
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def compile_top_resolved_vacancy_seeds(
    market_aggregate: Mapping[str, Any],
    vacancy_detail: Mapping[str, Any],
    *,
    limit: int = 25,
) -> dict[str, Any]:
    """Turn current vacancy-detail evidence into public-safe NO-SEND candidate seeds."""
    _validate_market_aggregate(market_aggregate)
    if vacancy_detail.get("authority_advanced") is not False:
        raise ValueError("vacancy-detail authority lock violated")
    if vacancy_detail.get("outbound") != "CLOSED" or vacancy_detail.get("send_allowed") != 0:
        raise ValueError("vacancy-detail outbound lock violated")
    market_by_id = {str(record.get("record_id")): record for record in market_aggregate["records"]}
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for detail_record in vacancy_detail.get("records") or []:
        record_id = str(detail_record.get("record_id") or "")
        market_record = market_by_id.get(record_id)
        if not market_record:
            raise ValueError(f"vacancy-detail record missing from market aggregate: {record_id}")
        if detail_record.get("outbound") != "CLOSED" or detail_record.get("send_allowed") != 0:
            raise ValueError("vacancy-detail record safety mismatch")
        careers = list((market_record.get("e07_vacancy") or {}).get("careers_routes") or [])
        base_score = vacancy_priority(market_record)
        for route in detail_record.get("routes") or []:
            if route.get("no_openings_explicit"):
                continue
            for signal in route.get("role_signals") or []:
                title = str(signal.get("title") or "").strip()
                source_url = str(signal.get("source_url") or route.get("final_url") or route.get("requested_url") or "")
                evidence_type = str(signal.get("evidence_type") or "")
                if not title or not source_url:
                    continue
                key = (record_id, title.casefold(), source_url)
                if key in seen:
                    continue
                seen.add(key)
                strategy = build_vacancy_first_seed(
                    market_record,
                    [{"title": title, "source_url": source_url}],
                    careers[0] if careers else None,
                )
                priority = base_score + EVIDENCE_PRIORITY.get(evidence_type, 100) + role_accessibility_score(title)
                if route.get("housing_signal"):
                    priority += 30
                candidates.append(
                    {
                        "record_id": record_id,
                        "hotel_name": market_record.get("name"),
                        "city": market_record.get("city"),
                        "market_observed_at": market_record.get("observed_at"),
                        "vacancy_observed_at": route.get("observed_at"),
                        "target_role": title,
                        "vacancy_source_url": source_url,
                        "vacancy_evidence_type": evidence_type,
                        "vacancy_priority": priority,
                        "requirement_evidence": {
                            "language_signal_snippets": route.get("language_signal_snippets") or [],
                            "experience_signal_snippets": route.get("experience_signal_snippets") or [],
                            "start_signal_snippets": route.get("start_signal_snippets") or [],
                            "housing_signal": bool(route.get("housing_signal")),
                            "contact_emails": route.get("contact_emails") or [],
                            "requires_requirement_detail": bool(signal.get("requires_requirement_detail")),
                        },
                        "strategy": strategy,
                        "candidate_private_truth_embedded": False,
                        "requires_private_fit_validation": True,
                        "application_ready_no_send": False,
                        "final_send_ready": False,
                        "outbound": "CLOSED",
                        "send_allowed": 0,
                    }
                )
    candidates.sort(
        key=lambda item: (
            -int(item["vacancy_priority"]),
            str(item["record_id"]),
            str(item["target_role"]).casefold(),
            str(item["vacancy_source_url"]),
        )
    )
    selected = candidates[:limit]
    return {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": market_aggregate.get("source_snapshot_id"),
        "market_observed_at": market_aggregate.get("observed_at"),
        "vacancy_detail_payload_sha256": vacancy_detail.get("payload_sha256"),
        "requested_limit": limit,
        "resolved_vacancy_signal_count": len(candidates),
        "selected_count": len(selected),
        "selected": selected,
        "selection_policy": "CURRENT_RESOLVED_ROLE_SIGNAL_THEN_EVIDENCE_QUALITY_THEN_GENERIC_ENTRY_ACCESSIBILITY",
        "candidate_truth_join": "PRIVATE_REQUIRED_BEFORE_APPLICATION_READY",
        "application_ready_no_send": 0,
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def compile_private_packet(
    seed: Mapping[str, Any],
    *,
    candidate_truth: Mapping[str, Any],
    role_relevant_evidence: Sequence[Mapping[str, Any]],
    approved_asset_refs: Mapping[str, Any],
) -> dict[str, Any]:
    """Join private candidate truth after public market selection; never sends anything."""
    strategy = seed.get("strategy") or {}
    enriched_truth = dict(candidate_truth)
    enriched_truth["role_relevant_evidence"] = list(role_relevant_evidence)
    enriched_truth["links"] = approved_asset_refs.get("links") or []
    enriched_truth["links_verified"] = bool(approved_asset_refs.get("links_verified"))
    enriched_truth["headshot_url"] = approved_asset_refs.get("headshot_url")
    enriched_truth["headshot_approved"] = bool(approved_asset_refs.get("headshot_approved"))
    gate = recruiter_10_second_gate(strategy, enriched_truth)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": seed.get("record_id"),
        "hotel_name": seed.get("hotel_name"),
        "city": seed.get("city"),
        "target_role": strategy.get("target_role"),
        "lane": strategy.get("lane"),
        "market_observed_at": seed.get("market_observed_at") or seed.get("observed_at"),
        "role_relevant_evidence": list(role_relevant_evidence),
        "asset_refs": dict(approved_asset_refs),
        "candidate_truth_ref": candidate_truth.get("private_truth_ref"),
        "recruiter_gate": gate,
        "application_ready_no_send": bool(gate["pass"]),
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"expected object: {path}")
    return value
