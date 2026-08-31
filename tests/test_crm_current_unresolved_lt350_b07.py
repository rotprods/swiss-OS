import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B07_2026-09-01.json'
NEXT=ROOT/'docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B07.json'
GRAPH=ROOT/'docs/state/META_GRAPH_DELTA_CRM_CURRENT_LT350_B07_2026-09-01.json'
CLAIM=ROOT/'docs/state/v2/claims/CLAIM-CRM-CURRENT-B07-007.json'
OLD=ROOT/'docs/state/v2/claims/CLAIM-CRM-SRR-SPECIAL-006.json'
KEYS=['MD-21cc675b7ddb4fb39c9a','MD-21d80dc6cd95557824af','MD-2371d6a62dfb46d25297','MD-23cc9ed081909afb8a76','MD-23d989d03ab52258efd9','MD-246d25ab845005abc642','MD-2503eb358ae6e9c901a7','MD-262dc840666b01355485','MD-2646d4114c7721222c87','MD-267556b17b23beb697d5']

def load(p): return json.loads(p.read_text(encoding='utf-8'))

def test_token7_supersedes_stale_token6_without_authority():
    old=load(OLD); c=load(CLAIM)
    assert old['state']=='SUPERSEDED' and old['superseded_by']==c['claim_id']
    assert c['fencing_token']==7 and c['state']=='ACTIVE'
    assert c['base_sha']=='d56593efff5a5947ae736026578176cb315d0535'
    assert c['authority_ceiling']=='PREAUTH_CURRENT_SOURCE_REVIEW_ONLY_NO_CANONICAL_MUTATION'
    assert 'H_ID_ALLOCATION' in c['excluded_scopes'] and 'OUTBOUND_EXECUTION' in c['excluded_scopes']
    assert c['preconditions']['terminal_mappings']==658 and c['preconditions']['reconcile_required']==1403

def test_b07_exact_lineage_current_evidence_and_fail_closed_disposition():
    d=load(STATE)
    assert d['wave_id']=='CURR-U1403-B07'
    assert d['claim_id']=='CLAIM-CRM-CURRENT-B07-007' and d['fencing_token']==7
    assert d['selection']['selected_source_record_keys']==KEYS
    assert d['selection']['prior_current_reviewed']==60
    assert d['source']['snapshot_id']=='HS-MEMBER-DE-33339392661' and d['source']['coverage_complete'] is True
    assert len(d['decisions'])==10
    for ordinal,row in enumerate(d['decisions'],1):
        assert row['ordinal']==ordinal
        assert row['source_record_key']==KEYS[ordinal-1]
        assert row['historical_similarity_band']=='lt350000'
        assert row['same_city_canonical_count']==0
        assert row['decision']=='NEW_CANONICAL_PREAUTH'
        assert row['mapping_state']=='RECONCILE_REQUIRED'
        assert row['current_evidence']
        assert row['canonical_h_id_reserved'] is False and row['h_id_allocated'] is False
        assert row['terminal_mapping_created'] is False and row['authority_effect']=='NONE'

def test_b07_collision_and_granularity_reviews_are_nonbinding():
    d=load(STATE)
    hammer=next(r for r in d['decisions'] if r['source_record_key']=='MD-21cc675b7ddb4fb39c9a')['canonical_collision_review']
    assert hammer['token_jaccard_ppm']==500000 and hammer['same_real_world_entity'] is False and hammer['match_existing_proven'] is False
    pied=next(r for r in d['decisions'] if r['source_record_key']=='MD-2503eb358ae6e9c901a7')['entity_granularity_review']
    assert pied['protocol']=='EGR-1.0' and pied['relationship']=='MOTEL_RESIDENCE_ACCOMMODATION_ENTITY'
    assert pied['conventional_hotel_type_coercion_forbidden'] is True
    mov=next(r for r in d['decisions'] if r['source_record_key']=='MD-2646d4114c7721222c87')['canonical_collision_review']
    assert mov['canonical_hotel_id']=='H-0614' and mov['same_real_world_entity'] is False and mov['match_existing_proven'] is False

def test_b07_frontier_conserves_authority_and_outbound_lock():
    d=load(STATE); f=d['frontier']; qa=d['qa']
    assert f['current_lt350000_reviewed_cumulative']==70
    assert f['cumulative_new_canonical_preauth']==184
    assert f['historical_lt350000_unreviewed_tail_remaining']==1219
    assert f['zero_same_city_lane_remaining']==415
    assert f['terminal_source_mappings']==658 and f['reconcile_required']==1403
    assert f['h_id_allocations']==0 and f['canonical_id_reservations']==0
    assert qa['authority_advanced'] is False and qa['fuzzy_autobind'] is False
    assert qa['crm_universe_complete'] is False and qa['outbound']=='CLOSED' and qa['send_allowed']==0

def test_b07_next_requires_pinned_lineage_reconstruction_not_current_similarity():
    n=load(NEXT)
    assert n['b07_source_record_keys']==KEYS
    assert n['route']=='COMPUTE_CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B08_FROM_PINNED_LINEAGE'
    assert 'Do not infer B08 from current similarity' in n['exact_dependency']
    assert n['authority_advance_allowed'] is False and n['canonical_id_allocation_allowed'] is False
    assert n['h_id_allocations']==0 and n['canonical_id_reservations']==0
    assert n['outbound']=='CLOSED' and n['send_allowed']==0

def test_b07_graph_is_preauthority_only():
    g=load(GRAPH); nodes={n['id']:n for n in g['nodes']}
    assert g['authority_effect']=='NONE'
    assert nodes['AUTHORITY-E4']['active']==690
    assert nodes['CURR-U1403-B07']['terminal_mapping_delta']==0
    assert nodes['CLAIM-CRM-CURRENT-B07-007']['fencing_token']==7
    assert nodes['OUTBOUND']['state']=='CLOSED' and nodes['OUTBOUND']['send_allowed']==0
    assert g['invariants']['canonical_id_allocations']==0 and g['invariants']['canonical_id_reservations']==0
