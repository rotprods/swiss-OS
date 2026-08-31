from __future__ import annotations

import html
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from .application_adversarial import Decision as AAGDecision
from .application_adversarial import SCHEMA_VERSION as AAG_SCHEMA_VERSION


class ApplicationLearningError(ValueError):
    pass


class Outcome(str, Enum):
    INTERVIEW = "INTERVIEW"
    INTEREST = "INTEREST"
    QUESTION = "QUESTION"
    REJECTION_FILLED = "REJECTION_FILLED"
    REJECTION_NO_MATCHING_VACANCY = "REJECTION_NO_MATCHING_VACANCY"
    REJECTION_COMPETITIVE_FIT = "REJECTION_COMPETITIVE_FIT"
    REJECTION_INTERNAL_NEEDS = "REJECTION_INTERNAL_NEEDS"
    REJECTION_REQUIREMENT = "REJECTION_REQUIREMENT"
    REJECTION_GENERIC = "REJECTION_GENERIC"
    NO_REPLY = "NO_REPLY"


class EvidenceClass(str, Enum):
    EXPLICIT_EMPLOYER_REASON = "EXPLICIT_EMPLOYER_REASON"
    STRONG_INFERENCE = "STRONG_INFERENCE"
    WEAK_HYPOTHESIS = "WEAK_HYPOTHESIS"


class Lane(str, Enum):
    HOUSEKEEPING = "HOUSEKEEPING"
    SERVICE_FNB = "SERVICE_FNB"
    KITCHEN_SUPPORT = "KITCHEN_SUPPORT"
    OPERATIONS_GENERAL = "OPERATIONS_GENERAL"
    GUEST_SUPPORT = "GUEST_SUPPORT"
    HYBRID_DIGITAL = "HYBRID_DIGITAL"


HOUSEKEEPING_RE = re.compile(r"housekeep|zimmer|room attendant|reinigung|clean", re.I)
SERVICE_RE = re.compile(r"service|chef de rang|commis de rang|runner|restaurant|bar|frühstück|breakfast|f&b|food and beverage", re.I)
KITCHEN_RE = re.compile(r"kitchen|küche|steward|spül|dish|cuisine|koch|cook", re.I)
GUEST_RE = re.compile(r"reception|front office|guest|concierge|reservations?|empfang", re.I)
DIGITAL_RE = re.compile(r"marketing|content|social|digital|e-?commerce|communication|photo|video|creative|design|web", re.I)


FORBIDDEN_HTML_RE = re.compile(
    r"<(?:script|iframe|form|input|button|object|embed|video|audio|canvas|svg)\b|"
    r"\bon(?:load|error|click|mouseover|focus)\s*=|"
    r"javascript:|data:text/html|"
    r"(?:width|height)\s*=\s*[\"']?1[\"']?",
    re.I,
)

POLITICAL_GRIEVANCE_RE = re.compile(
    r"oppress|opres|escape from spain|huir de españa|sistema español|government|gobierno|politic|polític",
    re.I,
)

MANIPULATIVE_FLATTERY_RE = re.compile(
    r"best country in the world|mejor país del mundo|perfect country|país perfecto|dream company|empresa de mis sueños",
    re.I,
)


@dataclass(frozen=True)
class FeedbackEvent:
    outcome: Outcome
    evidence_class: EvidenceClass
    vacancy_key: str | None = None
    hotel_key: str | None = None


def classify_lane(role_title: str | None) -> Lane:
    role = (role_title or "").strip()
    if DIGITAL_RE.search(role):
        return Lane.HYBRID_DIGITAL
    if HOUSEKEEPING_RE.search(role):
        return Lane.HOUSEKEEPING
    if KITCHEN_RE.search(role):
        return Lane.KITCHEN_SUPPORT
    if SERVICE_RE.search(role):
        return Lane.SERVICE_FNB
    if GUEST_RE.search(role):
        return Lane.GUEST_SUPPORT
    return Lane.OPERATIONS_GENERAL


