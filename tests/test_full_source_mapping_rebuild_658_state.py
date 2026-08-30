import json
from pathlib import Path

ATTEST = Path("docs/state/FULL_SOURCE_MAPPING_REBUILD_658_ATTESTATION_33206402141.json")
NEXT = Path("docs/state/NEXT.json")

def test_full_source_mapping_rebuild_658_invariants():
    a = json.loads(ATTEST.read_text(encoding="utf-8"))
    n = json.loads(NEXT.read_text(encoding="utf-8"))
    r = a["rebuild"]
    q = a["qa"]
    recovery = a["recovery_recipe"]
    assert a["source"]["records"] == 2061
    assert a["candidate"]["records"] == 1438
    assert r["exact_name_city"] == 623
    assert r["pinned_exact_correction"] == 1
    assert r["explicit_srr_deltas"] == 34
    assert r["terminal_source_mappings"] == 658
    assert r["unique_canonical_targets"] == 656
    assert r["reconcile_required"] == 1403
    assert r["terminal_pairs_sha256"] == "cdcecdf445395fe36c6318c2f0103757b0a14ec08d33e229c138df2ec36ad56e"
    assert r["unresolved_source_keys_sha256"] == "910cfd92974025a836430612387d380be0f15d173d41f20fda6fea2bcca48581"
    assert q["previous_657_hash_recipe_reproduced"] is True
    assert q["previous_terminal_pairs_sha256_reproduced"] == "5698591ab5c89bc8651dda6f7e2cfeba8c80312e3c19c78736adf1d0e521727e"
    assert q["previous_unresolved_source_keys_sha256_reproduced"] == "7285cbcd5936cfabd33ea6f1769cfbf99acd3639562306c0e1bf0632d5400323"
    assert q["all_source_keys_sha256_reproduced"] == "950cc95f56c9f70a36b79ef6adb301925f30660527430ae799c2cb5ff30e9497"
    assert len(recovery["exceptional_mappings"]) == recovery["exceptional_count"] == 35
    assert recovery["exceptional_mappings"]["MD-33d867e983644585e4b2"] == "H-0114"
    assert len(a["ragr"]["gap_hotel_ids"]) == a["ragr"]["reverse_authority_source_gaps"] == 34
    assert a["ragr"]["gap_hotel_ids_sha256"] == "bca692c105efac8c8929c1639e1ebe643dd03f0a6ecab4bb42d86e0acccba568"
    assert n["mapping_frontier"]["terminal_coverage_rebuild_pending"] is False
    assert n["mapping_frontier"]["terminal_source_mappings"] == 658
    assert n["mapping_frontier"]["reconcile_required"] == 1403
    assert q["authority_advanced"] is False
    assert q["h_id_allocations"] == 0
    assert q["canonical_id_reservations"] == 0
    assert q["outbound"] == "CLOSED"
    assert q["send_allowed"] == 0
    assert q["irreversible_external_actions"] == 0
