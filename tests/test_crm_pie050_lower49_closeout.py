import json
from pathlib import Path

CLOSEOUT = Path('docs/state/CRM_PIE050_LOWER49_CLOSEOUT_33206402141.json')
NEXT = Path('docs/state/NEXT_META_EXECUTION_2026-08-30.json')
CLAIM = Path('docs/state/v2/claims/CLAIM-CRM-PIE050-LOWER49-005.json')
ACTIVE = Path('docs/state/v2/active-claims.json')
STATE = Path('STATE.md')
META = Path('docs/state/v2/META_GRAPH_DELTA_PIE050_LOWER49_CLOSEOUT_2026-08-30.json')
P1 = Path('docs/state/PIE050_LOWER49_REVIEW_PACKET_01_2026-08-30.json')
P2 = Path('docs/state/PIE050_LOWER49_REVIEW_PACKET_02_2026-08-30.json')
P3 = Path('docs/state/PIE050_LOWER49_REVIEW_PACKET_03_2026-08-30.json')
P4 = Path('docs/state/PIE050_LOWER49_REVIEW_PACKET_04_2026-08-30.json')
P5 = Path('docs/state/PIE050_LOWER49_REVIEW_PACKET_05_2026-08-30.json')
QUEUE = Path('docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def test_closeout_accounts_for_exact_lower49_without_authority_mutation():
    closeout = load(CLOSEOUT)
    queue = load(QUEUE)
    packets = [load(p) for p in [P1, P2, P3, P4, P5]]
    ordinary = {r['source_record_key'] for packet in packets for r in packet['reviews']}
    special = {case['source_record_key'] for case in closeout['special_cases']}
    all_keys = set(queue['source_record_keys'])

    assert closeout['parent_git_sha'] == '11a528dd1584b3606fed83356c006065e9785778'
    assert closeout['authority_epoch'] == 'HS_ENTITY_EPOCH_2026-08-25_E4'
    assert closeout['lower49']['queue_count'] == 49
    assert closeout['lower49']['queue_keys_sha256'] == queue['source_record_keys_sha256']
    assert len(ordinary) == closeout['lower49']['ordinary_distinctness_reviewed'] == 47
    assert len(special) == closeout['lower49']['special_relationship_reviewed'] == 2
    assert ordinary.isdisjoint(special)
    assert ordinary | special == all_keys
    assert closeout['lower49']['preauthority_classified_total'] == 49
    assert closeout['lower49']['preauthority_pending'] == 0

    effect = closeout['authority_effect']
    assert effect['authority_advanced'] is False
    assert effect['terminal_source_mapping_delta'] == 0
    assert effect['h_id_allocations'] == effect['canonical_id_reservations'] == 0
    assert effect['crm_universe_complete'] is False
    assert effect['outbound'] == 'CLOSED' and effect['send_allowed'] == 0
    assert effect['irreversible_external_actions'] == 0


def test_delta_dual_artifact_has_explicit_single_preauth_precedence():
    closeout = load(CLOSEOUT)
    delta = next(c for c in closeout['special_cases'] if c['source_record_key'] == 'MD-7976c173678dc89c9cf0')
    assert delta['canonical_preauth_artifact'] == 'docs/state/PIE050_DELTA_RESORT_RELATIONSHIP_CANDIDATE_2026-08-30.json'
    assert delta['superseded_redundant_evidence_artifact'] == 'docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json'
    reconciliation = closeout['concurrency_reconciliation']
    assert reconciliation['conflicting_authority_mutation'] is False
    assert reconciliation['history_deleted'] is False
    assert reconciliation['redundant_surface_status'] == 'SUPERSEDED_REDUNDANT_EVIDENCE'


def test_token5_is_released_and_next_is_fail_closed():
    claim = load(CLAIM)
    active = load(ACTIVE)
    next_state = load(NEXT)

    assert claim['claim_id'] == 'CLAIM-CRM-PIE050-LOWER49-005'
    assert claim['fencing_token'] == 5 and claim['state'] == 'RELEASED'
    assert all(c.get('claim_id') != claim['claim_id'] for c in active['claims'])
    assert active['fencing_high_watermark'] == 5
    assert next_state['parent_sha'] == '11a528dd1584b3606fed83356c006065e9785778'
    assert next_state['authority_epoch'] == 'HS_ENTITY_EPOCH_2026-08-25_E4'
    assert next_state['released_claim_id'] == claim['claim_id']
    assert next_state['known_live_metrics']['lower49_preauthority_classified'] == 49
    assert next_state['known_live_metrics']['lower49_preauthority_pending'] == 0
    locks = next_state['hard_invariants']
    assert locks['crm_universe_complete'] is False
    assert locks['outbound'] == 'CLOSED' and locks['send_allowed'] == 0
    assert locks['canonical_id_reservations_from_staging'] == 0
    assert locks['authority_from_canary_or_cache'] is False


def test_state_and_meta_graph_expose_real_blockers_not_stale_reconstruction_route():
    state = STATE.read_text(encoding='utf-8')
    meta = load(META)
    node_states = {n['id']: n['state'] for n in meta['nodes']}

    assert 'PREAUTH classification total' in state
    assert '47 / 47' in state and '2 / 2' in state
    assert 'CLAIM-CRM-PIE050-LOWER49-005` is **RELEASED**' in state
    assert 'Reconstruct the **exact lower49 queue**' not in state
    assert node_states['CLAIM-CRM-PIE050-LOWER49-005'] == 'RELEASED'
    assert node_states['DELTA-PREAUTH-PR334'] == 'CANONICAL_PREAUTH_SURFACE'
    assert node_states['DELTA-PREAUTH-PR333'] == 'SUPERSEDED_REDUNDANT_EVIDENCE'
    assert node_states['SSR-DISCOVER-SWISS-KEY'] == 'BLOCKED_PROVIDER_CREDENTIAL_BOUNDARY'
