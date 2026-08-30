import hashlib
import json
from pathlib import Path

PACKET=Path('docs/state/PIE050_DELTA_RESORT_RELATIONSHIP_CANDIDATE_2026-08-30.json')

def load(): return json.loads(PACKET.read_text(encoding='utf-8'))

def test_delta_relationship_candidate_is_fail_closed():
    d=load()
    assert d['parent_git_sha']=='3fefe3725205563e8cb363cafbe07dd95b4015ed'
    assert d['authority_epoch']=='HS_ENTITY_EPOCH_2026-08-25_E4'
    assert d['claim_id']=='CLAIM-CRM-PIE050-LOWER49-005' and d['fencing_token']==5
    assert d['source_record_key']=='MD-7976c173678dc89c9cf0'
    assert d['canonical_candidate']['hotel_id']=='H-0220'
    assert d['relationship_class']=='SAME_OPERATOR_SAME_LICENSE_ADJACENT_PREMISES_SUBINVENTORY'
    assert d['review_outcome']=='RELATIONSHIP_SENSITIVE_REQUIRES_ENTITY_GRANULARITY_AUTHORITY_REVIEW'
    assert len(d['current_relationship_evidence']) >= 4
    assert d['terminal_mapping_proposal']['terminal_mapping_allowed'] is False
    assert d['new_canonical_proposal']['canonical_id_reservation_allowed'] is False
    e=d['effect']
    assert e['terminal_source_mappings_added']==0 and e['terminal_source_mappings_total']==657
    assert e['reconcile_required_before']==e['reconcile_required_after']==1404
    assert e['h_id_allocations']==e['canonical_id_reservations']==0
    assert e['authority_advanced'] is False and e['crm_universe_complete'] is False
    assert e['outbound']=='CLOSED' and e['send_allowed']==0

def test_delta_relationship_candidate_hash():
    d=load(); expected=d.pop('packet_sha256')
    canonical=json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical).hexdigest()==expected
