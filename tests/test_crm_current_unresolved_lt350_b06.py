import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B06_2026-08-31.json'
NEXT=ROOT/'docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B06.json'
KEYS=['MD-19586421c51cd23ffdc4','MD-19705e8792a9dc41db8d','MD-19cf8bbb5909736ab761','MD-1a855e1755243c506c83','MD-1bf5b9fb31fc299a0c86','MD-1cca35242ea804d858d2','MD-1cf6c236e4dcc1381605','MD-1d3317abd4dd8d2032cd','MD-1d7a0e1653c1039424b6','MD-1dd3e23d5d5f7559cf99']
B07=['MD-21cc675b7ddb4fb39c9a','MD-21d80dc6cd95557824af','MD-2371d6a62dfb46d25297','MD-23cc9ed081909afb8a76','MD-23d989d03ab52258efd9','MD-246d25ab845005abc642','MD-2503eb358ae6e9c901a7','MD-262dc840666b01355485','MD-2646d4114c7721222c87','MD-267556b17b23beb697d5']

def load(p): return json.loads(p.read_text(encoding='utf-8'))

def test_b06_lineage_and_safety():
    d=load(STATE)
    assert d['parent_git_sha']=='1bbabe457d8ec561249b2bb52b862096df900d42'
    assert d['selection']['selected_source_record_keys']==KEYS
    assert d['selection']['prior_current_reviewed']==50
    assert d['source']['snapshot_id']=='HS-MEMBER-DE-33339392661' and d['source']['coverage_complete'] is True
    assert len(d['decisions'])==10
    for r in d['decisions']:
        assert r['decision']=='NEW_CANONICAL_PREAUTH' and r['mapping_state']=='RECONCILE_REQUIRED'
        assert r['current_evidence'] and r['canonical_h_id_reserved'] is False and r['h_id_allocated'] is False
        assert r['terminal_mapping_created'] is False and r['authority_effect']=='NONE'
    f=d['frontier']
    assert f['current_lt350000_reviewed_cumulative']==60
    assert f['cumulative_new_canonical_preauth']==174
    assert f['historical_lt350000_unreviewed_tail_remaining']==1229
    assert f['zero_same_city_lane_remaining']==425
    assert f['terminal_source_mappings']==658 and f['reconcile_required']==1403
    assert d['qa']['authority_advanced'] is False and d['qa']['outbound']=='CLOSED' and d['qa']['send_allowed']==0

def test_b06_locality_granularity_and_collision_guards():
    d=load(STATE)
    m=next(r for r in d['decisions'] if r['source_record_key']=='MD-1bf5b9fb31fc299a0c86')['locality_variant_review']
    assert m['related_canonical_locality']=='Montreux' and m['related_canonical_property_count']==5
    assert m['exact_existing_youth_hostel_target_proven'] is False
    c=next(r for r in d['decisions'] if r['source_record_key']=='MD-1d3317abd4dd8d2032cd')['entity_granularity_review']
    assert c['relationship']=='GROUP_ACCOMMODATION_FACILITY'
    assert c['single_physical_hotel_identity_proven'] is False and c['hotel_type_coercion_forbidden'] is True
    b=next(r for r in d['decisions'] if r['source_record_key']=='MD-19cf8bbb5909736ab761')['canonical_collision_review']
    assert b['match_existing_proven'] is False and b['same_real_world_entity'] is False
    bad=next(r for r in d['decisions'] if r['source_record_key']=='MD-1cf6c236e4dcc1381605')['canonical_collision_review']
    assert bad['token_jaccard_ppm']==500000 and bad['match_existing_proven'] is False

def test_b07_next_is_exact_and_locked():
    n=load(NEXT)
    assert n['route']=='CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B07'
    assert n['b07_source_record_keys']==B07
    assert n['authority_epoch']=='HS_ENTITY_EPOCH_2026-08-25_E4'
    assert n['authority_advance_allowed'] is False and n['canonical_id_allocation_allowed'] is False
    assert n['h_id_allocations']==0 and n['canonical_id_reservations']==0
    assert n['crm_universe_complete'] is False and n['outbound']=='CLOSED' and n['send_allowed']==0
