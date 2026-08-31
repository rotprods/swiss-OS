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
from swiss_os.application_learning import (
    ApplicationLearningError,
    EvidenceClass,
    FeedbackEvent,
    Lane,
    Outcome,
    build_vacancy_first_seed,
    classify_lane,
    feedback_effect,
    recruiter_10_second_gate,
    render_static_profile_card,
    validate_email_html,
    validate_motivation_text,
)
from swiss_os.application_wave import compile_private_packet, compile_top_exact_vacancy_seeds


class ApplicationLearningV2Tests(unittest.TestCase):
    def ready_aag(self):
        return evaluate_application(
            dimension_scores={key: 95 for key in DIMENSION_WEIGHTS},
            hard_gate_states=dict(HARD_GATE_EXPECTED),
            risk_scores={key: 10 for key in RISK_COMPONENTS},
            evidence_confidence_score=98,
            human_resonance_score=92,
            desperation_score=5,
            questionnaire_answers={question.question_id: AuditState.PASS.value for question in QUESTION_BANK},
            stakeholder_votes={stakeholder: True for stakeholder in STAKEHOLDERS},
        )

    def test_lane_selection_is_role_first(self):
        self.assertEqual(classify_lane("Zimmermädchen / Roomboy"), Lane.HOUSEKEEPING)
        self.assertEqual(classify_lane("Kitchen Helper"), Lane.KITCHEN_SUPPORT)
        self.assertEqual(classify_lane("Chef de Rang"), Lane.SERVICE_FNB)
        self.assertEqual(classify_lane("Front Office Agent"), Lane.GUEST_SUPPORT)
        self.assertEqual(classify_lane("Content & Social Media Manager"), Lane.HYBRID_DIGITAL)

    def test_generic_rejection_and_no_reply_do_not_invent_causes(self):
        for outcome in (Outcome.REJECTION_GENERIC, Outcome.NO_REPLY):
            effect = feedback_effect(FeedbackEvent(outcome, EvidenceClass.EXPLICIT_EMPLOYER_REASON))
            self.assertFalse(effect["causal_inference_allowed"])
            self.assertFalse(effect["infer_language_failure"])
            self.assertFalse(effect["infer_education_failure"])
            self.assertFalse(effect["infer_work_authorization_failure"])
            self.assertFalse(effect["infer_experience_failure"])

    def test_filled_suppresses_exact_vacancy_not_hotel(self):
        effect = feedback_effect(FeedbackEvent(Outcome.REJECTION_FILLED, EvidenceClass.EXPLICIT_EMPLOYER_REASON, vacancy_key="V1", hotel_key="H1"))
        self.assertTrue(effect["suppress_exact_vacancy"])
        self.assertFalse(effect["suppress_hotel"])

    def test_no_matching_vacancy_penalizes_spontaneous_retry(self):
        effect = feedback_effect(FeedbackEvent(Outcome.REJECTION_NO_MATCHING_VACANCY, EvidenceClass.EXPLICIT_EMPLOYER_REASON))
        self.assertTrue(effect["penalize_spontaneous_retry"])
        self.assertFalse(effect["suppress_hotel"])

    def test_primary_application_requires_exact_current_vacancy(self):
        hotel = {"name": "Hotel Test", "city": "Davos"}
        exact = build_vacancy_first_seed(hotel, [{"title": "Housekeeping Attendant"}], "https://hotel.example/careers")
        fallback = build_vacancy_first_seed(hotel, [], "https://hotel.example/careers")
        no_route = build_vacancy_first_seed(hotel, [], None)
        self.assertEqual(exact["application_mode"], "PRIMARY_EXACT_VACANCY")
        self.assertEqual(fallback["application_mode"], "SPONTANEOUS_FALLBACK_RESEARCH_ONLY")
        self.assertEqual(no_route["application_mode"], "RESEARCH_ONLY_NO_APPLICATION_ROUTE")
        self.assertTrue(exact["application_adversarial_gate"]["required"])
        self.assertFalse(exact["application_adversarial_gate"]["hard_fail_compensation_allowed"])
        self.assertFalse(exact["final_send_ready"])
        self.assertEqual(exact["send_allowed"], 0)

    def test_portfolio_is_secondary_for_operations(self):
        ops = build_vacancy_first_seed({"name": "A", "city": "B"}, [{"title": "Housekeeping Attendant"}], None)
        digital = build_vacancy_first_seed({"name": "A", "city": "B"}, [{"title": "Digital Marketing Manager"}], None)
        self.assertFalse(ops["asset_policy"]["portfolio_default_attachment"])
        self.assertTrue(digital["asset_policy"]["portfolio_default_attachment"])
        self.assertFalse(ops["asset_policy"]["founder_ceo_primary_signal_for_operations"])

    def test_recruiter_gate_blocks_unverified_founder_photo_links_and_missing_aag(self):
        seed = build_vacancy_first_seed({"name": "A", "city": "B"}, [{"title": "Housekeeping Attendant"}], None)
        truth = {
            "role_relevant_evidence": ["evidence"],
            "languages": "verified",
            "availability": "verified",
            "permanent_relocation": "verified",
            "swiss_work_eligibility": "verified",
            "contact_identity": "verified",
            "founder_ceo_claim": "CEO",
            "founder_ceo_evidence_verified": False,
            "headshot_url": "https://example.com/me.jpg",
            "headshot_approved": False,
            "links": [{"url": "https://example.com"}],
            "links_verified": False,
        }
        gate = recruiter_10_second_gate(seed, truth)
        self.assertFalse(gate["pass"])
        self.assertIn("FOUNDER_CEO_CLAIM_UNVERIFIED", gate["failures"])
        self.assertIn("HEADSHOT_UNVERIFIED", gate["failures"])
        self.assertIn("LINKS_UNVERIFIED", gate["failures"])
        self.assertIn("AAG_REQUIRED", gate["failures"])
        self.assertFalse(gate["final_send_ready"])

    def test_motivation_rejects_grievance_and_fake_flattery(self):
        validate_motivation_text("I want to build a long-term future in Switzerland and contribute to the team.")
        for text in ("I am escaping from Spain because the system is oppressive.", "Switzerland is the best country in the world."):
            with self.assertRaises(ApplicationLearningError):
                validate_motivation_text(text)

    def test_static_email_is_active_content_free_and_has_plain_fallback(self):
        html_text, plain = render_static_profile_card(
            display_name="Candidate",
            role="Housekeeping Attendant",
            motivation="I want to build a long-term future in Switzerland and contribute to the team.",
            verified_links=[{"label": "Portfolio", "url": "https://example.com/portfolio", "verified": "true"}],
        )
        validate_email_html(html_text, plain)
        self.assertNotIn("<script", html_text.lower())
        self.assertNotIn("<iframe", html_text.lower())
        self.assertNotIn("<form", html_text.lower())
        self.assertTrue(plain.strip())

    def test_creative_pilot_is_scope_guarded(self):
        seed = build_vacancy_first_seed({"name": "A", "city": "B"}, [{"title": "Kitchen Helper"}], None)
        policy = seed["creative_value_policy"]
        self.assertTrue(policy["employer_approval_required"])
        self.assertTrue(policy["lawful_agreed_scope_or_working_time_required"])
        self.assertFalse(policy["unconditional_free_off_clock_labor_allowed"])

    def test_top25_compiler_only_selects_exact_structured_vacancies(self):
        def record(rid, jobs, careers=True):
            return {
                "record_id": rid,
                "name": rid,
                "city": "Davos",
                "observed_at": "2026-08-31T12:00:00Z",
                "e07_vacancy": {"state": "X", "structured_openings": jobs, "opening_routes": [], "careers_routes": [f"https://{rid}.example/careers"] if careers else [], "explicit_no_openings_proof": False},
                "e08_housing": {"state": "STAFF_HOUSING_RESEARCH_PENDING"},
                "e15_score": {"market_readiness_score": 50},
                "safety": {"authority_advanced": False, "canonical_id_allocations": 0, "canonical_id_reservations": 0, "outbound": "CLOSED", "send_allowed": 0, "irreversible_external_actions": 0},
            }
        aggregate = {"source_snapshot_id": "S", "observed_at": "T", "records": [record("a", [{"title": "Chef de Rang"}]), record("b", []), record("c", [{"title": "Housekeeping Attendant"}])], "safety": {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0, "irreversible_external_actions": 0}}
        result = compile_top_exact_vacancy_seeds(aggregate, limit=25)
        self.assertEqual(result["selected_count"], 2)
        self.assertEqual({item["record_id"] for item in result["selected"]}, {"a", "c"})
        self.assertFalse(result["final_send_ready"])
        self.assertEqual(result["send_allowed"], 0)

    def test_private_packet_requires_role_evidence_verified_assets_and_aag(self):
        seed = {
            "record_id": "x",
            "hotel_name": "Hotel",
            "city": "Davos",
            "observed_at": "T",
            "strategy": build_vacancy_first_seed({"name": "Hotel", "city": "Davos"}, [{"title": "Housekeeping Attendant"}], None),
        }
        candidate_truth = {
            "private_truth_ref": "PRIVATE",
            "languages": "verified",
            "availability": "absolute + role recheck",
            "permanent_relocation": "verified",
            "swiss_work_eligibility": "verified",
            "contact_identity": "verified",
        }
        packet = compile_private_packet(seed, candidate_truth=candidate_truth, role_relevant_evidence=[], approved_asset_refs={"links": [], "links_verified": True, "headshot_approved": False})
        self.assertFalse(packet["application_ready_no_send"])
        self.assertIn("CANDIDATE_TRUTH_INCOMPLETE", packet["recruiter_gate"]["failures"])
        self.assertIn("AAG_REQUIRED", packet["recruiter_gate"]["failures"])

        candidate_truth["application_adversarial_gate"] = self.ready_aag()
        packet2 = compile_private_packet(seed, candidate_truth=candidate_truth, role_relevant_evidence=[{"claim": "verified role evidence"}], approved_asset_refs={"links": [], "links_verified": True, "headshot_approved": False})
        self.assertTrue(packet2["application_ready_no_send"])
        self.assertTrue(packet2["recruiter_gate"]["aag_pass"])
        self.assertFalse(packet2["final_send_ready"])
        self.assertEqual(packet2["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
