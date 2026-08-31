from __future__ import annotations

from typing import Any, Mapping, Sequence

from .application_adversarial import Decision
from .application_adversarial_v31 import SCHEMA_VERSION as AAG_SCHEMA_VERSION
from .application_learning import (
    build_vacancy_first_seed as build_vacancy_first_seed_v30,
    classify_lane,
)

READY_DECISIONS = {Decision.APPLICATION_READY_NO_SEND.value, Decision.ELITE_MATCH.value}


def build_vacancy_first_seed(
    hotel: Mapping[str, Any], jobs: Sequence[Mapping[str, Any]], careers_url: str | None
) -> dict[str, Any]:
    seed = dict(build_vacancy_first_seed_v30(hotel, jobs, careers_url))
    seed["strategy_version"] = "VACANCY-FIRST-APPLICATION-3.1+AAG-3.1"
    seed["application_adversarial_gate"] = {
        "required": True,
        "schema_version": AAG_SCHEMA_VERSION,
        "ready_decisions": sorted(READY_DECISIONS),
        "hard_fail_compensation_allowed": False,
        "vacancy_semantic_validity_required": True,
        "vacancy_temporal_validity_required": True,
        "employer_scope_required": True,
        "mandatory_requirements_extracted_required": True,
        "application_route_verified_required": True,
        "final_send_ready": False,
    }
    return seed


def _score(receipt: Mapping[str, Any], key: str) -> int | None:
    raw = receipt.get(key)
    if raw is None or isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    value = int(round(float(raw)))
    return value if 0 <= value <= 100 else None


def validate_aag31_receipt(candidate_truth: Mapping[str, Any]) -> tuple[bool, str | None, str | None]:
    receipt = candidate_truth.get("application_adversarial_gate")
    if not isinstance(receipt, Mapping):
        return False, None, "AAG31_REQUIRED"
    decision = str(receipt.get("decision") or "") or None
    if receipt.get("schema_version") != AAG_SCHEMA_VERSION:
        return False, decision, "AAG31_SCHEMA_MISMATCH"
    if decision not in READY_DECISIONS:
        return False, decision, "AAG31_NOT_READY"
    if receipt.get("application_ready_no_send") is not True:
        return False, decision, "AAG31_READY_FLAG_MISMATCH"
    if receipt.get("final_send_ready") is not False:
        return False, decision, "AAG31_SEND_SAFETY_MISMATCH"
    if receipt.get("outbound") != "CLOSED" or receipt.get("send_allowed") != 0:
        return False, decision, "AAG31_OUTBOUND_SAFETY_MISMATCH"
    if receipt.get("blockers"):
        return False, decision, "AAG31_BLOCKERS_PRESENT"

    hard = receipt.get("hard_gates")
    if not isinstance(hard, Mapping):
        return False, decision, "AAG31_HARD_GATE_RECEIPT_MISSING"
    if hard.get("pass") is not True or hard.get("failures") or hard.get("unknown"):
        return False, decision, "AAG31_HARD_GATES_NOT_TERMINAL_PASS"

    provenance = receipt.get("vacancy_provenance_hard_gates")
    if not isinstance(provenance, Mapping) or not provenance:
        return False, decision, "AAG31_PROVENANCE_GATES_MISSING"
    observed = hard.get("observed")
    if not isinstance(observed, Mapping):
        return False, decision, "AAG31_HARD_GATE_OBSERVED_MISSING"
    missing_pass = [gate for gate, expected in provenance.items() if observed.get(gate) is not expected]
    if missing_pass:
        return False, decision, f"AAG31_PROVENANCE_NOT_VERIFIED:{missing_pass[0]}"

    scores = {
        "application_quality_score": _score(receipt, "application_quality_score"),
        "evidence_confidence_score": _score(receipt, "evidence_confidence_score"),
        "employer_risk_score": _score(receipt, "employer_risk_score"),
        "desperation_score": _score(receipt, "desperation_score"),
        "human_resonance_score": _score(receipt, "human_resonance_score"),
    }
    invalid = [key for key, value in scores.items() if value is None]
    if invalid:
        return False, decision, f"AAG31_SCORE_INVALID:{invalid[0]}"
    if scores["application_quality_score"] < 92:
        return False, decision, "AAG31_QUALITY_BELOW_READY"
    if scores["evidence_confidence_score"] < 95:
        return False, decision, "AAG31_EVIDENCE_BELOW_READY"
    if scores["employer_risk_score"] > 20:
        return False, decision, "AAG31_EMPLOYER_RISK_TOO_HIGH"
    if scores["desperation_score"] > 15:
        return False, decision, "AAG31_DESPERATION_TOO_HIGH"
    if scores["human_resonance_score"] < 85:
        return False, decision, "AAG31_RESONANCE_BELOW_READY"
    return True, decision, None


def recruiter_10_second_gate(
    seed: Mapping[str, Any], candidate_truth: Mapping[str, Any]
) -> dict[str, Any]:
    required_truth = list(seed.get("candidate_truth_required_fields") or [])
    missing = [field for field in required_truth if not candidate_truth.get(field)]
    exact_role = seed.get("target_role")
    failures: list[str] = []
    if seed.get("application_mode") != "PRIMARY_EXACT_VACANCY" or not exact_role:
        failures.append("EXACT_LIVE_VACANCY_REQUIRED")
    if missing:
        failures.append("CANDIDATE_TRUTH_INCOMPLETE")
    if candidate_truth.get("hard_requirement_failure"):
        failures.append("HARD_REQUIREMENT_FAILURE")
    if candidate_truth.get("founder_ceo_claim") and not candidate_truth.get("founder_ceo_evidence_verified"):
        failures.append("FOUNDER_CEO_CLAIM_UNVERIFIED")
    if candidate_truth.get("headshot_url") and not candidate_truth.get("headshot_approved"):
        failures.append("HEADSHOT_UNVERIFIED")
    if candidate_truth.get("links") and not candidate_truth.get("links_verified"):
        failures.append("LINKS_UNVERIFIED")
    aag_pass, aag_decision, aag_failure = validate_aag31_receipt(candidate_truth)
    if not aag_pass and aag_failure:
        failures.append(aag_failure)
    return {
        "pass": not failures,
        "failures": failures,
        "missing_candidate_truth": missing,
        "exact_role": exact_role,
        "lane": seed.get("lane") or classify_lane(str(exact_role or "")).value,
        "portfolio_default_attachment": bool((seed.get("asset_policy") or {}).get("portfolio_default_attachment")),
        "aag_schema_version": AAG_SCHEMA_VERSION,
        "aag_decision": aag_decision,
        "aag_pass": aag_pass,
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }
