import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'docs/state/CRM_CURRENT_UNRESOLVED_LT350_B07_2026-09-10.json'
HANDOFF = ROOT / 'docs/handoffs/META_20260910_CRM_CURRENT_LT350_B07.md'

KEYS = [
    'MD-21cc675b7ddb4fb39c9a',
    'MD-21d80dc6cd95557824af',
    'MD-2371d6a62dfb46d25297',
    'MD-23cc9ed081909afb8a76',
    'MD-23d989d03ab52258efd9',
    'MD-246d25ab845005abc642',
    'MD-2503eb358ae6e9c901a7',
    'MD-262dc840666b01355485',
    'MD-2646d4114c7721222c87',
    'MD-267556b17b23beb697d5',
]


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def test_b07_exact_lineage_and_fencing():
    data = load(STATE)
    assert data['wave_id'] == 'CURR-U1403-B07'
    assert data['claim_id'] == 'CLAIM-CRM-ENTITY-RESOLUTION-016'
    assert data['fencing_token'] == 16
    assert data['selection']['selected_source_record_keys'] == KEYS
    assert len(set(KEYS)) == 10
    assert data['authority']['canonical_rows'] == 690
    assert data['authority']['next_physical_id'] == 'H-0691_UNALLOCATED'
    assert data['authority']['effect'] == 'NONE'


def test_b07_typed_decisions_are_preauthority_only():
    data = load(STATE)
    decisions = data['decisions']
    assert len(decisions) == 10
    assert sum(d['decision'] == 'NEW_CANONICAL_PREAUTH' for d in decisions) == 9
    assert sum(d['decision'] == 'NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED' for d in decisions) == 1
    assert all(d['mapping_state'] == 'RECONCILE_REQUIRED' for d in decisions)
    assert all(d['canonical_h_id_reserved'] is False for d in decisions)
    assert all(d['h_id_allocated'] is False for d in decisions)
    assert all(d['terminal_mapping_created'] is False for d in decisions)
    assert all(d['authority_effect'] == 'NONE' for d in decisions)


def test_b07_frontier_conservation_and_safety():
    data = load(STATE)
    f = data['frontier']
    assert f['batch_reviewed'] == 10
    assert f['batch_new_canonical_preauth'] == 9
    assert f['batch_new_accommodation_preauth_egr_required'] == 1
    assert f['current_lt350000_reviewed_cumulative'] == 70
    assert f['cumulative_new_canonical_preauth'] == 183
    assert f['historical_lt350000_unreviewed_tail_remaining'] == 1219
    assert f['zero_same_city_lane_remaining'] == 415
    assert f['terminal_source_mappings'] == 658
    assert f['reconcile_required'] == 1403
    assert f['h_id_allocations'] == 0
    assert f['canonical_id_reservations'] == 0
    q = data['qa']
    assert q['authority_advanced'] is False
    assert q['crm_universe_complete'] is False
    assert q['outbound'] == 'CLOSED'
    assert q['send_allowed'] == 0


def test_b07_egr_and_group_relations_do_not_collapse_identity():
    data = load(STATE)
    by_key = {d['source_record_key']: d for d in data['decisions']}
    motel = by_key['MD-2503eb358ae6e9c901a7']
    assert motel['entity_granularity']['entity_type'] == 'ACCOMMODATION_MOTEL_RESIDENCE'
    assert motel['entity_granularity']['conventional_hotel_coercion_forbidden'] is True
    geneva = by_key['MD-2646d4114c7721222c87']
    assert any(r.get('target_hotel_id') == 'H-0614' and r['must_not_imply_alias'] for r in geneva['relationship_candidates'])
    nessi = by_key['MD-267556b17b23beb697d5']
    assert any(r['type'] == 'MEMBER_OF_HOTEL_GROUP' and r['must_not_imply_alias'] for r in nessi['relationship_candidates'])


def test_b07_handoff_persists_next_safe_frontier():
    text = HANDOFF.read_text(encoding='utf-8')
    for token in (
        'recompute B08',
        'BLOCKED_COMPARATOR_AUTHORITY',
        'H-0691',
        'OUTBOUND = CLOSED',
    ):
        assert token in text
