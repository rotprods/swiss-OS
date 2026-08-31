from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "APPLICATION-ADVERSARIAL-GATE-3.0"
CALIBRATION_STATE = "HEURISTIC_UNCALIBRATED_UNTIL_OUTCOME_SAMPLE"


class AdversarialGateError(ValueError):
    pass


class AuditState(str, Enum):
    PASS = "PASS"
    WEAK = "WEAK"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Decision(str, Enum):
    REJECT = "REJECT"
    WEAK = "WEAK"
    PROMISING = "PROMISING"
    LIMBO = "LIMBO"
    APPLICATION_READY_NO_SEND = "APPLICATION_READY_NO_SEND"
    ELITE_MATCH = "ELITE_MATCH"


DIMENSION_WEIGHTS: dict[str, int] = {
    "eligibility_permit": 8,
    "vacancy_freshness": 8,
    "hard_requirement_match": 10,
    "role_evidence_match": 9,
    "language_match": 7,
    "start_schedule_availability": 5,
    "relocation_logistics": 4,
    "experience_credibility": 7,
    "operational_readiness": 6,
    "brand_fit": 4,
    "motivation_specificity": 4,
    "retention_permanence": 4,
    "employer_risk_profile": 5,
    "additional_value_relevance": 5,
    "portfolio_proof": 5,
    "email_communication": 4,
    "ats_deliverability": 3,
    "reply_friction": 1,
    "housing_economic_compatibility": 1,
}

if sum(DIMENSION_WEIGHTS.values()) != 100:
    raise RuntimeError("AAG dimension weights must total exactly 100")


# Expected values are intentionally explicit. A false/unknown hard gate cannot be
# compensated by a strong email, portfolio or aggregate score.
HARD_GATE_EXPECTED: dict[str, bool] = {
    "vacancy_current": True,
    "exact_role_verified": True,
    "mandatory_language_met": True,
    "work_eligibility_met": True,
    "mandatory_experience_met": True,
    "start_date_compatible": True,
    "contact_route_verified": True,
    "unsupported_claim_present": False,
    "suppression_match": False,
    "duplicate_application": False,
    "vacancy_filled": False,
}

STAKEHOLDERS = (
    "ATS_RECRUITER",
    "DEPARTMENT_HEAD",
    "HR_MANAGER",
    "GENERAL_MANAGER_CEO",
    "BRAND_PR",
    "CANDIDATE_LONG_TERM_FIT",
)

RISK_COMPONENTS = (
    "flight_risk",
    "overqualification_risk",
    "ego_hierarchy_risk",
    "operational_credibility_risk",
    "language_risk",
    "relocation_risk",
    "housing_risk",
    "role_confusion_risk",
    "brand_risk",
    "retention_risk",
)


@dataclass(frozen=True)
class AuditQuestion:
    question_id: str
    category: str
    stakeholder: str
    text: str
    critical: bool = False


def _questions(category: str, stakeholder: str, texts: Sequence[str], critical: set[int] | None = None) -> list[AuditQuestion]:
    critical = critical or set()
    prefix = {
        "eligibility": "ELG",
        "vacancy_requirements": "VAC",
        "languages": "LAN",
        "experience": "EXP",
        "operational_credibility": "OPS",
        "employer_risk": "RSK",
        "culture_brand": "BRD",
        "evidence": "EVD",
        "relocation": "REL",
        "email": "EML",
        "portfolio": "PRT",
    }[category]
    return [
        AuditQuestion(f"{prefix}-{index:02d}", category, stakeholder, text, index in critical)
        for index, text in enumerate(texts, start=1)
    ]


