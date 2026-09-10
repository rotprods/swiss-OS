import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B10_2026-09-10.json'
SCAN=ROOT/'docs/state/LOCALITY_NORMALIZATION_SCAN_LT350_REMAINING_2026-09-10.json'
EVIDENCE=ROOT/'docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B10_EVIDENCE_PACKET_2026-09-10.json'
NEXT=ROOT/'docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B10.json'
EXPECTED=[
'MD-315c01eaa157e5b3602f','MD-323db50ea273aa998ca6','MD-339cb8d3f38f76b192dd','MD-34f61a1d95ba700cfe94','MD-350bcd0642995b5b2d89','MD-35ea8c63b3b3459e39b7','MD-36743f6ab6fb963fb3a3','MD-36c39d2fd2a2f49a5855','MD-36de2d991c8ba24a7a94','MD-377dc48ee075aa309eab']
EXPECTED_B11=[
'MD-37c920c06fa392c578aa','MD-39077c13b83ef6775c58','MD-39f0f1ccfbfb59438afc','MD-39fdd00ab3bb208620ff','MD-3a55671a2c16fbf26f50','MD-3adb4257b579fae1525e','MD-3b41390ad96ab8bbf7ce','MD-3be208b823a531c6bcc1','MD-3c473d1649021c1b6b5b','MD-3d333fe34a8cbe815fa1']

def load(p): return json.loads(p.read_text(encoding='utf-8'))

def test_locality_scan_reconstructs_historical_lane_exactly():
    s=load(SCAN); r=s['lane_reconstruction']
    assert r['candidate_records']==1438
    assert r['raw_zero_exact_city_records']==488
    assert r['exact_global_name_locality_conflicts_excluded']==3
    assert r['operational_zero_city_lane']==485
    assert r['completed_b01_b09']==90 and r['remaining_after_b09']==395
    assert s['remaining_locality_variant_review_count']==5
    assert s['qa']['auto_bind'] is False
    assert s['qa']['authority_advanced'] is False
    assert s['qa']['h_id_allocations']==0 and s['qa']['canonical_id_reservations']==0

def test_b10_selection_evidence_and_frontier():
    d=load(STATE); e=load(EVIDENCE)
    assert d['selection']['selected_source_record_keys']==EXPECTED
    assert e['selection']['selected_source_record_keys']==EXPECTED
    assert len(e['records'])==10 and all(r['current_evidence'] for r in e['records'])
    f=d['frontier']
    assert f['current_lt350000_reviewed_cumulative']==100
    assert f['historical_lt350000_unreviewed_tail_remaining']==1189
    assert f['zero_same_city_lane_remaining']==385
    assert f['cumulative_new_canonical_preauth']==208
    assert f['terminal_source_mappings']==658 and f['reconcile_required']==1403
    assert f['h_id_allocations']==0 and f['canonical_id_reservations']==0

def test_b10_preserves_egr_and_never_autobinds():
    d=load(STATE)
    decisions={x['source_record_key']:x for x in d['decisions']}
    vall=decisions['MD-36c39d2fd2a2f49a5855']
    assert vall['decision']=='NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED'
    assert vall['entity_granularity']['conventional_hotel_coercion_forbidden'] is True
    assert all(x['mapping_state']=='RECONCILE_REQUIRED' for x in d['decisions'])
    assert all(x['canonical_h_id_reserved'] is False and x['h_id_allocated'] is False and x['terminal_mapping_created'] is False for x in d['decisions'])
    assert d['qa']['fuzzy_autobind'] is False and d['qa']['authority_advanced'] is False
    assert d['qa']['outbound']=='CLOSED' and d['qa']['send_allowed']==0

def test_standalone_b11_frontier_is_exact_and_skips_locality_conflict():
    nxt=load(NEXT)
    assert nxt['route']=='CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B11'
    assert nxt['selected_source_record_keys']==EXPECTED_B11
    assert len(set(EXPECTED_B11))==10
    assert 'MD-37df0d95a87f101c1916' not in EXPECTED_B11
    assert nxt['safety']['locality_guard_required'] is True
    assert nxt['safety']['authority_advance_allowed'] is False
    assert nxt['safety']['outbound']=='CLOSED' and nxt['safety']['send_allowed']==0
