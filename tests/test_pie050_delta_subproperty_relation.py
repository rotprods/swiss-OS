import hashlib
import json
from pathlib import Path

ART=Path('docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json')
QUEUE=Path('docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json')

def load(p): return json.loads(p.read_text(encoding='utf-8'))

def test_delta_relation_is_preserved_without_identity_collapse_or_allocation():
    d=load(ART); q=load(QUEUE)
    assert d['parent_git_sha']=='3fefe3725205563e8cb363cafbe07dd95b4015ed'
    assert d['authority_epoch']=='HS_ENTITY_EPOCH_2026-08-25_E4'
    assert d['claim_id']=='CLAIM-CRM-PIE050-LOWER49-005' and d['fencing_token']==5
    assert d['source_record_key']=='MD-7976c173678dc89c9cf0' and d['source_record_key'] in q['source_record_keys']
    assert d['canonical_candidate']['hotel_id']=='H-0220'
    assert d['review_outcome']=='COLOCATED_SUBPROPERTY_RELATION_REQUIRES_AUTHORITY_REVIEW'
    assert d['relationship_hypothesis']['relation']=='OPERATED_AS_SUBPROPERTY_OF'
    assert d['relationship_hypothesis']['authority']=='PROPOSED_ONLY'
    assert d['terminal_mapping']['state']=='NOT_PROPOSED' and d['terminal_mapping']['allowed'] is False
    assert d['new_identity_status']=='UNALLOCATED_PREAUTH_CANDIDATE'
    assert len(d['current_public_evidence'])>=3
    e=d['effect']
    assert e['terminal_source_mappings_added']==0 and e['terminal_source_mappings_total']==657
    assert e['reconcile_required_before']==e['reconcile_required_after']==1404
    assert e['h_id_allocations']==e['canonical_id_reservations']==0
    assert e['authority_advanced'] is False and e['crm_universe_complete'] is False
    assert e['outbound']=='CLOSED' and e['send_allowed']==0

def test_delta_relation_hash():
    d=load(ART); expected=d.pop('packet_sha256')
    assert hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==expected
