import unittest

from swiss_os.application_adversarial import (
    AuditState,
    DIMENSION_WEIGHTS,
    HARD_GATE_EXPECTED as BASE_HARD_GATES,
    QUESTION_BANK,
    RISK_COMPONENTS,
    STAKEHOLDERS,
    evaluate_application as evaluate_v30,
)
from swiss_os.application_adversarial_v31 import (
    HARD_GATE_EXPECTED,
    SCHEMA_VERSION,
    VACANCY_PROVENANCE_HARD_GATES,
    evaluate_application,
)
from swiss_os.application_learning_v31 import build_vacancy_first_seed, recruiter_10_second_gate
from swiss_os.application_private_v31 import compile_private_packet


class ApplicationAdversarialV31Tests(unittest.TestCase):
    def dimensions(self, score=96):
        return {key: score for key in DIMENSION_WEIGHTS}

    def risk(self, score=8):
        return {key: score for key in RISK_COMPONENTS}

    def questions(self):
        return {q.question_id: AuditState.PASS.value for q in QUESTION_BANK}

    def stakeholders(self):
        return {key: True for key in STAKEHOLDERS}

    def hard31(self):
        return dict(HARD_GATE_EXPECTED)

    def evaluate31(self, hard=None):
        return evaluate_application(
            dimension_scores=self.dimensions(),
            hard_gate_states=hard or self.hard31(),
            risk_scores=self.risk(),
            evidence_confidence_score=99,
            human_resonance_score=94,
            desperation_score=4,
            questionnaire_answers=self.questions(),
            stakeholder_votes=self.stakeholders(),
        )

    def test_contract_expands_to_sixteen_noncompensable_hard_gates(self):
        self.assertEqual(len(BASE_HARD_GATES), 11)
        self.assertEqual(len(VACANCY_PROVENANCE_HARD_GATES), 5)
        self.assertEqual(len(HARD_GATE_EXPECTED), 16)
        self.assertEqual(SCHEMA_VERSION, "APPLICATION-ADVERSARIAL-GATE-3.1")

    def test_perfect_soft_scores_cannot_compensate_wrong_employer_scope(self):
        hard = self.hard31()
        hard["employer_scope_verified"] = False
        receipt = self.evaluate31(hard)
        self.assertEqual(receipt["decision"], "REJECT")
        self.assertIn("HARD_FAIL:employer_scope_verified", receipt["blockers"])
        self.assertFalse(receipt["application_ready_no_send"])

    def test_unknown_temporal_validity_forces_limbo(self):
        hard = self.hard31()
        hard["vacancy_temporal_validity_verified"] = None
        receipt = self.evaluate31(hard)
        self.assertEqual(receipt["decision"], "LIMBO")
        self.assertIn("HARD_UNKNOWN:vacancy_temporal_validity_verified", receipt["blockers"])

    def test_requirement_extraction_and_application_route_are_hard_gates(self):
        for gate in ("mandatory_requirements_extracted", "application_route_verified"):
            with self.subTest(gate=gate):
                hard = self.hard31()
                hard[gate] = False
                receipt = self.evaluate31(hard)
                self.assertEqual(receipt["decision"], "REJECT")
                self.assertIn(f"HARD_FAIL:{gate}", receipt["blockers"])

    def test_all_v31_hard_gates_pass_can_reach_ready(self):
        receipt = self.evaluate31()
        self.assertEqual(receipt["schema_version"], SCHEMA_VERSION)
        self.assertTrue(receipt["hard_gates"]["pass"])
        self.assertTrue(receipt["application_ready_no_send"])
        self.assertIn(receipt["decision"], {"APPLICATION_READY_NO_SEND", "ELITE_MATCH"})
        self.assertFalse(receipt["final_send_ready"])
        self.assertEqual(receipt["send_allowed"], 0)

    def test_old_aag30_receipt_is_rejected_by_v31_recruiter_gate(self):
        receipt30 = evaluate_v30(
            dimension_scores=self.dimensions(),
            hard_gate_states=dict(BASE_HARD_GATES),
            risk_scores=self.risk(),
            evidence_confidence_score=99,
            human_resonance_score=94,
            desperation_score=4,
            questionnaire_answers=self.questions(),
            stakeholder_votes=self.stakeholders(),
        )
        seed = build_vacancy_first_seed(
            {"name": "Hotel Test", "city": "Davos"},
            [{"title": "Housekeeping Attendant"}],
            "https://hotel.example/jobs",
        )
        truth = {
            "role_relevant_evidence": ["proof"],
            "languages": "verified",
            "availability": "verified",
            "permanent_relocation": "verified",
            "swiss_work_eligibility": "verified",
            "contact_identity": "verified",
            "application_adversarial_gate": receipt30,
        }
        gate = recruiter_10_second_gate(seed, truth)
        self.assertFalse(gate["pass"])
        self.assertIn("AAG31_SCHEMA_MISMATCH", gate["failures"])

    def test_private_packet_requires_v31_receipt_and_remains_no_send(self):
        receipt31 = self.evaluate31()
        seed = {
            "record_id": "MD-test",
            "hotel_name": "Hotel Test",
            "city": "Davos",
            "target_role": "Housekeeping Attendant",
            "vacancy_source_url": "https://hotel.example/jobs/housekeeping",
            "careers_routes": ["https://hotel.example/jobs"],
            "signal_quality": {"semantic": {"valid": True}, "temporal": {"current": True}},
            "owner_scope_state": "UNIQUE_SOURCE_RECORD_CANDIDATE_REQUIRES_PRIVATE_RECHECK",
            "owner_scope_verification_required_before_aag_ready": True,
            "application_ready_no_send": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
        truth = {
            "private_truth_ref": "PRIVATE-CANON",
            "languages": "verified",
            "availability": "verified",
            "permanent_relocation": "verified",
            "swiss_work_eligibility": "verified",
            "contact_identity": "verified",
            "application_adversarial_gate": receipt31,
        }
        packet = compile_private_packet(
            seed,
            candidate_truth=truth,
            role_relevant_evidence=[{"claim": "verified"}],
            approved_asset_refs={"links": [], "links_verified": True, "headshot_approved": False},
        )
        self.assertTrue(packet["application_ready_no_send"])
        self.assertFalse(packet["final_send_ready"])
        self.assertEqual(packet["send_allowed"], 0)
        self.assertEqual(packet["application_adversarial_gate_required"], SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