QUESTION_BANK: tuple[AuditQuestion, ...] = tuple(
    _questions(
        "eligibility",
        "HR_MANAGER",
        [
            "¿La identidad del candidato está verificada y coincide en CV, email y formularios?",
            "¿La ciudadanía/nacionalidad usada para la ruta laboral está respaldada por Candidate Truth?",
            "¿La vacante admite la ruta de elegibilidad del candidato sin inventar excepciones?",
            "¿La explicación de permiso/registro suizo es exacta y no promete 'no permit required' incorrectamente?",
            "¿Existe algún requisito de residencia o permiso previo que el candidato no cumpla?",
            "¿La vacancy impone restricciones Swiss/EU/EFTA y el candidato las supera explícitamente?",
            "¿La documentación exigida puede producirse de forma veraz antes del inicio?",
            "¿Hay una dependencia legal/administrativa no resuelta que pueda impedir el comienzo?",
            "¿El paquete evita afirmaciones jurídicas más amplias que la evidencia oficial disponible?",
            "¿HR podría explicar internamente la elegibilidad del candidato en una frase sin dudas críticas?",
        ],
        {1, 2, 3, 4, 5, 6, 8, 10},
    )
    + _questions(
        "vacancy_requirements",
        "ATS_RECRUITER",
        [
            "¿La vacante sigue publicada o ha sido revalidada como actual?",
            "¿Existe un título de puesto exacto y no una candidatura genérica a cinco departamentos?",
            "¿Se ha extraído cada requisito obligatorio del anuncio actual?",
            "¿Se distingue requisito obligatorio de preferencia/deseable?",
            "¿El candidato cumple todos los requisitos obligatorios no negociables?",
            "¿La candidatura responde a esa vacante exacta desde el asunto y primer párrafo?",
            "¿La fecha de inicio solicitada por el hotel es compatible con la disponibilidad real?",
            "¿Turnos, fines de semana, nocturnidad o estacionalidad requeridos son compatibles?",
            "¿La ubicación concreta y necesidad de presencia física están asumidas?",
            "¿Se ha comprobado si el puesto ya fue cubierto o retirado?",
            "¿La ruta de aplicación usada es la indicada por el hotel para esa vacante?",
            "¿El hotel pide documentos/certificados que aún no están disponibles?",
            "¿El anuncio requiere experiencia hotelera específica y está tratada como hard gate si corresponde?",
            "¿El rol pertenece realmente a la lane CV seleccionada?",
            "¿Un recruiter entendería en diez segundos por qué este paquete corresponde a ESTE anuncio?",
        ],
        {1, 2, 3, 5, 7, 8, 10, 11, 12, 13, 15},
    )
    + _questions(
        "languages",
        "ATS_RECRUITER",
        [
            "¿Cada idioma obligatorio del anuncio está identificado?",
            "¿El nivel del candidato está expresado exactamente como está verificado?",
            "¿Se evita convertir uso práctico en certificación CEFR inexistente?",
            "¿Un idioma preferido se distingue de uno obligatorio?",
            "¿El puesto implica contacto con huéspedes que eleva el umbral lingüístico real?",
            "¿El idioma de trabajo del equipo puede manejarse con el nivel disponible?",
            "¿El CV y el email usan el mismo wording lingüístico?",
            "¿La ausencia de alemán/francés bloquea este rol concreto o solo reduce fit?",
            "¿Hay certificado obligatorio y, si lo hay, existe?",
            "¿No estamos compensando un idioma obligatorio incumplido con creatividad u otras fortalezas?",
        ],
        {1, 2, 3, 5, 8, 9, 10},
    )
    + _questions(
        "experience",
        "DEPARTMENT_HEAD",
        [
            "¿El CV contiene experiencia o evidencia directamente transferible al trabajo diario del rol?",
            "¿Las fechas, organizaciones/proyectos y responsabilidades afirmadas son trazables?",
            "¿La experiencia presentada responde al puesto en vez de exhibir capacidades irrelevantes?",
            "¿Si se exige experiencia comparable, podemos demostrarla realmente?",
            "¿Se distingue claramente experiencia profesional, proyecto propio, formación y hobby?",
            "¿Founder/CEO/operator se usa solo donde está probado y aporta contexto útil?",
            "¿Los resultados cuantitativos tienen evidencia y no son cifras de marketing no verificadas?",
            "¿Los gaps de experiencia se reconocen sin intentar maquillarlos con buzzwords?",
            "¿La experiencia demuestra responsabilidad, autonomía o trato con clientes cuando el rol lo necesita?",
            "¿El department head vería capacidad de aprendizaje suficiente para cualquier gap no obligatorio?",
        ],
        {1, 2, 4, 5, 7},
    )
    + _questions(
        "operational_credibility",
        "DEPARTMENT_HEAD",
        [
            "¿Parece capaz de cumplir la función principal antes de hablar de marketing/IA?",
            "¿Hay evidencia de fiabilidad, puntualidad, responsabilidad o entrega bajo presión?",
            "¿El paquete transmite humildad operacional y disposición a recibir instrucciones?",
            "¿Puede tolerar el componente físico/ritmo/turnos cuando el puesto lo exige?",
            "¿Entiende estándares, detalle y consistencia en hospitality?",
            "¿Puede trabajar en equipo sin necesitar autonomía total?",
            "¿La candidatura reduce el miedo a que abandone el rol por considerarlo 'por debajo' de su background?",
            "¿Se muestra capacidad de discreción y profesionalidad delante de huéspedes?",
            "¿El valor creativo adicional aparece como opcional y subordinado al rol contratado?",
            "¿El jefe del departamento podría imaginarlo haciendo el trabajo la próxima semana?",
        ],
        {1, 3, 4, 7, 9, 10},
    )
    + _questions(
        "employer_risk",
        "HR_MANAGER",
        [
            "¿La intención de permanencia reduce razonablemente el flight risk?",
            "¿La motivación por Suiza parece un proyecto vital estable y no una fantasía turística?",
            "¿La narrativa explica de forma creíble por qué un founder/operator acepta empezar en operations?",
            "¿El paquete evita señales de ego o resistencia a jerarquías?",
            "¿Evita parecer que busca captar al hotel como cliente de su agencia?",
            "¿Evita prometer trabajo gratuito incondicional que pueda generar problemas de scope?",
            "¿El candidato parece económicamente/logísticamente capaz de ejecutar la mudanza si recibe oferta?",
            "¿Existe riesgo de conflicto entre actividad externa y obligaciones del empleo que deba aclararse?",
            "¿La candidatura evita desperation signals como 'cualquier puesto', victimismo o sobrehalago?",
            "¿HR consideraría el riesgo global de entrevista bajo comparado con el upside potencial?",
        ],
        {3, 4, 5, 6, 9, 10},
    )
    + _questions(
        "culture_brand",
        "GENERAL_MANAGER_CEO",
        [
            "¿La motivación menciona razones específicas y verificables del hotel/lugar?",
            "¿El tono demuestra respeto sin adulación genérica?",
            "¿La candidatura refleja servicio, responsabilidad, colaboración y orientación al huésped?",
            "¿La ambición se presenta como crecimiento dentro de Suiza y no como superioridad sobre el puesto?",
            "¿La personalidad percibida encaja razonablemente con el posicionamiento del hotel?",
            "¿El paquete entiende si la marca es lujo discreto, lifestyle, familiar, business o alpine?",
            "¿El candidato muestra curiosidad real por el establecimiento además de por Suiza?",
            "¿Evita usar naturaleza/paisaje como cliché cuando no aporta una conexión específica?",
            "¿El GM podría ver potencial de crecimiento sin temer inestabilidad inmediata?",
            "¿RRHH estaría cómodo reenviando el paquete al GM sin añadir explicaciones defensivas?",
        ],
        {1, 2, 3, 4, 9, 10},
    )
    + _questions(
        "evidence",
        "HR_MANAGER",
        [
            "¿Cada claim de alto valor del CV tiene fuente/evidencia recuperable?",
            "¿Los links profesionales pertenecen realmente al candidato y están vivos?",
            "¿La fotografía de CV es real, aprobada y profesional?",
            "¿Las webs/apps presentadas están accesibles o documentadas con evidencia suficiente?",
            "¿Los casos de fotografía/vídeo muestran trabajo real atribuible al candidato?",
            "¿Las métricas están respaldadas por fuente y periodo, no por memoria vaga?",
            "¿Los títulos founder/CEO/creative director están documentados antes de usarse externamente?",
            "¿No hay repos forks/demos de terceros presentados como creación propia?",
            "¿El evidence confidence global supera el umbral exigido para readiness?",
            "¿Una auditoría externa podría reconstruir por qué cada afirmación fue permitida?",
        ],
        {1, 2, 3, 4, 5, 6, 7, 8, 9, 10},
    )
    + _questions(
        "relocation",
        "HR_MANAGER",
        [
            "¿La intención de mudanza permanente/indefinida está expresada sin exigir contrato permanente inicial?",
            "¿El candidato está abierto a una puerta de entrada estacional compatible con su proyecto de largo plazo?",
            "¿La fecha exacta de incorporación puede alinearse con el empleador?",
            "¿Housing/transporte/localización presentan algún blocker real no resuelto?",
            "¿La mudanza parece operativamente ejecutable si llega una oferta?",
        ],
        {1, 3, 5},
    )
    + _questions(
        "email",
        "ATS_RECRUITER",
        [
            "¿El subject contiene la vacante exacta y el nombre del candidato sin gimmicks?",
            "¿El primer bloque comunica role fit, disponibilidad y elegibilidad con fricción mínima?",
            "¿El email puede escanearse en menos de un minuto y entenderse en diez segundos?",
            "¿La firma HTML es estática, ligera, compatible y tiene fallback de texto plano?",
            "¿El CTA pide una siguiente acción simple, normalmente entrevista/conversación?",
        ],
        {1, 2, 3, 4, 5},
    )
    + _questions(
        "portfolio",
        "BRAND_PR",
        [
            "¿El portfolio enseña 3–5 pruebas fuertes en vez de una lista de herramientas?",
            "¿Cada caso explica problema, aportación, entregables, evidencia/resultado y visuales?",
            "¿El nivel visual sería defendible delante del responsable de marca del hotel?",
            "¿El portfolio respeta privacidad, derechos de imagen y contexto de clientes/proyectos?",
            "¿El portfolio solo se adjunta por defecto cuando la lane/rol se beneficia de él?",
        ],
        {1, 2, 3, 4, 5},
    )
)

