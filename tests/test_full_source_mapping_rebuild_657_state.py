import json
from pathlib import Path

ARTIFACT = Path("docs/state/FULL_SOURCE_MAPPING_REBUILD_657_ATTESTATION_33206402141.json")


def test_full_source_mapping_rebuild_657_invariants():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    rebuild = data["rebuild"]
    recovery = data["recovery_recipe"]
    assert data["source"]["records"] == 2061
    assert data["candidate"]["records"] == 1438
    assert rebuild["exact_name_city"] == 623
    assert rebuild["pinned_exact_correction"] == 1
    assert rebuild["explicit_srr_deltas"] == 33
    assert rebuild["terminal_source_mappings"] == 657
    assert rebuild["reconcile_required"] == 1404
    assert rebuild["unique_canonical_targets"] == 656
    assert len(recovery["exceptional_mappings"]) == recovery["exceptional_count"] == 34
    assert recovery["exceptional_mappings"]["MD-dd14bef2251b12ecd017"] == "H-0088"
    assert recovery["exceptional_mappings"]["MD-7c70baeb19408c2e971b"] == "H-0452"
    assert data["ragr"]["reverse_authority_source_gaps"] == len(data["ragr"]["gap_hotel_ids"]) == 34
    assert data["many_to_one_source_aliases"][0]["canonical_hotel_id"] == "H-0452"
    assert data["qa"]["authority_advanced"] is False
    assert data["qa"]["h_id_allocations"] == 0
    assert data["qa"]["canonical_id_reservations"] == 0
    assert data["qa"]["outbound"] == "CLOSED"
    assert data["qa"]["send_allowed"] == 0
