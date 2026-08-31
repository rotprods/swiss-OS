from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .application_learning import build_vacancy_first_seed, recruiter_10_second_gate

SCHEMA_VERSION = "APPLICATION-WAVE-2.0"


def _validate_market_record(record: Mapping[str, Any]) -> None:
    safety = record.get("safety") or {}
    if safety.get("authority_advanced") is not False:
        raise ValueError("market record advanced authority")
    if safety.get("outbound") != "CLOSED" or safety.get("send_allowed") != 0:
        raise ValueError("market record violates outbound lock")
    if safety.get("canonical_id_allocations") != 0 or safety.get("canonical_id_reservations") != 0:
        raise ValueError("market record violates canonical-id lock")


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
    records = aggregate.get("records")
    if not isinstance(records, list):
        raise ValueError("market aggregate records missing")
    aggregate_safety = aggregate.get("safety") or {}
    if aggregate_safety.get("authority_advanced") is not False:
        raise ValueError("market aggregate advanced authority")
    if aggregate_safety.get("outbound") != "CLOSED" or aggregate_safety.get("send_allowed") != 0:
        raise ValueError("market aggregate outbound lock violated")
    seeds = [public_seed(record) for record in records]
    exact = [seed for seed in seeds if seed["strategy"]["application_mode"] == "PRIMARY_EXACT_VACANCY"]
    exact.sort(key=lambda seed: (-int(seed["market_priority"]), str(seed.get("record_id") or "")))
    selected = exact[:limit]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": aggregate.get("source_snapshot_id"),
        "market_observed_at": aggregate.get("observed_at"),
        "requested_limit": limit,
        "exact_vacancy_seed_count": len(exact),
        "selected_count": len(selected),
        "selected": selected,
        "selection_policy": "EXACT_CURRENT_VACANCY_FIRST_THEN_MARKET_PRIORITY",
        "candidate_truth_join": "PRIVATE_REQUIRED_BEFORE_APPLICATION_READY",
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
    return payload


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
        "market_observed_at": seed.get("observed_at"),
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
