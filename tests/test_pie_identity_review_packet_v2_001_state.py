import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'docs/state/PIE_IDENTITY_REVIEW_PACKET_V2_001_33206402141.json'
EXPECTED_KEYS=['MD-0bc05b76e74e4bf37b9d','MD-1c67bec9e4e6883dcc51','MD-2883d04e3588f7215630','MD-4a9768f6c335edab67ca','MD-4d727160a4b32b3096cd']
EXPECTED_PROVIDER_HASHES=['57cb6cff8069ed7bd93a65261d10250b2b7f37dd9c2fd7b564e5d6e6c441e459','72a185a751eeadf5d6834bb58c999033656f3780f2108f1c05ddf4968180c9db','42bd1ae7837f81a89d7e7a38d11a21121e3148ab378bd3d9026f21c18b515f93','0295c0523d4158716b85a7c2fbba1e3592c6614a4a95c886af10d175beb008a4','965db2b082d40144ee866daf415566d6962815cac7e2301211c53755a57f851c']
class TestMigratedPIEReviewPacket(unittest.TestCase):
    def setUp(self): self.p=json.loads(PACKET.read_text(encoding='utf-8'))
    def test_lineage_and_selection(self):
        self.assertEqual(self.p['schema_version'],'PIE-IDENTITY-REVIEW-PACKET-V2-1.0')
        self.assertEqual(self.p['source_queue_sha256'],'eed5f949c55da71b7a69d3dd481778992f316bfdd35e4655f85070dc46a14429')
        self.assertEqual(self.p['provider_evidence_packet_sha256'],'17dcdee8cb5f1dec528b4f0da2880d3faa12b10c08f791d6092a215e412ffd30')
        self.assertEqual([i['source_record_key'] for i in self.p['items']],EXPECTED_KEYS)
        self.assertEqual([i['provider_response_sha256'] for i in self.p['items']],EXPECTED_PROVIDER_HASHES)
        self.assertEqual(self.p['items_count'],5)
    def test_fail_closed_review_semantics(self):
        for item in self.p['items']:
            self.assertEqual(item['review_state'],'CANONICAL_COMPARATOR_REQUIRED')
            self.assertIsNone(item['terminal_decision'])
            self.assertEqual(item['max_token_jaccard_ppm'],500000)
            self.assertTrue(item['candidate_hotel_ids'])
        self.assertEqual(self.p['domain_outcome'],'REVIEW_PACKET_MATERIALIZED_COMPARATOR_PENDING')
        self.assertEqual(self.p['mapping_effect'],{'terminal_mappings_delta':0,'reconcile_required_delta':0,'effective_reconcile_required':1404})
    def test_safety_lock(self):
        h=self.p['hard_invariants']
        self.assertIs(h['authority_advanced'],False)
        self.assertEqual(h['h_id_allocations'],0)
        self.assertEqual(h['canonical_id_reservations'],0)
        self.assertIs(h['crm_universe_complete'],False)
        self.assertEqual(h['outbound'],'CLOSED')
        self.assertEqual(h['send_allowed'],0)
        self.assertEqual(h['terminal_identity_decisions'],0)
if __name__=='__main__': unittest.main()
