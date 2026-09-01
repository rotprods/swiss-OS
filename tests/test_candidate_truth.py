import unittest

from swiss_os.candidate_truth import CandidateField, claim_is_renderable, evaluate_lane, public_safe_summary


def verified(key: str, *, private: bool = False) -> CandidateField:
    return CandidateField(key=key, truth_state="VERIFIED", approved=True, external_allowed=True, private_reference=private)


class CandidateTruthTests(unittest.TestCase):
    def test_entry_ready_without_creative_assets(self):
        fields = [
            verified("contact.email"),
            verified("contact.phone", private=True),
            verified("language.wording"),
            verified("availability.start"),
            verified("asset.cv"),
        ]
        result = evaluate_lane("ENTRY", fields)
        self.assertTrue(result.ready)
        self.assertEqual(result.missing, ())

    def test_entry_blocks_only_missing_cv_when_core_facts_are_ready(self):
        fields = [
            verified("contact.email"),
            verified("contact.phone", private=True),
            verified("language.wording"),
            verified("availability.start"),
        ]
        result = evaluate_lane("ENTRY", fields)
        self.assertFalse(result.ready)
        self.assertEqual(result.missing, ("asset.cv",))

    def test_hybrid_requires_linkedin_portfolio_and_case_studies(self):
        fields = [
            verified("contact.email"), verified("contact.phone"),
            verified("language.wording"), verified("availability.start"), verified("asset.cv")
        ]
        result = evaluate_lane("HYBRID", fields)
        self.assertFalse(result.ready)
        self.assertEqual(set(result.missing), {"social.linkedin", "asset.portfolio", "asset.case_studies"})

    def test_unverified_external_claim_is_rejected(self):
        field = CandidateField("experience.metric", "UNKNOWN", True, True)
        with self.assertRaises(ValueError):
            claim_is_renderable(field)

    def test_unapproved_claim_is_not_renderable(self):
        field = CandidateField("experience.founder", "VERIFIED", False, False)
        self.assertFalse(claim_is_renderable(field))

    def test_private_reference_counts_without_exposing_value(self):
        fields = [verified("contact.phone", private=True), verified("contact.email")]
        summary = public_safe_summary(fields)
        self.assertEqual(summary["private_reference_count"], 1)
        self.assertNotIn("value", summary)


if __name__ == "__main__":
    unittest.main()
