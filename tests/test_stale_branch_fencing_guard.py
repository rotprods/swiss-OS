import unittest

from scripts.stale_branch_fencing_guard import evaluate


class StaleBranchFencingGuardTests(unittest.TestCase):
    def test_new_token_must_exceed_canonical_watermark(self):
        canonical = {"fencing_high_watermark": 14, "claims": []}
        ok, receipt = evaluate(canonical, [{"claim_id": "C15", "state": "ACTIVE", "fencing_token": 15}])
        self.assertTrue(ok)
        self.assertEqual(receipt["violations"], [])

    def test_historical_stale_token12_attempt_fails_closed(self):
        canonical = {"fencing_high_watermark": 14, "claims": []}
        ok, receipt = evaluate(canonical, [{"claim_id": "STALE-SEMANTIC-GRAPHIFY-012", "state": "ACTIVE", "fencing_token": 12}])
        self.assertFalse(ok)
        self.assertIn(
            "STALE_BRANCH_FENCING_TOKEN:STALE-SEMANTIC-GRAPHIFY-012:12<=CANONICAL_WATERMARK:14",
            receipt["violations"],
        )

    def test_same_canonical_active_claim_may_continue(self):
        canonical_claim = {"claim_id": "C14", "state": "ACTIVE", "fencing_token": 14}
        canonical = {"fencing_high_watermark": 14, "claims": [canonical_claim]}
        ok, receipt = evaluate(canonical, [dict(canonical_claim)])
        self.assertTrue(ok)
        self.assertTrue(receipt["evaluated_active_claims"][0]["canonical_continuation"])

    def test_same_claim_with_different_token_fails(self):
        canonical = {"fencing_high_watermark": 14, "claims": [{"claim_id": "C14", "state": "ACTIVE", "fencing_token": 14}]}
        ok, receipt = evaluate(canonical, [{"claim_id": "C14", "state": "ACTIVE", "fencing_token": 15}])
        self.assertFalse(ok)
        self.assertIn("CANONICAL_CLAIM_TOKEN_MISMATCH:C14:14!=15", receipt["violations"])

    def test_duplicate_active_token_fails(self):
        canonical = {"fencing_high_watermark": 14, "claims": []}
        working = [
            {"claim_id": "C15A", "state": "ACTIVE", "fencing_token": 15},
            {"claim_id": "C15B", "state": "ACTIVE", "fencing_token": 15},
        ]
        ok, receipt = evaluate(canonical, working)
        self.assertFalse(ok)
        self.assertTrue(any(v.startswith("DUPLICATE_ACTIVE_FENCING_TOKEN:15") for v in receipt["violations"]))


if __name__ == "__main__":
    unittest.main()
