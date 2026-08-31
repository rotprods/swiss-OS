from __future__ import annotations

from typing import Any, Mapping, Sequence

from .application_learning_v31 import (
    AAG_SCHEMA_VERSION,
    build_vacancy_first_seed,
    recruiter_10_second_gate,
)

SCHEMA_VERSION = "APPLICATION-PRIVATE-PACKET-3.1"


def _strategy_v31(seed: Mapping[str, Any]) -> dict[str, Any]:
    role = str(seed.get("target_role") or (seed.get("strategy") or {}).get("target_role") or "").strip()
    if not role:
        raise ValueError("exact target role missing")
    hotel = {
        "name": seed.get("hotel_name") or (seed.get("strategy") or {}).get("hotel_name") or "hotel",
        "city": seed.get("city") or "Switzerland",
    }
    careers = list(seed.get("careers_routes") or [])
    return build_vacancy_first_seed(
        hotel,
        [{"title": role, "source_url": seed.get("vacancy_source_url")}],
        careers[0] if careers else None,
    )


def compile_private_packet(
    seed: Mapping[str, Any],
    *,
    candidate_truth: Mapping[str, Any],
    role_relevant_evidence: Sequence[Mapping[str, Any]],
    approved_asset_refs: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile a private NO-SEND packet under AAG-3.1.

    The public shortlist never proves employer/property ownership by itself. The AAG-3.1
    receipt must contain terminal PASS for employer_scope_verified, semantic/temporal
    vacancy validity, mandatory-requirement extraction and application-route verification.
    """
    if seed.get("outbound") != "CLOSED" or seed.get("send_allowed") != 0:
        raise ValueError("public seed violates outbound lock")
    if seed.get("application_ready_no_send") not in {False, 0, None}:
        raise ValueError("public seed pre-authorized application readiness")
    if seed.get("owner_scope_verification_required_before_aag_ready") is not True:
        raise ValueError("V3.1 owner-scope recheck contract missing")

    strategy = _strategy_v31(seed)
    enriched_truth = dict(candidate_truth)
    enriched_truth["role_relevant_evidence"] = list(role_relevant_evidence)
    enriched_truth["links"] = approved_asset_refs.get("links") or []
    enriched_truth["links_verified"] = bool(approved_asset_refs.get("links_verified"))
    enriched_truth["headshot_url"] = approved_asset_refs.get("headshot_url")
    enriched_truth["headshot_approved"] = bool(approved_asset_refs.get("headshot_approved"))

    gate = recruiter_10_second_gate(strategy, enriched_truth)
    return {
        "schema_version": SCHEMA_VERSION,
        "application_adversarial_gate_required": AAG_SCHEMA_VERSION,
        "record_id": seed.get("record_id"),
        "hotel_name": seed.get("hotel_name"),
        "city": seed.get("city"),
        "target_role": strategy.get("target_role"),
        "lane": strategy.get("lane"),
        "vacancy_source_url": seed.get("vacancy_source_url"),
        "vacancy_signal_quality": seed.get("signal_quality"),
        "owner_scope_state": seed.get("owner_scope_state"),
        "role_relevant_evidence": list(role_relevant_evidence),
        "asset_refs": dict(approved_asset_refs),
        "candidate_truth_ref": candidate_truth.get("private_truth_ref"),
        "recruiter_gate": gate,
        "application_ready_no_send": bool(gate["pass"]),
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }
