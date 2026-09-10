import pytest

from swiss_os.locality_normalization_guard import (
    LocalityGuardError,
    locality_keys,
    locality_variant_review,
    rebuild_zero_city_lane,
)


def test_parenthetical_locality_variant_is_review_only():
    source=[{"record_id":"MD-1","name":"Seehotel Wilerbad","city":"Wilen (Sarnen)"}]
    canonical=[{"hotel_id":"H-0681","canonical_name":"Seehotel Wilerbad Seminar & Spa","city":"Wilen"}]
    out=locality_variant_review(source,canonical)
    assert len(out)==1
    assert out[0]["canonical_candidates"][0]["hotel_id"]=="H-0681"
    assert out[0]["candidate_count"]==1
    assert out[0]["ambiguity"]=="SINGLE_LOCALITY_COMPARATOR"
    assert out[0]["auto_bind_allowed"] is False
    assert out[0]["authority_action"]=="NONE"


def test_canton_numeric_airport_accent_and_punctuation_normalize_for_review():
    assert "brienz" in locality_keys("Brienz BE")
    assert "davos dorf" in locality_keys("Davos-Dorf")
    assert "geneve" in locality_keys("Genève 15 Aéroport")
    assert "geneve" in locality_keys("Geneve")
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


def test_multiple_canonical_locality_candidates_are_explicitly_ambiguous():
    source=[{"record_id":"MD-1","name":"Property X","city":"Aesch (BL)"}]
    canonical=[
        {"hotel_id":"H-1","canonical_name":"Hotel One","city":"Aesch BL"},
        {"hotel_id":"H-2","canonical_name":"Hotel Two","city":"Aesch (BL)"},
    ]
    # Exact literal city would suppress review for H-2, so use a presentation variant that
    # normalizes to both canonical localities while remaining literal-distinct.
    source[0]["city"]="Aesch, BL"
    out=locality_variant_review(source,canonical)
    assert len(out)==1
    assert out[0]["candidate_count"]==2
    assert out[0]["ambiguity"]=="MULTIPLE_CANONICAL_LOCALITY_CANDIDATES"
    assert {c["hotel_id"] for c in out[0]["canonical_candidates"]}=={"H-1","H-2"}
    assert out[0]["auto_bind_allowed"] is False


def test_duplicate_source_record_key_fails_closed():
    source=[
        {"record_id":"MD-1","name":"A","city":"X"},
        {"record_id":"MD-1","name":"B","city":"Y"},
    ]
    canonical=[{"hotel_id":"H-1","canonical_name":"C","city":"Z"}]
    with pytest.raises(LocalityGuardError, match="DUPLICATE_SOURCE_RECORD_KEY:MD-1"):
        rebuild_zero_city_lane(source,canonical)


def test_duplicate_canonical_hotel_id_fails_closed():
    source=[{"record_id":"MD-1","name":"A","city":"X"}]
    canonical=[
        {"hotel_id":"H-1","canonical_name":"C","city":"Z"},
        {"hotel_id":"H-1","canonical_name":"D","city":"Q"},
    ]
    with pytest.raises(LocalityGuardError, match="DUPLICATE_CANONICAL_HOTEL_ID:H-1"):
        locality_variant_review(source,canonical)


def test_missing_source_or_canonical_identity_fails_closed():
    with pytest.raises(LocalityGuardError, match="SOURCE_RECORD_KEY_REQUIRED"):
        rebuild_zero_city_lane([{"name":"A","city":"X"}],[{"hotel_id":"H-1","canonical_name":"B","city":"Y"}])
    with pytest.raises(LocalityGuardError, match="CANONICAL_HOTEL_ID_REQUIRED"):
        rebuild_zero_city_lane([{"record_id":"MD-1","name":"A","city":"X"}],[{"canonical_name":"B","city":"Y"}])


def test_locality_review_order_is_deterministic_by_source_record_key():
    source=[
        {"record_id":"MD-2","name":"B","city":"Brienz"},
        {"record_id":"MD-1","name":"A","city":"Brienz"},
    ]
    canonical=[{"hotel_id":"H-1","canonical_name":"C","city":"Brienz BE"}]
    out=locality_variant_review(source,canonical)
    assert [x["source_record_key"] for x in out]==["MD-1","MD-2"]
