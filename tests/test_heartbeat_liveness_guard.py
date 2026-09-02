import unittest
from datetime import datetime, timezone

from scripts.heartbeat_liveness_guard import evaluate


NOW = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)


class HeartbeatLivenessGuardTests(unittest.TestCase):
    def test_live_active_heartbeat_passes(self):
        claims = [{"claim_id": "C15", "session_id": "S15", "state": "ACTIVE"}]
        heartbeats = [{"heartbeat_id": "HB15", "session_id": "S15", "state": "ACTIVE", "observed_at": "2026-09-02T11:45:00Z"}]
        ok, receipt = evaluate(claims, heartbeats, NOW, 1800)
        self.assertTrue(ok)
        self.assertEqual(receipt["sessions"][0]["status"], "LIVE")

    def test_expired_heartbeat_fails_without_commits(self):
        claims = [{"claim_id": "C15", "session_id": "S15", "state": "ACTIVE"}]
        heartbeats = [{"heartbeat_id": "HB15", "session_id": "S15", "state": "ACTIVE", "observed_at": "2026-09-02T11:00:00Z"}]
        ok, receipt = evaluate(claims, heartbeats, NOW, 1800)
        self.assertFalse(ok)
        self.assertTrue(any(v.startswith("STALE_HEARTBEAT:C15:S15") for v in receipt["violations"]))

    def test_missing_heartbeat_fails_closed(self):
        claims = [{"claim_id": "C15", "session_id": "S15", "state": "BLOCKED"}]
        ok, receipt = evaluate(claims, [], NOW, 1800)
        self.assertFalse(ok)
        self.assertIn("MISSING_HEARTBEAT:C15:S15", receipt["violations"])

    def test_terminal_heartbeat_while_claim_active_fails(self):
        claims = [{"claim_id": "C15", "session_id": "S15", "state": "ACTIVE"}]
        heartbeats = [{"heartbeat_id": "HB15", "session_id": "S15", "state": "COMPLETE", "observed_at": "2026-09-02T11:59:00Z"}]
        ok, receipt = evaluate(claims, heartbeats, NOW, 1800)
        self.assertFalse(ok)
        self.assertIn("ACTIVE_CLAIM_TERMINAL_HEARTBEAT:C15:COMPLETE", receipt["violations"])

    def test_released_claim_is_not_liveness_work(self):
        claims = [{"claim_id": "C14", "session_id": "S14", "state": "RELEASED"}]
        ok, receipt = evaluate(claims, [], NOW, 1800)
        self.assertTrue(ok)
        self.assertEqual(receipt["active_session_count"], 0)


if __name__ == "__main__":
    unittest.main()
