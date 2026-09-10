import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_DIR = ROOT / "docs/state/v2/claims"
ACTIVE = ROOT / "docs/state/v2/active-claims.json"
STATE = ROOT / "STATE.md"
B10 = ROOT / "docs/state/CRM_CURRENT_UNRESOLVED_LT350_B10_2026-09-10.json"
NEXT = ROOT / "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B10.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class B10CoordinationHandoffTests(unittest.TestCase):
    def test_fencing_high_watermark_never_lags_durable_claims(self):
        active = load(ACTIVE)
        claims = [load(p) for p in CLAIMS_DIR.glob("*.json")]
        max_token = max(int(c.get("fencing_token", 0)) for c in claims)
        self.assertEqual(active["fencing_high_watermark"], max_token)
        self.assertGreaterEqual(max_token, 17)

    def test_released_token17_is_not_active(self):
        claim = load(CLAIMS_DIR / "CLAIM-CRM-ENTITY-RESOLUTION-017.json")
        active = load(ACTIVE)
        self.assertEqual(claim["state"], "RELEASED")
        self.assertNotIn(claim["claim_id"], [c.get("claim_id") for c in active.get("claims", [])])

    def test_state_and_next_agree_on_b11_frontier(self):
        state_text = STATE.read_text(encoding="utf-8")
        b10 = load(B10)
        nxt = load(NEXT)
        self.assertIn("B10", state_text)
        self.assertIn("B11", state_text)
        self.assertEqual(b10["next"]["route"], nxt["route"])
        self.assertEqual(b10["next"]["selected_source_record_keys"], nxt["selected_source_record_keys"])
        self.assertEqual(nxt["preconditions"]["current_lt350_reviewed"], 100)
        self.assertEqual(nxt["preconditions"]["zero_city_lane_remaining"], 385)

    def test_b10_never_advances_authority_or_outbound(self):
        b10 = load(B10)
        self.assertFalse(b10["qa"]["authority_advanced"])
        self.assertEqual(b10["qa"]["h_id_allocations"], 0)
        self.assertEqual(b10["qa"]["canonical_id_reservations"], 0)
        self.assertEqual(b10["qa"]["outbound"], "CLOSED")
        self.assertEqual(b10["qa"]["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
