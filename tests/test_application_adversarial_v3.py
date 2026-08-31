import unittest

from swiss_os.application_adversarial import (
    AuditState,
    Decision,
    DIMENSION_WEIGHTS,
    HARD_GATE_EXPECTED,
    QUESTION_BANK,
    RISK_COMPONENTS,
    STAKEHOLDERS,
    evaluate_application,
    evaluate_hard_gates,
    evaluate_questionnaire,
    question_bank_public_contract,
)


class ApplicationAdversarialGateV3Tests(unittest.TestCase):
    def complete_dimensions(self, score=95):
        return {key: score for key in DIMENSION_WEIGHTS}

    def passing_hard_gates(self):
        return dict(HARD_GATE_EXPECTED)

    def low_risk(self, score=10):
        return {key: score for key in RISK_COMPONENTS}

    def all_questions(self, state=AuditState.PASS):
        return {question.question_id: state.value for question in QUESTION_BANK}

    def all_stakeholders(self, vote=True):
        return {stakeholder: vote for stakeholder in STAKEHOLDERS}

    def evaluate(self, **overrides):
        data = {
            "dimension_scores": self.complete_dimensions(),
            "hard_gate_states": self.passing_hard_gates(),
            "risk_scores": self.low_risk(),
            "evidence_confidence_score": 98,
            "human_resonance_score": 92,
            "desperation_score": 5,
            "questionnaire_answers": self.all_questions(),
            "stakeholder_votes": self.all_stakeholders(),
        }
        data.update(overrides)
        return evaluate_application(**data)

    def test_contract_is_exactly_100_points_100_questions_and_six_stakeholders(self):
        self.assertEqual(sum(DIMENSION_WEIGHTS.values()), 100)
        self.assertEqual(len(DIMENSION_WEIGHTS), 19)
        self.assertEqual(len(QUESTION_BANK), 100)
        self.assertEqual(len({q.question_id for q in QUESTION_BANK}), 100)
        self.assertEqual(len(question_bank_public_contract()), 100)
        self.assertEqual(len(STAKEHOLDERS), 6)
        self.assertEqual(len(RISK_COMPONENTS), 10)

    def test_hard_failure_cannot_be_compensated_by_perfect_soft_scores(self):
        hard = self.passing_hard_gates()
        hard["mandatory_language_met"] = False
        result = self.evaluate(
            dimension_scores=self.complete_dimensions(100),
            hard_gate_states=hard,
            evidence_confidence_score=100,
            human_resonance_score=100,
            desperation_score=0,
            risk_scores=self.low_risk(0),
        )
        self.assertEqual(result["application_quality_score"], 100)
        self.assertEqual(result["decision"], Decision.REJECT.value)
        self.assertIn("HARD_FAIL:mandatory_language_met", result["blockers"])
        self.assertFalse(result["application_ready_no_send"])
        self.assertFalse(result["final_send_ready"])
        self.assertEqual(result["send_allowed"], 0)

    def test_unknown_hard_gate_forces_limbo_not_ready(self):
        hard = self.passing_hard_gates()
        hard["contact_route_verified"] = None
        result = self.evaluate(hard_gate_states=hard)
        self.assertEqual(result["decision"], Decision.LIMBO.value)
        self.assertIn("HARD_UNKNOWN:contact_route_verified", result["blockers"])

    def test_quality_95_can_still_be_limbo_on_weak_evidence(self):
        result = self.evaluate(evidence_confidence_score=80)
        self.assertEqual(result["application_quality_score"], 95)
        self.assertEqual(result["decision"], Decision.LIMBO.value)
        self.assertIn("EVIDENCE_CONFIDENCE_LT_95", result["blockers"])

    def test_employer_risk_and_desperation_are_independent_gates(self):
        risk = self.low_risk(10)
        risk["flight_risk"] = 100
        risk["overqualification_risk"] = 100
        risk["role_confusion_risk"] = 100
        risk["retention_risk"] = 100
        result = self.evaluate(risk_scores=risk, desperation_score=40)
        self.assertEqual(result["decision"], Decision.LIMBO.value)
        self.assertIn("EMPLOYER_RISK_GT_20", result["blockers"])
        self.assertIn("DESPERATION_GT_15", result["blockers"])

    def test_six_of_six_stakeholders_required_for_readiness(self):
        votes = self.all_stakeholders()
        votes["DEPARTMENT_HEAD"] = False
        result = self.evaluate(stakeholder_votes=votes)
        self.assertEqual(result["stakeholders"]["yes"], 5)
        self.assertFalse(result["stakeholders"]["unanimous_yes"])
        self.assertEqual(result["decision"], Decision.LIMBO.value)
        self.assertIn("STAKEHOLDER_NO:DEPARTMENT_HEAD", result["blockers"])

    def test_unanswered_questionnaire_never_reaches_ready(self):
        answers = self.all_questions()
        answers.pop(QUESTION_BANK[-1].question_id)
        result = self.evaluate(questionnaire_answers=answers)
        self.assertEqual(result["questionnaire"]["answered_explicitly"], 99)
        self.assertIn("QUESTIONNAIRE_NOT_100_EXPLICIT", result["blockers"])
        self.assertNotIn(result["decision"], {Decision.APPLICATION_READY_NO_SEND.value, Decision.ELITE_MATCH.value})

    def test_critical_question_failure_is_terminal_reject(self):
        critical = next(question for question in QUESTION_BANK if question.critical)
        answers = self.all_questions()
        answers[critical.question_id] = AuditState.FAIL.value
        result = self.evaluate(questionnaire_answers=answers)
        self.assertEqual(result["decision"], Decision.REJECT.value)
        self.assertIn(critical.question_id, result["questionnaire"]["critical_failures"])

    def test_unknown_soft_dimension_is_exposed_and_blocks_readiness(self):
        dims = self.complete_dimensions()
        dims["portfolio_proof"] = None
        result = self.evaluate(dimension_scores=dims)
        self.assertFalse(result["quality_complete"])
        self.assertIn("portfolio_proof", result["hard_gates"].get("unknown", []) if False else result["blockers"][0:])
        self.assertIn("UNKNOWN_DIMENSION:portfolio_proof", result["blockers"])
        self.assertEqual(result["decision"], Decision.LIMBO.value)

    def test_application_ready_no_send_thresholds(self):
        result = self.evaluate()
        self.assertEqual(result["decision"], Decision.APPLICATION_READY_NO_SEND.value)
        self.assertTrue(result["application_ready_no_send"])
        self.assertFalse(result["final_send_ready"])
        self.assertEqual(result["outbound"], "CLOSED")
        self.assertEqual(result["send_allowed"], 0)
        self.assertEqual(result["calibration_state"], "HEURISTIC_UNCALIBRATED_UNTIL_OUTCOME_SAMPLE")

    def test_elite_match_is_still_no_send(self):
        result = self.evaluate(
            dimension_scores=self.complete_dimensions(99),
            evidence_confidence_score=100,
            human_resonance_score=98,
            desperation_score=0,
            risk_scores=self.low_risk(5),
        )
        self.assertEqual(result["decision"], Decision.ELITE_MATCH.value)
        self.assertTrue(result["elite_match"])
        self.assertTrue(result["application_ready_no_send"])
        self.assertFalse(result["final_send_ready"])
        self.assertEqual(result["send_allowed"], 0)

    def test_hard_gate_contract_has_no_ambiguous_score_semantics(self):
        result = evaluate_hard_gates(self.passing_hard_gates())
        self.assertTrue(result["pass"])
        self.assertEqual(result["failures"], [])
        self.assertEqual(result["unknown"], [])

    def test_questionnaire_category_counts_match_design(self):
        counts = {}
        for question in QUESTION_BANK:
            counts[question.category] = counts.get(question.category, 0) + 1
        self.assertEqual(counts["eligibility"], 10)
        self.assertEqual(counts["vacancy_requirements"], 15)
        self.assertEqual(counts["languages"], 10)
        self.assertEqual(counts["experience"], 10)
        self.assertEqual(counts["operational_credibility"], 10)
        self.assertEqual(counts["employer_risk"], 10)
        self.assertEqual(counts["culture_brand"], 10)
        self.assertEqual(counts["evidence"], 10)
        self.assertEqual(counts["relocation"], 5)
        self.assertEqual(counts["email"], 5)
        self.assertEqual(counts["portfolio"], 5)


if __name__ == "__main__":
    unittest.main()
