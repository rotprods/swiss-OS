import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B08 = ROOT / 'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B08_2026-09-10.json'
B09 = ROOT / 'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B09_2026-09-10.json'

B08_KEYS = ['MD-26e7c28b41181b3f61d3','MD-27224563cb53290593d0','MD-27a401c5e00f91073a6c','MD-27cb7654c25138f8566a','MD-281e7be2c117561bb57e','MD-284d08ed79e92ca9633a','MD-2855ae3538687dc08390','MD-29ca94166046fcd921f5','MD-2b51224ee38c42763d77','MD-2c5ff2038682379edd93']
B09_KEYS = ['MD-2c965eba36d2e32e14b6','MD-2e8edf3b3a5b6d30c48d','MD-2e94b51deff4b930852b','MD-2fddbfbe76a514a94bfe','MD-30049898b6933d37f8ed','MD-30b31ab8d1f66bab5fcf','MD-30fa87b1899965855d0c','MD-310fdead9d1b018a63fd','MD-31202790b99ef13dd806','MD-3146a6879d30c3ba40de']


def load(p): return json.loads(p.read_text(encoding='utf-8'))


def assert_safety(data):
    assert data['claim_id'] == 'CLAIM-CRM-ENTITY-RESOLUTION-016'
    assert data['fencing_token'] == 16
    assert data['authority']['canonical_rows'] == 690
    assert data['authority']['next_physical_id'] == 'H-0691_UNALLOCATED'
    assert data['authority']['effect'] == 'NONE'
    assert all(d['mapping_state'] == 'RECONCILE_REQUIRED' for d in data['decisions'])
    assert all(d['canonical_h_id_reserved'] is False for d in data['decisions'])
    assert all(d['h_id_allocated'] is False for d in data['decisions'])
    assert all(d['terminal_mapping_created'] is False for d in data['decisions'])
    assert data['qa']['authority_advanced'] is False
    assert data['qa']['crm_universe_complete'] is False
    assert data['qa']['outbound'] == 'CLOSED'
    assert data['qa']['send_allowed'] == 0


def test_b08_recovery_selection_and_safety():
    d = load(B08)
    assert d['wave_id'] == 'CURR-U1403-B08'
    assert d['selection']['selected_source_record_keys'] == B08_KEYS
    assert len(set(B08_KEYS)) == 10
    assert d['qa']['selection_reproduces_prior_70_exact_keys'] is True
    assert d['frontier']['current_lt350000_reviewed_cumulative'] == 80
    assert d['frontier']['cumulative_new_canonical_preauth'] == 192
    assert d['frontier']['zero_same_city_lane_remaining'] == 405
    assert sum(x['decision']=='NEW_CANONICAL_PREAUTH' for x in d['decisions']) == 9
    assert sum(x['decision']=='NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED' for x in d['decisions']) == 1
    assert_safety(d)


def test_b09_detects_locality_variant_false_negative():
    d = load(B09)
    assert d['wave_id'] == 'CURR-U1403-B09'
    assert d['selection']['selected_source_record_keys'] == B09_KEYS
    assert len(set(B09_KEYS)) == 10
    assert d['qa']['selection_reproduces_prior_80_exact_keys'] is True
    assert d['frontier']['current_lt350000_reviewed_cumulative'] == 90
    assert d['frontier']['cumulative_new_canonical_preauth'] == 199
    assert d['frontier']['zero_same_city_lane_remaining'] == 395
    by_key = {x['source_record_key']:x for x in d['decisions']}
    w = by_key['MD-30b31ab8d1f66bab5fcf']
    assert w['decision'] == 'MATCH_EXISTING_PREAUTH'
    assert w['candidate_hotel_id'] == 'H-0681'
    assert w['locality_variant_review']['same_property_supported'] is True
    assert sum(x['decision']=='NEW_CANONICAL_PREAUTH' for x in d['decisions']) == 7
    assert sum(x['decision']=='NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED' for x in d['decisions']) == 2
    assert_safety(d)


def test_b09_egr_cases_are_not_coerced_to_hotels():
    d = load(B09)
    by_key = {x['source_record_key']:x for x in d['decisions']}
    assert by_key['MD-2fddbfbe76a514a94bfe']['entity_granularity']['conventional_hotel_coercion_forbidden'] is True
    assert by_key['MD-310fdead9d1b018a63fd']['entity_granularity']['conventional_hotel_coercion_forbidden'] is True
