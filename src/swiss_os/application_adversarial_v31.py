from __future__ import annotations

from typing import Any, Mapping

from .application_adversarial import (
    AuditState,
    Decision,
    HARD_GATE_EXPECTED as BASE_HARD_GATE_EXPECTED,
    evaluate_application as evaluate_application_v30,
)

SCHEMA_VERSION = "APPLICATION-ADVERSARIAL-GATE-3.1"
CALIBRATION_STATE = "HEURISTIC_UNCALIBRATED_UNTIL_OUTCOME_SAMPLE"

# These gates exist because a high-scoring candidate cannot compensate for uncertainty
# about whether the object being applied to is a real, current vacancy owned by the
# named employer/property and reached through the correct application surface.
VACANCY_PROVENANCE_HARD_GATES: dict[str, bool] = {
    "vacancy_semantic_validity_verified": True,
    "vacancy_temporal_validity_verified": True,
    "employer_scope_verified": True,
    "mandatory_requirements_extracted": True,
    "application_route_verified": True,
}

HARD_GATE_EXPECTED: dict[str, bool] = {
    **BASE_HARD_GATE_EXPECTED,
    **VACANCY_PROVENANCE_HARD_GATES,
}


def evaluate_v31_hard_gates(states: Mapping[str, bool | None]) -> dict[str, Any]:
    failures: list[str] = []
    unknown: list[str] = []
    observed: dict[str, bool | None] = {}
    for gate, expected in HARD_GATE_EXPECTED.items():
        value = states.get(gate)
        observed[gate] = value
        if value is None:
            unknown.append(gate)
        elif not isinstance(value, bool):
            raise ValueError(f"hard gate {gate} must be boolean/null")
        elif value != expected:
            failures.append(gate)
    return {
        "pass": not failures and not unknown,
        "failures": failures,
        "unknown": unknown,
        "observed": observed,
        "expected": dict(HARD_GATE_EXPECTED),
    }


def _base_states(states: Mapping[str, bool | None]) -> dict[str, bool | None]:
    return {gate: states.get(gate) for gate in BASE_HARD_GATE_EXPECTED}


def evaluate_application(
    *,
    dimension_scores: Mapping[str, Any],
    hard_gate_states: Mapping[str, bool | None],
    risk_scores: Mapping[str, Any],
    evidence_confidence_score: Any,
    human_resonance_score: Any,
    desperation_score: Any,
    questionnaire_answers: Mapping[str, str | AuditState],
    stakeholder_votes: Mapping[str, bool | None],
) -> dict[str, Any]:
    """Evaluate AAG-3.1 while preserving all AAG-3.0 scoring semantics.

    AAG-3.0 remains the scoring/questionnaire foundation. V3.1 adds five
    non-compensable provenance gates. Failure of any new gate is terminal REJECT;
    an unknown new gate forces LIMBO unless the base decision was already weaker.
    """
    receipt = dict(
        evaluate_application_v30(
            dimension_scores=dimension_scores,
            hard_gate_states=_base_states(hard_gate_states),
            risk_scores=risk_scores,
            evidence_confidence_score=evidence_confidence_score,
            human_resonance_score=human_resonance_score,
            desperation_score=desperation_score,
            questionnaire_answers=questionnaire_answers,
            stakeholder_votes=stakeholder_votes,
        )
    )
    hard = evaluate_v31_hard_gates(hard_gate_states)
    blockers = set(str(item) for item in receipt.get("blockers") or [])
    blockers.update(f"HARD_FAIL:{item}" for item in hard["failures"])
    blockers.update(f"HARD_UNKNOWN:{item}" for item in hard["unknown"])

    base_decision = Decision(str(receipt["decision"]))
    if hard["failures"]:
        decision = Decision.REJECT
    elif hard["unknown"]:
        # Preserve an already weak/reject result. Only a base READY/ELITE/high-quality
        # LIMBO is demoted to LIMBO by missing vacancy provenance.
        decision = (
            base_decision
            if base_decision in {Decision.REJECT, Decision.WEAK, Decision.PROMISING}
            else Decision.LIMBO
        )
    else:
        decision = base_decision

    receipt.update(
        {
            "schema_version": SCHEMA_VERSION,
            "calibration_state": CALIBRATION_STATE,
            "decision": decision.value,
            "hard_gates": hard,
            "vacancy_provenance_hard_gates": dict(VACANCY_PROVENANCE_HARD_GATES),
            "blockers": sorted(blockers),
            "application_ready_no_send": decision
            in {Decision.APPLICATION_READY_NO_SEND, Decision.ELITE_MATCH},
            "elite_match": decision == Decision.ELITE_MATCH,
            "final_send_ready": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        }
    )
    return receipt
