import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs/state/CRM_CURRENT_UNRESOLVED_LT350_B11_2026-09-10.json"
NEXT = ROOT / "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B11.json"
EVIDENCE = ROOT / "docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B11_EVIDENCE_PACKET_2026-09-10.json"

EXPECTED_B11 = [
    "MD-37c920c06fa392c578aa","MD-39077c13b83ef6775c58","MD-39f0f1ccfbfb59438afc","MD-39fdd00ab3bb208620ff","MD-3a55671a2c16fbf26f50",
    "MD-3adb4257b579fae1525e","MD-3b41390ad96ab8bbf7ce","MD-3be208b823a531c6bcc1","MD-3c473d1649021c1b6b5b","MD-3d333fe34a8cbe815fa1",
]
EXPECTED_B12 = [
    "MD-3dbc8580e89d992f445d","MD-3e3e7fdc097318b15740","MD-3f96ba3e09575493c4de","MD-3fd0814738e50d59e367","MD-4005f3401ff4ff6b31fe",
    "MD-401819d323db4d0c6ad4","MD-403bc80bd88a20683e31","MD-411ab7bce89c40f7c0d8","MD-4153a2d77c05dbf5809c","MD-416e5b4ac65974bbdb1d",
]

class B11FrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = json.loads(STATE.read_text())
        cls.next = json.loads(NEXT.read_text())
        cls.evidence = json.loads(EVIDENCE.read_text())

    def test_exact_b11_and_b12_keys(self):
        self.assertEqual(self.state["selection"]["selected_source_record_keys"], EXPECTED_B11)
        self.assertEqual(self.next["selected_source_record_keys"], EXPECTED_B12)
        self.assertEqual(len(set(EXPECTED_B11 + EXPECTED_B12)), 20)

    def test_b11_is_evidence_complete_and_preauth_only(self):
        self.assertEqual(self.evidence["qa"]["records"], 10)
        self.assertEqual(self.evidence["qa"]["current_evidence_captured"], 10)
        self.assertEqual(self.evidence["qa"]["locality_variant_findings"], 0)
        self.assertFalse(self.evidence["qa"]["fuzzy_autobind"])
        self.assertEqual(self.state["frontier"]["batch_reviewed"], 10)
        self.assertEqual(self.state["frontier"]["batch_new_canonical_preauth"], 6)
        self.assertEqual(self.state["frontier"]["batch_new_accommodation_preauth_egr_required"], 4)
        self.assertEqual(self.state["frontier"]["batch_terminal_mapping_delta"], 0)

    def test_authority_and_outbound_are_unchanged(self):
        self.assertEqual(self.state["authority"]["canonical_rows"], 690)
        self.assertEqual(self.state["authority"]["next_physical_id"], "H-0691_UNALLOCATED")
        self.assertEqual(self.state["frontier"]["h_id_allocations"], 0)
        self.assertEqual(self.state["frontier"]["canonical_id_reservations"], 0)
        self.assertFalse(self.state["qa"]["authority_advanced"])
        self.assertEqual(self.state["qa"]["outbound"], "CLOSED")
        self.assertEqual(self.state["qa"]["send_allowed"], 0)

    def test_egr_and_temporal_risk_are_not_erased(self):
        decisions = {d["source_record_key"]: d for d in self.state["decisions"]}
        self.assertEqual(decisions["MD-37c920c06fa392c578aa"]["temporal_risks"][0]["type"], "ANNOUNCED_CLOSURE_END_2026")
        for key in ("MD-3b41390ad96ab8bbf7ce","MD-3be208b823a531c6bcc1","MD-3c473d1649021c1b6b5b","MD-3d333fe34a8cbe815fa1"):
            self.assertEqual(decisions[key]["decision"], "NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED")
            self.assertTrue(decisions[key]["entity_granularity"]["conventional_hotel_coercion_forbidden"])

if __name__ == "__main__":
    unittest.main()
