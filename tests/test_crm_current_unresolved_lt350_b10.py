import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B10_2026-09-10.json'; SCAN=ROOT/'docs/state/LOCALITY_NORMALIZATION_SCAN_LT350_REMAINING_2026-09-10.json'; EVIDENCE=ROOT/'docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B10_EVIDENCE_PACKET_2026-09-10.json'; NEXT=ROOT/'docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B10.json'
EXPECTED=['MD-315c01eaa157e5b3602f','MD-323db50ea273aa998ca6','MD-339cb8d3f38f76b192dd','MD-34f61a1d95ba700cfe94','MD-350bcd0642995b5b2d89','MD-35ea8c63b3b3459e39b7','MD-36743f6ab6fb963fb3a3','MD-36c39d2fd2a2f49a5855','MD-36de2d991c8ba24a7a94','MD-377dc48ee075aa309eab']
def load(p): return json.loads(p.read_text(encoding='utf-8'))
class B10Tests(unittest.TestCase):
    def test_lane_reconstruction(self):
        r=load(SCAN)['lane_reconstruction']; self.assertEqual((r['candidate_records'],r['raw_zero_exact_city_records'],r['exact_global_name_locality_conflicts_excluded'],r['operational_zero_city_lane']),(1438,488,3,485)); self.assertEqual(r['completed_b01_b09'],90); self.assertEqual(r['remaining_after_b09'],395)
    def test_selection_and_evidence(self):
        d,e=load(STATE),load(EVIDENCE); self.assertEqual(d['selection']['selected_source_record_keys'],EXPECTED); self.assertEqual(e['selection']['selected_source_record_keys'],EXPECTED); self.assertEqual(len(e['records']),10); self.assertTrue(all(x['current_evidence'] for x in e['records']))
    def test_frontier_and_safety(self):
        d=load(STATE); f=d['frontier']; self.assertEqual(f['current_lt350000_reviewed_cumulative'],100); self.assertEqual(f['zero_same_city_lane_remaining'],385); self.assertEqual(f['cumulative_new_canonical_preauth'],208); self.assertEqual((f['terminal_source_mappings'],f['reconcile_required']),(658,1403)); self.assertEqual(f['h_id_allocations'],0); self.assertEqual(f['canonical_id_reservations'],0); self.assertFalse(d['qa']['authority_advanced']); self.assertEqual(d['qa']['outbound'],'CLOSED'); self.assertEqual(d['qa']['send_allowed'],0)
    def test_egr_preserved(self):
        d={x['source_record_key']:x for x in load(STATE)['decisions']}; v=d['MD-36c39d2fd2a2f49a5855']; self.assertEqual(v['decision'],'NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED'); self.assertTrue(v['entity_granularity']['conventional_hotel_coercion_forbidden'])
    def test_next_is_exact_and_conflict_excluded(self):
        d,n=load(STATE),load(NEXT); self.assertEqual(d['next']['selected_source_record_keys'],n['selected_source_record_keys']); self.assertEqual(len(n['selected_source_record_keys']),10); self.assertNotIn('MD-37df0d95a87f101c1916',n['selected_source_record_keys'])
if __name__=='__main__': unittest.main()
