import json
from pathlib import Path


def test_b07_evidence_packet_is_complete_and_preauthority_only():
    p = json.loads(Path('docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B07_EVIDENCE_PACKET_2026-09-01.json').read_text())
    expected = [
        'MD-21cc675b7ddb4fb39c9a','MD-21d80dc6cd95557824af','MD-2371d6a62dfb46d25297',
        'MD-23cc9ed081909afb8a76','MD-23d989d03ab52258efd9','MD-246d25ab845005abc642',
        'MD-2503eb358ae6e9c901a7','MD-262dc840666b01355485','MD-2646d4114c7721222c87',
        'MD-267556b17b23beb697d5'
    ]
    assert p['route'] == 'CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B07'
    assert [r['source_record_key'] for r in p['records']] == expected
    assert len(set(expected)) == 10
    assert all(r['review_state'] == 'CURRENT_EVIDENCE_CAPTURED_REVIEW_REQUIRED' for r in p['records'])
    assert all(r['current_evidence'] for r in p['records'])
    c = p['counts']
    assert c['input_records'] == c['source_identity_rows_recovered'] == c['current_evidence_captured'] == 10
    assert c['srr_decisions'] == c['terminal_mapping_delta'] == 0
    assert c['canonical_id_reservations'] == c['h_id_allocations'] == 0
    assert p['authority']['effect'] == 'NONE'
    assert p['hard_invariants']['authority_advanced'] is False
    assert p['hard_invariants']['outbound'] == 'CLOSED'
    assert p['hard_invariants']['send_allowed'] == 0
    assert p['hard_invariants']['canonical_id_reservations'] == 0
    assert p['hard_invariants']['h_id_allocations'] == 0
