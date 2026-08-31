import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B05_2026-08-31.json'
NEXT=ROOT/'docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B05.json'
KEYS=['MD-1523bc8c54a8f80c63a1','MD-15328beab2813a777e0d','MD-1679afa763ce7de7c324','MD-16d503bef0fa48f1d44d','MD-172e10497469ac29259e','MD-17a059dc9632c6ff4d1d','MD-17af64859ef43e875027','MD-1855265ec07d6b3c1a40','MD-18cbb9206e15539f177d','MD-18ddf5bd589df297650d']
B06=['MD-19586421c51cd23ffdc4','MD-19705e8792a9dc41db8d','MD-19cf8bbb5909736ab761','MD-1a855e1755243c506c83','MD-1bf5b9fb31fc299a0c86','MD-1cca35242ea804d858d2','MD-1cf6c236e4dcc1381605','MD-1d3317abd4dd8d2032cd','MD-1d7a0e1653c1039424b6','MD-1dd3e23d5d5f7559cf99']

def load(p): return json.loads(p.read_text(encoding='utf-8'))

def test_b05_lineage_and_safety():
    d=load(STATE)
    assert d['parent_git_sha']=='06af39bb00bc50c6b76f5d68f42c7966d8306229'
    assert d['selection']['selected_source_record_keys']==KEYS
    assert d['selection']['prior_current_reviewed']==40
    assert d['source']['snapshot_id']=='HS-MEMBER-DE-33339392661' and d['source']['coverage_complete'] is True
    assert len(d['decisions'])==10
    for r in d['decisions']:
        assert r['decision']=='NEW_CANONICAL_PREAUTH' and r['mapping_state']=='RECONCILE_REQUIRED'
        assert r['current_evidence'] and r['canonical_h_id_reserved'] is False and r['h_id_allocated'] is False
        assert r['terminal_mapping_created'] is False and r['authority_effect']=='NONE'
    assert d['frontier']['current_lt350000_reviewed_cumulative']==50
    assert d['frontier']['cumulative_new_canonical_preauth']==164
    assert d['frontier']['historical_lt350000_unreviewed_tail_remaining']==1239
    assert d['frontier']['zero_same_city_lane_remaining']==435
    assert d['frontier']['terminal_source_mappings']==658 and d['frontier']['reconcile_required']==1403
    assert d['qa']['authority_advanced'] is False and d['qa']['outbound']=='CLOSED' and d['qa']['send_allowed']==0

def test_b05_fast_lane_exceptions_fail_closed():
    d=load(STATE)
    st=next(r for r in d['decisions'] if r['source_record_key']=='MD-172e10497469ac29259e')['locality_variant_review']
    assert st['related_canonical_locality']=='St. Moritz' and st['related_canonical_property_count']==17
    assert st['exact_existing_youth_hostel_target_proven'] is False
    mag=next(r for r in d['decisions'] if r['source_record_key']=='MD-18cbb9206e15539f177d')['entity_granularity_review']
    assert mag['related_source_record_key']=='MD-59d5669304eabea2a4ef'
    assert mag['relationship']=='SHARED_RECEPTION_SIBLING_ACCOMMODATION_PROPERTY'
    assert mag['collapse_to_alias_proven'] is False
    concorde=next(r for r in d['decisions'] if r['source_record_key']=='MD-16d503bef0fa48f1d44d')['canonical_collision_review']
    assert concorde['token_jaccard_ppm']==600000 and concorde['match_existing_proven'] is False

def test_b06_next_is_exact_and_locked():
    n=load(NEXT)
    assert n['route']=='CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B06'
    assert n['b06_source_record_keys']==B06
    assert n['authority_epoch']=='HS_ENTITY_EPOCH_2026-08-25_E4'
    assert n['authority_advance_allowed'] is False and n['canonical_id_allocation_allowed'] is False
    assert n['h_id_allocations']==0 and n['canonical_id_reservations']==0
    assert n['crm_universe_complete'] is False and n['outbound']=='CLOSED' and n['send_allowed']==0
