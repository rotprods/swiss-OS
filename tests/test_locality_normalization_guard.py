import unittest
from swiss_os.locality_normalization_guard import LocalityGuardError, locality_keys, locality_variant_review, rebuild_zero_city_lane

class LocalityNormalizationGuardTests(unittest.TestCase):
    def test_parenthetical_variant_review_only(self):
        out=locality_variant_review([{"record_id":"MD-1","name":"Seehotel Wilerbad","city":"Wilen (Sarnen)"}],[{"hotel_id":"H-0681","canonical_name":"Seehotel Wilerbad Seminar & Spa","city":"Wilen"}])
        self.assertEqual(out[0]["canonical_candidates"][0]["hotel_id"],"H-0681")
        self.assertIs(out[0]["auto_bind_allowed"],False)
    def test_locality_normalizations(self):
        self.assertIn("brienz",locality_keys("Brienz BE")); self.assertIn("davos dorf",locality_keys("Davos-Dorf")); self.assertIn("geneve",locality_keys("Genève 15 Aéroport")); self.assertIn("wilen",locality_keys("Wilen (Sarnen)"))
    def test_exact_name_cross_locality_is_separate(self):
        out=rebuild_zero_city_lane([{"record_id":"MD-1","name":"Hotel Du Lac","city":"Därligen"},{"record_id":"MD-2","name":"Novel House","city":"Nowhere"}],[{"hotel_id":"H-1","canonical_name":"Hotel Du Lac","city":"Interlaken"}])
        self.assertEqual(out["exact_global_name_conflicts"],1); self.assertEqual(out["lane_records"],1); self.assertEqual(out["lane"][0]["record_id"],"MD-2")
    def test_multiple_locality_candidates_are_ambiguous(self):
        out=locality_variant_review([{"record_id":"MD-1","name":"X","city":"Aesch, BL"}],[{"hotel_id":"H-1","canonical_name":"A","city":"Aesch BL"},{"hotel_id":"H-2","canonical_name":"B","city":"Aesch (BL)"}])
        self.assertEqual(out[0]["candidate_count"],2); self.assertEqual(out[0]["ambiguity"],"MULTIPLE_CANONICAL_LOCALITY_CANDIDATES"); self.assertIs(out[0]["auto_bind_allowed"],False)
    def test_duplicate_source_key_fails_closed(self):
        with self.assertRaisesRegex(LocalityGuardError,"DUPLICATE_SOURCE_RECORD_KEY"):
            rebuild_zero_city_lane([{"record_id":"MD-1","name":"A","city":"X"},{"record_id":"MD-1","name":"B","city":"Y"}],[{"hotel_id":"H-1","canonical_name":"C","city":"Z"}])
    def test_duplicate_canonical_id_fails_closed(self):
        with self.assertRaisesRegex(LocalityGuardError,"DUPLICATE_CANONICAL_HOTEL_ID"):
            locality_variant_review([{"record_id":"MD-1","name":"A","city":"X"}],[{"hotel_id":"H-1","canonical_name":"C","city":"Z"},{"hotel_id":"H-1","canonical_name":"D","city":"Q"}])
    def test_missing_identity_fails_closed(self):
        with self.assertRaisesRegex(LocalityGuardError,"SOURCE_RECORD_KEY_REQUIRED"):
            rebuild_zero_city_lane([{"name":"A","city":"X"}],[{"hotel_id":"H-1","canonical_name":"B","city":"Y"}])
        with self.assertRaisesRegex(LocalityGuardError,"CANONICAL_HOTEL_ID_REQUIRED"):
            rebuild_zero_city_lane([{"record_id":"MD-1","name":"A","city":"X"}],[{"canonical_name":"B","city":"Y"}])
    def test_order_deterministic(self):
        out=locality_variant_review([{"record_id":"MD-2","name":"B","city":"Brienz"},{"record_id":"MD-1","name":"A","city":"Brienz"}],[{"hotel_id":"H-1","canonical_name":"C","city":"Brienz BE"}])
        self.assertEqual([x["source_record_key"] for x in out],["MD-1","MD-2"])

if __name__ == '__main__': unittest.main()
