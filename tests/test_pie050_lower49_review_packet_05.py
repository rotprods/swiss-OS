import hashlib
import json
from pathlib import Path

QUEUE=Path('docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json')
PACKETS=[Path(f'docs/state/PIE050_LOWER49_REVIEW_PACKET_0{i}_2026-08-30.json') for i in range(1,6)]
SPECIAL={'MD-33d867e983644585e4b2','MD-7976c173678dc89c9cf0'}

def load(p): return json.loads(p.read_text(encoding='utf-8'))

def test_packet05_closes_ordinary_lower49_frontier_fail_closed():
    q=load(QUEUE); ps=[load(p) for p in PACKETS]
    sets=[{r['source_record_key'] for r in p['reviews']} for p in ps]
    assert all(not (sets[i]&sets[j]) for i in range(5) for j in range(i+1,5))
    reviewed=set().union(*sets)
    assert len(reviewed)==47
    assert set(q['source_record_keys'])-reviewed==SPECIAL
    p5=ps[-1]; keys=sorted(sets[-1])
    assert p5['parent_git_sha']=='ccc9fad1369f2e2cf1ddb25074d7a362fa1f6604'
    assert p5['authority_epoch']=='HS_ENTITY_EPOCH_2026-08-25_E4'
    assert p5['claim_id']=='CLAIM-CRM-PIE050-LOWER49-005' and p5['fencing_token']==5
    assert p5['reviewed_count']==7 and p5['reviewed_cumulative']==47 and p5['pending_lower49_after']==2
    assert set(p5['pending_special_relationship_keys'])==SPECIAL
    assert hashlib.sha256('\n'.join(keys).encode()).hexdigest()==p5['reviewed_source_record_keys_sha256']
    for r in p5['reviews']:
        assert r['review_outcome']=='CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED'
        assert r['terminal_source_mapping']=='NONE' and r['authority_effect']=='NONE'
        assert r['new_identity_status']=='UNALLOCATED_PREAUTH_CANDIDATE' and r['current_public_evidence_urls']
    e=p5['effect']
    assert e['terminal_source_mappings_added']==0 and e['terminal_source_mappings_total']==657
    assert e['reconcile_required_before']==e['reconcile_required_after']==1404
    assert e['h_id_allocations']==e['canonical_id_reservations']==0
    assert e['authority_advanced'] is False and e['crm_universe_complete'] is False
    assert e['outbound']=='CLOSED' and e['send_allowed']==0

def test_packet05_hash():
    d=load(PACKETS[-1]); expected=d.pop('packet_sha256')
    canonical=json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical).hexdigest()==expected
