import unittest

from swiss_os.locality_normalization_guard import (
    LocalityGuardError,
    locality_keys,
    locality_variant_review,
    rebuild_zero_city_lane,
)


class LocalityNormalizationGuardTests(unittest.TestCase):
    def test_parenthetical_locality_variant_is_review_only(self):
        source=[{"record_id":"MD-1","name":"Seehotel Wilerbad","city":"Wilen (Sarnen)"}]
        canonical=[{"hotel_id":"H-0681","canonical_name":"Seehotel Wilerbad Seminar & Spa","city":"Wilen"}]
        out=locality_variant_review(source,canonical)
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]["canonical_candidates"][0]["hotel_id"],"H-0681")
        self.assertEqual(out[0]["candidate_count"],1)
        self.assertEqual(out[0]["ambiguity"],"SINGLE_LOCALITY_COMPARATOR")
        self.assertIs(out[0]["auto_bind_allowed"],False)
        self.assertEqual(out[0]["authority_action"],"NONE")

    def test_canton_numeric_airport_accent_and_punctuation_normalize_for_review(self):
        self.assertIn("brienz",locality_keys("Brienz BE"))
        self.assertIn("davos dorf",locality_keys("Davos-Dorf"))
        self.assertIn("geneve",locality_keys("Genève 15 Aéroport"))
        self.assertIn("geneve",locality_keys("Geneve"))
        self.assertIn("wilen",locality_keys("Wilen (Sarnen)"))

    def test_exact_global_name_conflict_is_excluded_from_zero_city_lane(self):
        source=[{"record_id":"MD-1","name":"Hotel Du Lac","city":"Därligen"},{"record_id":"MD-2","name":"Novel House","city":"Nowhere"}]
        canonical=[{"hotel_id":"H-1","canonical_name":"Hotel Du Lac","city":"Interlaken"}]
        out=rebuild_zero_city_lane(source,canonical)
        self.assertEqual(out["candidate_records"],2)
        self.assertEqual(out["raw_zero_city_records"],2)
        self.assertEqual(out["exact_global_name_conflicts"],1)
        self.assertEqual(out["lane_records"],1)
        self.assertEqual(out["lane"][0]["record_id"],"MD-2")
        self.assertIs(out["auto_bind_allowed"],False)

    def test_literal_city_match_is_not_emitted_as_locality_variant(self):
        source=[{"record_id":"MD-1","name":"Youth Hostel","city":"Brienz"}]
        canonical=[{"hotel_id":"H-1","canonical_name":"Other Hotel","city":"Brienz"}]
        self.assertEqual(locality_variant_review(source,canonical),[])

    def test_multiple_canonical_locality_candidates_are_explicitly_ambiguous(self):
        source=[{"record_id":"MD-1","name":"Property X","city":"Aesch, BL"}]
        canonical=[{"hotel_id":"H-1","canonical_name":"Hotel One","city":"Aesch BL"},{"hotel_id":"H-2","canonical_name":"Hotel Two","city":"Aesch (BL)"}]
        out=locality_variant_review(source,canonical)
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]["candidate_count"],2)
        self.assertEqual(out[0]["ambiguity"],"MULTIPLE_CANONICAL_LOCALITY_CANDIDATES")
        self.assertEqual({c["hotel_id"] for c in out[0]["canonical_candidates"]},{"H-1","H-2"})
        self.assertIs(out[0]["auto_bind_allowed"],False)

    def test_duplicate_source_record_key_fails_closed(self):
        source=[{"record_id":"MD-1","name":"A","city":"X"},{"record_id":"MD-1","name":"B","city":"Y"}]
        canonical=[{"hotel_id":"H-1","canonical_name":"C","city":"Z"}]
        with self.assertRaisesRegex(LocalityGuardError,"DUPLICATE_SOURCE_RECORD_KEY:MD-1"):
            rebuild_zero_city_lane(source,canonical)

    def test_duplicate_canonical_hotel_id_fails_closed(self):
        source=[{"record_id":"MD-1","name":"A","city":"X"}]
        canonical=[{"hotel_id":"H-1","canonical_name":"C","city":"Z"},{"hotel_id":"H-1","canonical_name":"D","city":"Q"}]
        with self.assertRaisesRegex(LocalityGuardError,"DUPLICATE_CANONICAL_HOTEL_ID:H-1"):
            locality_variant_review(source,canonical)

    def test_missing_source_or_canonical_identity_fails_closed(self):
        with self.assertRaisesRegex(LocalityGuardError,"SOURCE_RECORD_KEY_REQUIRED"):
            rebuild_zero_city_lane([{"name":"A","city":"X"}],[{"hotel_id":"H-1","canonical_name":"B","city":"Y"}])
        with self.assertRaisesRegex(LocalityGuardError,"CANONICAL_HOTEL_ID_REQUIRED"):
            rebuild_zero_city_lane([{"record_id":"MD-1","name":"A","city":"X"}],[{"canonical_name":"B","city":"Y"}])

    def test_locality_review_order_is_deterministic_by_source_record_key(self):
        source=[{"record_id":"MD-2","name":"B","city":"Brienz"},{"record_id":"MD-1","name":"A","city":"Brienz"}]
        canonical=[{"hotel_id":"H-1","canonical_name":"C","city":"Brienz BE"}]
        out=locality_variant_review(source,canonical)
        self.assertEqual([x["source_record_key"] for x in out],["MD-1","MD-2"])


if __name__ == "__main__":
    unittest.main()