if len(QUESTION_BANK) != 100 or len({q.question_id for q in QUESTION_BANK}) != 100:
    raise RuntimeError("AAG question bank must contain exactly 100 unique questions")


def _score(value: Any, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdversarialGateError(f"{field} must be numeric 0..100 or null")
    number = int(round(float(value)))
    if number < 0 or number > 100:
        raise AdversarialGateError(f"{field} outside 0..100")
    return number


def weighted_quality(dimension_scores: Mapping[str, Any]) -> dict[str, Any]:
    unknown: list[str] = []
    contributions: dict[str, float] = {}
    total = 0.0
    for dimension, weight in DIMENSION_WEIGHTS.items():
        value = _score(dimension_scores.get(dimension), field=dimension)
        if value is None:
            unknown.append(dimension)
            value = 0
        contribution = value * weight / 100.0
        contributions[dimension] = round(contribution, 2)
        total += contribution
    return {
        "score": int(round(total)),
        "complete": not unknown,
        "unknown_dimensions": unknown,
        "contributions": contributions,
    }


def evaluate_hard_gates(states: Mapping[str, bool | None]) -> dict[str, Any]:
    failures: list[str] = []
    unknown: list[str] = []
    for gate, expected in HARD_GATE_EXPECTED.items():
        observed = states.get(gate)
        if observed is None:
            unknown.append(gate)
        elif not isinstance(observed, bool):
            raise AdversarialGateError(f"hard gate {gate} must be boolean/null")
        elif observed != expected:
            failures.append(gate)
    return {"pass": not failures and not unknown, "failures": failures, "unknown": unknown}


def evaluate_risk(risk_scores: Mapping[str, Any]) -> dict[str, Any]:
    values: list[int] = []
    unknown: list[str] = []
    normalized: dict[str, int | None] = {}
    for component in RISK_COMPONENTS:
        value = _score(risk_scores.get(component), field=component)
        normalized[component] = value
        if value is None:
            unknown.append(component)
        else:
            values.append(value)
    score = int(round(sum(values) / len(values))) if values else 100
    return {"score": score, "complete": not unknown, "unknown_components": unknown, "components": normalized}


def evaluate_questionnaire(answers: Mapping[str, str | AuditState]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    critical_failures: list[str] = []
    critical_unknown: list[str] = []
    unanswered: list[str] = []
    normalized: dict[str, str] = {}
    for question in QUESTION_BANK:
        raw = answers.get(question.question_id)
        if raw is None:
            unanswered.append(question.question_id)
            state = AuditState.UNKNOWN
        else:
            try:
                state = raw if isinstance(raw, AuditState) else AuditState(str(raw))
            except ValueError as exc:
                raise AdversarialGateError(f"invalid answer state for {question.question_id}") from exc
        normalized[question.question_id] = state.value
        counts[state.value] += 1
        if question.critical and state == AuditState.FAIL:
            critical_failures.append(question.question_id)
        if question.critical and state == AuditState.UNKNOWN:
            critical_unknown.append(question.question_id)
    return {
        "total": 100,
        "answered_explicitly": 100 - len(unanswered),
        "counts": {state.value: counts[state.value] for state in AuditState},
        "critical_failures": critical_failures,
        "critical_unknown": critical_unknown,
        "unanswered": unanswered,
        "answers": normalized,
    }


def evaluate_stakeholders(votes: Mapping[str, bool | None]) -> dict[str, Any]:
    no: list[str] = []
    unknown: list[str] = []
    for stakeholder in STAKEHOLDERS:
        vote = votes.get(stakeholder)
        if vote is None:
            unknown.append(stakeholder)
        elif not isinstance(vote, bool):
            raise AdversarialGateError(f"stakeholder vote {stakeholder} must be boolean/null")
        elif not vote:
            no.append(stakeholder)
    return {
        "yes": len(STAKEHOLDERS) - len(no) - len(unknown),
        "total": len(STAKEHOLDERS),
        "no": no,
        "unknown": unknown,
        "unanimous_yes": not no and not unknown,
    }


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
    quality = weighted_quality(dimension_scores)
    hard = evaluate_hard_gates(hard_gate_states)
    risk = evaluate_risk(risk_scores)
    questions = evaluate_questionnaire(questionnaire_answers)
    stakeholders = evaluate_stakeholders(stakeholder_votes)
    evidence = _score(evidence_confidence_score, field="evidence_confidence_score")
    resonance = _score(human_resonance_score, field="human_resonance_score")
    desperation = _score(desperation_score, field="desperation_score")
    evidence = 0 if evidence is None else evidence
    resonance = 0 if resonance is None else resonance
    desperation = 100 if desperation is None else desperation

    quality_score = quality["score"]
    critical_reject = bool(hard["failures"] or questions["critical_failures"])

    ready_contract = (
        not critical_reject
        and not hard["unknown"]
        and quality["complete"]
        and risk["complete"]
        and not questions["critical_unknown"]
        and questions["answered_explicitly"] == 100
        and stakeholders["unanimous_yes"]
        and quality_score >= 92
        and evidence >= 95
        and risk["score"] <= 20
        and desperation <= 15
        and resonance >= 85
    )

    if critical_reject or quality_score < 60:
        decision = Decision.REJECT
    elif quality_score < 75:
        decision = Decision.WEAK
    elif quality_score < 85:
        decision = Decision.PROMISING
    elif ready_contract and quality_score >= 97:
        decision = Decision.ELITE_MATCH
    elif ready_contract:
        decision = Decision.APPLICATION_READY_NO_SEND
    else:
        decision = Decision.LIMBO

    # Deliberately heuristic and separately labelled. It is not a calibrated hire probability.
    confidence_adjusted = round(
        (quality_score * 0.55 + evidence * 0.25 + resonance * 0.20)
        * (1.0 - min(risk["score"], 100) / 200.0)
    )
    confidence_adjusted = max(0, min(100, confidence_adjusted))

    blockers: list[str] = []
    blockers.extend(f"HARD_FAIL:{item}" for item in hard["failures"])
    blockers.extend(f"HARD_UNKNOWN:{item}" for item in hard["unknown"])
    blockers.extend(f"CRITICAL_QUESTION_FAIL:{item}" for item in questions["critical_failures"])
    blockers.extend(f"CRITICAL_QUESTION_UNKNOWN:{item}" for item in questions["critical_unknown"])
    blockers.extend(f"UNKNOWN_DIMENSION:{item}" for item in quality["unknown_dimensions"])
    blockers.extend(f"UNKNOWN_RISK:{item}" for item in risk["unknown_components"])
    blockers.extend(f"STAKEHOLDER_NO:{item}" for item in stakeholders["no"])
    blockers.extend(f"STAKEHOLDER_UNKNOWN:{item}" for item in stakeholders["unknown"])
    if questions["answered_explicitly"] != 100:
        blockers.append("QUESTIONNAIRE_NOT_100_EXPLICIT")
    if evidence < 95:
        blockers.append("EVIDENCE_CONFIDENCE_LT_95")
    if risk["score"] > 20:
        blockers.append("EMPLOYER_RISK_GT_20")
    if desperation > 15:
        blockers.append("DESPERATION_GT_15")
    if resonance < 85:
        blockers.append("HUMAN_RESONANCE_LT_85")
    if quality_score < 92:
        blockers.append("APPLICATION_QUALITY_LT_92")

    return {
        "schema_version": SCHEMA_VERSION,
        "calibration_state": CALIBRATION_STATE,
        "decision": decision.value,
        "application_quality_score": quality_score,
        "quality_complete": quality["complete"],
        "dimension_contributions": quality["contributions"],
        "evidence_confidence_score": evidence,
        "employer_risk_score": risk["score"],
        "risk_complete": risk["complete"],
        "human_resonance_score": resonance,
        "desperation_score": desperation,
        "confidence_adjusted_score": confidence_adjusted,
        "hard_gates": hard,
        "questionnaire": questions,
        "stakeholders": stakeholders,
        "blockers": sorted(set(blockers)),
        "application_ready_no_send": decision in {Decision.APPLICATION_READY_NO_SEND.value, Decision.ELITE_MATCH.value},
        "elite_match": decision == Decision.ELITE_MATCH.value,
        "final_send_ready": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }


def question_bank_public_contract() -> list[dict[str, Any]]:
    return [
        {
            "question_id": q.question_id,
            "category": q.category,
            "stakeholder": q.stakeholder,
            "text": q.text,
            "critical": q.critical,
        }
        for q in QUESTION_BANK
    ]
