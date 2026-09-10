from swiss_os.locality_normalization_guard import locality_keys, locality_variant_review, rebuild_zero_city_lane


def test_parenthetical_locality_variant_is_review_only():
    source=[{"record_id":"MD-1","name":"Seehotel Wilerbad","city":"Wilen (Sarnen)"}]
    canonical=[{"hotel_id":"H-0681","canonical_name":"Seehotel Wilerbad Seminar & Spa","city":"Wilen"}]
    out=locality_variant_review(source,canonical)
    assert len(out)==1
    assert out[0]["canonical_candidates"][0]["hotel_id"]=="H-0681"
    assert out[0]["auto_bind_allowed"] is False
    assert out[0]["authority_action"]=="NONE"


def test_canton_numeric_airport_and_punctuation_normalize_for_review():
    assert "brienz" in locality_keys("Brienz BE")
    assert "davos dorf" in locality_keys("Davos-Dorf")
    assert "geneve" in locality_keys("Genève 15 Aéroport")
    assert "wilen" in locality_keys("Wilen (Sarnen)")


def test_exact_global_name_conflict_is_excluded_from_zero_city_lane():
    source=[
        {"record_id":"MD-1","name":"Hotel Du Lac","city":"Därligen"},
        {"record_id":"MD-2","name":"Novel House","city":"Nowhere"},
    ]
    canonical=[{"hotel_id":"H-1","canonical_name":"Hotel Du Lac","city":"Interlaken"}]
    out=rebuild_zero_city_lane(source,canonical)
    assert out["candidate_records"]==2
    assert out["raw_zero_city_records"]==2
    assert out["exact_global_name_conflicts"]==1
    assert out["lane_records"]==1
    assert out["lane"][0]["record_id"]=="MD-2"
    assert out["auto_bind_allowed"] is False


def test_literal_city_match_is_not_emitted_as_locality_variant():
    source=[{"record_id":"MD-1","name":"Youth Hostel","city":"Brienz"}]
    canonical=[{"hotel_id":"H-1","canonical_name":"Other Hotel","city":"Brienz"}]
    assert locality_variant_review(source,canonical)==[]
