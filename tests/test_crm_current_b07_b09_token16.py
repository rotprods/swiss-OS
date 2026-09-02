import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=[ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B07_2026-09-02.json',ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B08_2026-09-02.json',ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B09_2026-09-02.json']
CLAIM='CLAIM-CRM-CURRENT-B07-B09-016'
SESSION='SES-20260902T152200Z-CRM-B07-B09-016'
B10=['MD-315c01eaa157e5b3602f','MD-323db50ea273aa998ca6','MD-339cb8d3f38f76b192dd','MD-34f61a1d95ba700cfe94','MD-350bcd0642995b5b2d89','MD-35ea8c63b3b3459e39b7','MD-36743f6ab6fb963fb3a3','MD-36c39d2fd2a2f49a5855','MD-36de2d991c8ba24a7a94','MD-377dc48ee075aa309eab']

def load(p): return json.loads(p.read_text(encoding='utf-8'))

def test_token16_batches_share_fresh_lineage_and_hard_locks():
    ds=[load(p) for p in FILES]
    assert [d['wave_id'] for d in ds]==['CURR-U1403-B07-R1','CURR-U1403-B08','CURR-U1403-B09']
    for d in ds:
        assert d['claim_id']==CLAIM and d['session_id']==SESSION and d['fencing_token']==16
        assert d['source']['snapshot_id']=='HS-MEMBER-DE-33339392661' and d['source']['records']==2061
        assert d['authority']['canonical_rows']==690 and d['authority']['next_h_id']=='H-0691_UNALLOCATED'
        assert d['locks']=={'authority_advanced':False,'canonical_id_reservations':0,'h_id_allocations':0,'terminal_mapping_delta':0,'outbound':'CLOSED','send_allowed':0}
        assert d['frontier']['terminal_source_mappings']==658 and d['frontier']['reconcile_required']==1403
    assert [d['frontier']['reviewed_cumulative'] for d in ds]==[70,80,90]
    assert [d['frontier']['cumulative_new_canonical_preauth'] for d in ds]==[184,193,200]

def test_b07_and_b08_preserve_preauthority_and_egr_semantics():
    b07,b08,_=map(load,FILES)
    assert b07['decision_counts']=={'NEW_CANONICAL_PREAUTH':10,'MATCH_EXISTING':0,'EGR_REQUIRED':0,'TERMINAL_MAPPING_CREATED':0}
    assert b07['special_reviews']['MD-2646d4114c7721222c87']['canonical_comparator']=='H-0614'
    assert b07['special_reviews']['MD-2503eb358ae6e9c901a7']['conventional_hotel_type_coercion_forbidden'] is True
    assert b08['decision_counts']=={'NEW_CANONICAL_PREAUTH':9,'MATCH_EXISTING':0,'EGR_REQUIRED':1,'TERMINAL_MAPPING_CREATED':0}
    assert b08['egr_required']['MD-2b51224ee38c42763d77']['single_physical_accommodation_identity_proven'] is False

def test_b09_detects_wilerbad_false_zero_city_without_terminalizing():
    b09=load(FILES[2])
    assert b09['decision_counts']=={'NEW_CANONICAL_PREAUTH':7,'MATCH_EXISTING_REVIEW':1,'EGR_REQUIRED':2,'TERMINAL_MAPPING_CREATED':0}
    w=b09['match_existing_review']['MD-30b31ab8d1f66bab5fcf']
    assert w['target_hotel_id']=='H-0681'
    assert w['source_city']=='Wilen (Sarnen)' and w['canonical_city']=='Wilen'
    assert w['terminal_mapping_authorized'] is False
    assert b09['egr_required']['MD-310fdead9d1b018a63fd']['first_party_explicit_not_a_hotel'] is True

def test_next_b10_is_exact_and_non_authoritative():
    n=load(ROOT/'docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B09.json')
    assert n['claim_id']==CLAIM and n['fencing_token']==16
    assert n['selected_source_record_keys']==B10
    payload=json.dumps(B10,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(payload).hexdigest()==n['selected_keys_sha256']=='8f170c7dca912e635e324764d52f5c2344a7bfe47b7f77033cc25e63cb149d35'
    assert n['hard_locks']['authority_advance_allowed'] is False
