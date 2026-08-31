from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from .application_learning import build_vacancy_first_seed
from .application_wave import EVIDENCE_PRIORITY, _validate_market_aggregate, vacancy_priority, role_accessibility_score
from .vacancy_signal_quality import evaluate_signal, vacancy_identity_key

SCHEMA_VERSION = "APPLICATION-WAVE-3.1"


def _validate_vacancy_detail(vacancy_detail: Mapping[str, Any]) -> None:
    if vacancy_detail.get("authority_advanced") is not False:
        raise ValueError("vacancy-detail authority lock violated")
    if vacancy_detail.get("outbound") != "CLOSED" or vacancy_detail.get("send_allowed") != 0:
        raise ValueError("vacancy-detail outbound lock violated")


def _candidate_priority(candidate: Mapping[str, Any]) -> int:
    return (
        int(candidate["base_market_priority"])
        + EVIDENCE_PRIORITY.get(str(candidate["vacancy_evidence_type"]), 100)
        + role_accessibility_score(str(candidate["target_role"]))
        + (30 if candidate.get("housing_signal") else 0)
    )


def compile_top_resolved_vacancy_seeds_v31(
    market_aggregate: Mapping[str, Any],
    vacancy_detail: Mapping[str, Any],
    *,
    limit: int = 25,
) -> dict[str, Any]:
    """Compile a conservative vacancy shortlist before private Candidate Truth/AAG evaluation.

    This compiler rejects navigation labels, temporally contradictory/expired structured
    postings and cross-property duplicate vacancy identities. A duplicate vacancy URL+title
    observed under multiple source hotels is preserved in an ownership-review queue instead
    of being multiplied into several property applications.
    """
    _validate_market_aggregate(market_aggregate)
    _validate_vacancy_detail(vacancy_detail)
    market_by_id = {str(record.get("record_id")): record for record in market_aggregate["records"]}

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    rejected_signals: list[dict[str, Any]] = []

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
            route_observed_at = route.get("observed_at") or detail_record.get("observed_at") or vacancy_detail.get("observed_at")
            structured_qualities = [
                evaluate_signal(signal, route, route_observed_at)
                for signal in route.get("role_signals") or []
                if str(signal.get("evidence_type") or "") == "CURRENT_STRUCTURED_JOBPOSTING"
            ]
            route_temporal_conflict = any(not quality["temporal"]["current"] for quality in structured_qualities)

            for signal in route.get("role_signals") or []:
                quality = evaluate_signal(signal, route, route_observed_at)
                title = str(signal.get("title") or "").strip()
                source_url = str(signal.get("source_url") or route.get("final_url") or route.get("requested_url") or "").strip()
                evidence_type = str(signal.get("evidence_type") or "")
                reasons = list(quality["reasons"])
                eligible = bool(quality["signal_eligible_before_owner_scope"])
                if route_temporal_conflict and evidence_type != "CURRENT_STRUCTURED_JOBPOSTING":
                    eligible = False
                    reasons.append("ROUTE_STRUCTURED_TEMPORAL_CONFLICT_REQUIRES_RECHECK")

                base = {
                    "record_id": record_id,
                    "hotel_name": market_record.get("name"),
                    "city": market_record.get("city"),
                    "target_role": title,
                    "vacancy_source_url": source_url,
                    "vacancy_evidence_type": evidence_type,
                    "market_observed_at": market_record.get("observed_at"),
                    "vacancy_observed_at": route_observed_at,
                    "signal_quality": quality,
                    "signal_quality_reasons": reasons,
                }
                if not eligible:
                    rejected_signals.append(base)
                    continue

                grouped[vacancy_identity_key(title, source_url)].append(
                    {
                        **base,
                        "base_market_priority": base_score,
                        "housing_signal": bool(route.get("housing_signal")),
                        "requirement_evidence": {
                            "language_signal_snippets": route.get("language_signal_snippets") or [],
                            "experience_signal_snippets": route.get("experience_signal_snippets") or [],
                            "start_signal_snippets": route.get("start_signal_snippets") or [],
                            "housing_signal": bool(route.get("housing_signal")),
                            "contact_emails": route.get("contact_emails") or [],
                            "requires_requirement_detail": bool(signal.get("requires_requirement_detail")),
                        },
                        "careers_url": careers[0] if careers else None,
                    }
                )

    ownership_review_queue: list[dict[str, Any]] = []
    primary: list[dict[str, Any]] = []

    for identity_key, rows in grouped.items():
        record_ids = sorted({str(row["record_id"]) for row in rows})
        if len(record_ids) > 1:
            ownership_review_queue.append(
                {
                    "vacancy_identity": {"source_url": identity_key[0], "normalized_title": identity_key[1]},
                    "state": "MULTI_PROPERTY_SHARED_VACANCY_OWNER_UNRESOLVED",
                    "record_ids": record_ids,
                    "hotels": sorted({str(row.get("hotel_name") or "") for row in rows}),
                    "target_roles": sorted({str(row.get("target_role") or "") for row in rows}),
                    "requires_owner_scope_verification": True,
                }
            )
            continue

        # Same property can expose the same role through several evidence modes. Keep the
        # strongest evidence deterministically rather than multiplying one vacancy.
        best = sorted(
            rows,
            key=lambda row: (
                -EVIDENCE_PRIORITY.get(str(row["vacancy_evidence_type"]), 100),
                str(row["target_role"]).casefold(),
                str(row["vacancy_source_url"]),
            ),
        )[0]
        strategy = build_vacancy_first_seed(
            {"name": best.get("hotel_name"), "city": best.get("city")},
            [{"title": best["target_role"], "source_url": best["vacancy_source_url"]}],
            best.get("careers_url"),
        )
        priority = _candidate_priority(best)
        primary.append(
            {
                "record_id": best["record_id"],
                "hotel_name": best["hotel_name"],
                "city": best["city"],
                "market_observed_at": best["market_observed_at"],
                "vacancy_observed_at": best["vacancy_observed_at"],
                "target_role": best["target_role"],
                "vacancy_source_url": best["vacancy_source_url"],
                "vacancy_evidence_type": best["vacancy_evidence_type"],
                "vacancy_priority": priority,
                "signal_quality": best["signal_quality"],
                "owner_scope_state": "UNIQUE_SOURCE_RECORD_CANDIDATE_REQUIRES_PRIVATE_RECHECK",
                "owner_scope_verification_required_before_aag_ready": True,
                "requirement_evidence": best["requirement_evidence"],
                "strategy": strategy,
                "candidate_private_truth_embedded": False,
                "requires_private_fit_validation": True,
                "application_adversarial_gate_required": "APPLICATION-ADVERSARIAL-GATE-3.0",
                "application_ready_no_send": False,
                "final_send_ready": False,
                "outbound": "CLOSED",
                "send_allowed": 0,
            }
        )

    primary.sort(
        key=lambda item: (
            -int(item["vacancy_priority"]),
            str(item["record_id"]),
            str(item["target_role"]).casefold(),
            str(item["vacancy_source_url"]),
        )
    )
    selected = primary[:limit]
    return {
        "schema_version": SCHEMA_VERSION,
        "project": "SWITZERLAND_JOB_OS",
        "source_snapshot_id": market_aggregate.get("source_snapshot_id"),
        "market_observed_at": market_aggregate.get("observed_at"),
        "vacancy_detail_payload_sha256": vacancy_detail.get("payload_sha256"),
        "requested_limit": limit,
        "raw_signal_identity_count": len(grouped),
        "signal_quality_rejected_count": len(rejected_signals),
        "ownership_review_count": len(ownership_review_queue),
        "primary_vacancy_candidate_count": len(primary),
        "selected_count": len(selected),
        "selected": selected,
        "ownership_review_queue": ownership_review_queue,
        "rejected_signal_reason_counts": _reason_counts(rejected_signals),
        "selection_policy": "SEMANTIC_VALID_AND_TEMPORALLY_CURRENT_AND_NONMULTIPLIED_OWNER_SCOPE_THEN_EVIDENCE_PRIORITY",
        "candidate_truth_join": "PRIVATE_REQUIRED_BEFORE_APPLICATION_READY",
        "application_adversarial_gate_required": "APPLICATION-ADVERSARIAL-GATE-3.0",
        "application_ready_no_send": 0,
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def _reason_counts(rejected_signals: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rejected_signals:
        for reason in row.get("signal_quality_reasons") or []:
            counts[str(reason)] = counts.get(str(reason), 0) + 1
    return dict(sorted(counts.items()))
