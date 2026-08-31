import unittest

from swiss_os.application_adversarial import (
    AuditState,
    DIMENSION_WEIGHTS,
    HARD_GATE_EXPECTED,
    QUESTION_BANK,
    RISK_COMPONENTS,
    STAKEHOLDERS,
    evaluate_application,
)
from swiss_os.application_learning import build_vacancy_first_seed, recruiter_10_second_gate


class AAGReceiptEdgeTests(unittest.TestCase):
    def test_zero_risk_and_zero_desperation_are_valid_ready_values(self):
        receipt = evaluate_application(
            dimension_scores={key: 99 for key in DIMENSION_WEIGHTS},
            hard_gate_states=dict(HARD_GATE_EXPECTED),
            risk_scores={key: 0 for key in RISK_COMPONENTS},
            evidence_confidence_score=100,
            human_resonance_score=100,
            desperation_score=0,
            questionnaire_answers={q.question_id: AuditState.PASS.value for q in QUESTION_BANK},
            stakeholder_votes={stakeholder: True for stakeholder in STAKEHOLDERS},
        )
        self.assertTrue(receipt["application_ready_no_send"])
        self.assertEqual(receipt["employer_risk_score"], 0)
        self.assertEqual(receipt["desperation_score"], 0)

        seed = build_vacancy_first_seed(
            {"name": "Hotel Test", "city": "Davos"},
            [{"title": "Housekeeping Attendant"}],
            "https://hotel.example/careers",
        )
        truth = {
            "role_relevant_evidence": [{"claim": "verified"}],
            "languages": "verified",
            "availability": "verified",
            "permanent_relocation": "verified",
            "swiss_work_eligibility": "verified",
            "contact_identity": "verified",
            "application_adversarial_gate": receipt,
        }
        gate = recruiter_10_second_gate(seed, truth)
        self.assertTrue(gate["pass"], gate["failures"])
        self.assertTrue(gate["aag_pass"])
        self.assertFalse(gate["final_send_ready"])
        self.assertEqual(gate["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