def feedback_effect(event: FeedbackEvent) -> dict[str, Any]:
    """Return deterministic learning effects without inventing an unstated cause."""
    base = {
        "outcome": event.outcome.value,
        "evidence_class": event.evidence_class.value,
        "causal_inference_allowed": event.evidence_class != EvidenceClass.WEAK_HYPOTHESIS,
        "suppress_exact_vacancy": False,
        "suppress_hotel": False,
        "penalize_spontaneous_retry": False,
        "increase_role_specificity_weight": False,
        "infer_language_failure": False,
        "infer_education_failure": False,
        "infer_work_authorization_failure": False,
        "infer_experience_failure": False,
    }
    if event.outcome == Outcome.REJECTION_FILLED:
        base["suppress_exact_vacancy"] = True
    elif event.outcome == Outcome.REJECTION_NO_MATCHING_VACANCY:
        base["penalize_spontaneous_retry"] = True
    elif event.outcome in {Outcome.REJECTION_COMPETITIVE_FIT, Outcome.REJECTION_INTERNAL_NEEDS}:
        base["increase_role_specificity_weight"] = True
    elif event.outcome == Outcome.REJECTION_REQUIREMENT:
        base["increase_role_specificity_weight"] = True
    elif event.outcome in {Outcome.REJECTION_GENERIC, Outcome.NO_REPLY}:
        base["causal_inference_allowed"] = False
    return base


def _job_title(job: Mapping[str, Any]) -> str | None:
    value = str(job.get("title") or "").strip()
    return value or None


def build_vacancy_first_seed(
    hotel: Mapping[str, Any],
    jobs: Sequence[Mapping[str, Any]],
    careers_url: str | None,
) -> dict[str, Any]:
    """Compile a NO-SEND application seed from public market evidence only."""
    name = str(hotel.get("name") or "el hotel").strip()
    city = str(hotel.get("city") or "Suiza").strip()
    current_titles = [title for title in (_job_title(job) for job in jobs) if title]
    exact_role = current_titles[0] if current_titles else None
    lane = classify_lane(exact_role)

    if exact_role:
        mode = "PRIMARY_EXACT_VACANCY"
        hook = f"He revisado la vacante actual de {exact_role} en {name}, {city}."
    elif careers_url:
        mode = "SPONTANEOUS_FALLBACK_RESEARCH_ONLY"
        hook = f"He revisado la vía oficial de empleo de {name}, {city}, pero aún falta una vacante exacta compatible."
    else:
        mode = "RESEARCH_ONLY_NO_APPLICATION_ROUTE"
        hook = f"Aún falta una vacante o vía oficial de empleo verificable para {name}, {city}."

    portfolio_default = lane == Lane.HYBRID_DIGITAL
    return {
        "strategy_version": "VACANCY-FIRST-APPLICATION-2.0+AAG-3.0",
        "application_mode": mode,
        "hotel_specific_hook": hook,
        "subject_seed": f"Application — {exact_role} | {name}" if exact_role else f"Future vacancy research — {name}",
        "target_role": exact_role,
        "current_roles_observed": current_titles[:10],
        "lane": lane.value,
        "exact_live_vacancy_required_for_primary": True,
        "candidate_truth_block_required": True,
        "candidate_truth_required_fields": [
            "role_relevant_evidence",
            "languages",
            "availability",
            "permanent_relocation",
            "swiss_work_eligibility",
            "contact_identity",
        ],
        "asset_policy": {
            "role_lane_cv_required": True,
            "portfolio_default_attachment": portfolio_default,
            "verified_real_links_only": True,
            "approved_real_headshot_only": True,
            "founder_ceo_claim_requires_evidence": True,
            "founder_ceo_primary_signal_for_operations": False,
        },
        "motivation_policy": {
            "positive_switzerland_pull": True,
            "employer_specific_appreciation_requires_evidence": True,
            "political_grievance_allowed": False,
            "fake_flattery_allowed": False,
        },
        "creative_value_policy": {
            "allowed_as_secondary_differentiator": True,
            "employer_approval_required": True,
            "lawful_agreed_scope_or_working_time_required": True,
            "unconditional_free_off_clock_labor_allowed": False,
        },
        "presentation_policy": {
            "static_html_allowed": True,
            "plain_text_fallback_required": True,
            "javascript_allowed": False,
            "iframe_allowed": False,
            "forms_allowed": False,
            "hidden_tracking_allowed": False,
        },
        "application_adversarial_gate": {
            "required": True,
            "schema_version": AAG_SCHEMA_VERSION,
            "ready_decisions": [AAGDecision.APPLICATION_READY_NO_SEND.value, AAGDecision.ELITE_MATCH.value],
            "hard_fail_compensation_allowed": False,
            "final_send_ready": False,
        },
        "recruiter_10_second_gate_required": True,
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def _aag_receipt_state(candidate_truth: Mapping[str, Any]) -> tuple[bool, str | None, str | None]:
    receipt = candidate_truth.get("application_adversarial_gate")
    if not isinstance(receipt, Mapping):
        return False, None, "AAG_REQUIRED"
    if receipt.get("schema_version") != AAG_SCHEMA_VERSION:
        return False, str(receipt.get("decision") or "") or None, "AAG_SCHEMA_MISMATCH"
    decision = str(receipt.get("decision") or "")
    ready_decisions = {AAGDecision.APPLICATION_READY_NO_SEND.value, AAGDecision.ELITE_MATCH.value}
    if decision not in ready_decisions:
        return False, decision or None, "AAG_NOT_READY"
    if receipt.get("application_ready_no_send") is not True:
        return False, decision, "AAG_READY_FLAG_MISMATCH"
    if receipt.get("final_send_ready") is not False:
        return False, decision, "AAG_SEND_SAFETY_MISMATCH"
    if receipt.get("outbound") != "CLOSED" or receipt.get("send_allowed") != 0:
        return False, decision, "AAG_OUTBOUND_SAFETY_MISMATCH"
    if receipt.get("blockers"):
        return False, decision, "AAG_BLOCKERS_PRESENT"
    if int(receipt.get("application_quality_score") or 0) < 92:
        return False, decision, "AAG_QUALITY_BELOW_READY"
    if int(receipt.get("evidence_confidence_score") or 0) < 95:
        return False, decision, "AAG_EVIDENCE_BELOW_READY"
    if int(receipt.get("employer_risk_score") or 100) > 20:
        return False, decision, "AAG_EMPLOYER_RISK_TOO_HIGH"
    if int(receipt.get("desperation_score") or 100) > 15:
        return False, decision, "AAG_DESPERATION_TOO_HIGH"
    if int(receipt.get("human_resonance_score") or 0) < 85:
        return False, decision, "AAG_RESONANCE_BELOW_READY"
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
    aag_pass, aag_decision, aag_failure = _aag_receipt_state(candidate_truth)
    if not aag_pass and aag_failure:
        failures.append(aag_failure)
    return {
        "pass": not failures,
        "failures": failures,
        "missing_candidate_truth": missing,
        "exact_role": exact_role,
        "lane": seed.get("lane"),
        "portfolio_default_attachment": bool((seed.get("asset_policy") or {}).get("portfolio_default_attachment")),
        "aag_schema_version": AAG_SCHEMA_VERSION,
        "aag_decision": aag_decision,
        "aag_pass": aag_pass,
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def validate_motivation_text(text: str) -> None:
    if POLITICAL_GRIEVANCE_RE.search(text):
        raise ApplicationLearningError("political grievance/victimhood framing is not allowed")
    if MANIPULATIVE_FLATTERY_RE.search(text):
        raise ApplicationLearningError("generic manipulative flattery is not allowed")


def validate_email_html(html_text: str, plain_text: str) -> None:
    if not plain_text.strip():
        raise ApplicationLearningError("plain-text fallback is required")
    if FORBIDDEN_HTML_RE.search(html_text):
        raise ApplicationLearningError("unsafe or low-deliverability HTML feature detected")


def render_static_profile_card(
    *,
    display_name: str,
    role: str,
    motivation: str,
    verified_links: Sequence[Mapping[str, str]],
    headshot_url: str | None = None,
    headshot_approved: bool = False,
) -> tuple[str, str]:
    validate_motivation_text(motivation)
    if headshot_url and not headshot_approved:
        raise ApplicationLearningError("headshot must be an approved real asset")
    links = []
    for link in verified_links:
        label = str(link.get("label") or "").strip()
        url = str(link.get("url") or "").strip()
        if not label or not url.startswith("https://") or str(link.get("verified") or "").lower() != "true":
            raise ApplicationLearningError("all profile links must be verified HTTPS assets")
        links.append((label, url))
    image = (
        f'<img src="{html.escape(headshot_url, quote=True)}" alt="Portrait of {html.escape(display_name)}" width="64" height="64" style="border-radius:50%;display:block">'
        if headshot_url
        else ""
    )
    link_html = " · ".join(
        f'<a href="{html.escape(url, quote=True)}" style="color:#1f4b99">{html.escape(label)}</a>'
        for label, url in links
    )
    html_text = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="font-family:Arial,sans-serif;max-width:560px">'
        '<tr><td style="padding-right:14px;vertical-align:top">'
        f"{image}</td><td>"
        f'<strong>{html.escape(display_name)}</strong><br>'
        f'{html.escape(role)}<br>'
        f'<span>{html.escape(motivation)}</span>'
        + (f'<br><span>{link_html}</span>' if link_html else "")
        + '</td></tr></table>'
    )
    plain = f"{display_name}\n{role}\n{motivation}"
    if links:
        plain += "\n" + " | ".join(f"{label}: {url}" for label, url in links)
    validate_email_html(html_text, plain)
    return html_text, plain
