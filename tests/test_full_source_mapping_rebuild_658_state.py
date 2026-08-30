import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL657 = ROOT / "docs/state/FULL_SOURCE_MAPPING_REBUILD_657_ATTESTATION_33206402141.json"
FULL658 = ROOT / "docs/state/FULL_SOURCE_MAPPING_REBUILD_658_ATTESTATION_33206402141.json"
BATCH8 = ROOT / "docs/state/SOURCE_RESOLUTION_REVIEW_BATCH_0008_33206402141.json"
CLAIM = ROOT / "docs/state/v2/claims/CLAIM-CRM-SRR-SPECIAL-006.json"
ACTIVE = ROOT / "docs/state/v2/active-claims.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_full658_rebuild_advances_only_exact_preauthority_mapping_frontier():
    old = load(FULL657)
    new = load(FULL658)
    batch = load(BATCH8)

    assert new["schema_version"] == "FULL-SOURCE-MAPPING-REBUILD-ATTESTATION-2.1"
    assert new["parent_git_sha"] == "db0bd9bb6eab966230e6a9cb42688be3a952867c"
    assert new["authority_epoch"] == old["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert new["authority_parent_materialized_sha256"] == old["authority_parent_materialized_sha256"]
    assert new["source"]["records"] == old["source"]["records"] == 2061
    assert new["source"]["records_sha256"] == old["source"]["records_sha256"]
    assert new["candidate"]["records"] == old["candidate"]["records"] == 1438
    assert new["candidate"]["records_sha256"] == old["candidate"]["records_sha256"]
    assert new["canonical_projection"]["rows"] == old["canonical_projection"]["rows"] == 690
    assert new["canonical_projection"]["identity_sha256"] == old["canonical_projection"]["identity_sha256"]

    rb = new["rebuild"]
    assert rb["exact_name_city"] == 623
    assert rb["pinned_exact_correction"] == 1
    assert rb["explicit_srr_deltas"] == 34
    assert rb["terminal_source_mappings"] == 658
    assert rb["reconcile_required"] == 1403
    assert rb["unique_canonical_targets"] == 656
    assert rb["all_source_keys_sha256"] == old["rebuild"]["all_source_keys_sha256"]
    assert rb["terminal_pairs_sha256"] == "cdcecdf445395fe36c6318c2f0103757b0a14ec08d33e229c138df2ec36ad56e"
    assert rb["unresolved_source_keys_sha256"] == "910cfd92974025a836430612387d380be0f15d173d41f20fda6fea2bcca48581"
    assert rb["terminal_pairs_sha256"] != old["rebuild"]["terminal_pairs_sha256"]
    assert rb["unresolved_source_keys_sha256"] != old["rebuild"]["unresolved_source_keys_sha256"]
    assert rb["terminal_source_mappings"] + rb["reconcile_required"] == new["source"]["records"]

    recovery = new["recovery_recipe"]
    assert recovery["exceptional_count"] == 35
    assert len(recovery["exceptional_mappings"]) == 35
    assert set(old["recovery_recipe"]["exceptional_mappings"].items()) <= set(recovery["exceptional_mappings"].items())
    assert recovery["exceptional_mappings"]["MD-33d867e983644585e4b2"] == "H-0114"
    review = batch["reviews"][0]
    assert review["source_record_key"] == "MD-33d867e983644585e4b2"
    assert review["canonical_hotel_id"] == "H-0114"
    assert review["action"] == "ALIAS_EXISTING"


def test_full658_ragr_many_to_one_and_hard_safety_locks_are_explicit():
    data = load(FULL658)
    old = load(FULL657)

    assert data["ragr"]["reverse_authority_source_gaps"] == 34
    assert data["ragr"]["gap_hotel_ids"] == old["ragr"]["gap_hotel_ids"]
    assert data["ragr"]["gap_hotel_ids_sha256"] == "bca692c105efac8c8929c1639e1ebe643dd03f0a6ecab4bb42d86e0acccba568"

    aliases = {item["canonical_hotel_id"]: item["source_record_keys"] for item in data["many_to_one_source_aliases"]}
    assert aliases == {
        "H-0114": ["MD-33d867e983644585e4b2", "MD-b1eb8f0ce9f3a4733c71"],
        "H-0452": ["MD-319d62613a484d48f48a", "MD-7c70baeb19408c2e971b"],
    }

    qa = data["qa"]
    assert qa["previous_657_terminal_pairs_reproduced"] is True
    assert qa["previous_657_unresolved_sha_reproduced"] is True
    assert qa["live_canonical_identity_reproduced"] is True
    assert qa["source_key_conservation"] is True
    assert qa["terminal_source_keys_unique"] is True
    assert qa["all_targets_in_690_projection"] is True
    assert qa["exceptional_source_keys_all_candidate_side"] is True
    assert qa["fuzzy_autobind"] is False
    assert qa["authority_advanced"] is False
    assert qa["h_id_allocations"] == 0
    assert qa["canonical_id_reservations"] == 0
    assert qa["irreversible_external_actions"] == 0
    assert qa["crm_universe_complete"] is False
    assert qa["outbound"] == "CLOSED"
    assert qa["send_allowed"] == 0


def test_token6_scope_amendment_allows_only_preauthority_rebuild_surface():
    claim = load(CLAIM)
    active = load(ACTIVE)

    assert claim["state"] == "ACTIVE"
    assert claim["fencing_token"] == 6
    assert claim["authority_ceiling"] == "PREAUTH_SRR_DECISION_ONLY_NO_CANONICAL_MUTATION"
    assert "docs/state/FULL_SOURCE_MAPPING_REBUILD_*" in claim["resource_scopes"]
    assert claim["scope_amendments"][-1]["added_resource_scope"] == "docs/state/FULL_SOURCE_MAPPING_REBUILD_*"
    for forbidden in ("HOTELS_AUTHORITY_MUTATION", "H_ID_ALLOCATION", "CANONICAL_ID_RESERVATION", "OUTBOUND_EXECUTION", "DISCOVER_SWISS_SSR_AUTHORITY"):
        assert forbidden in claim["excluded_scopes"]

    assert active["as_of_main_sha"] == "db0bd9bb6eab966230e6a9cb42688be3a952867c"
    assert active["fencing_high_watermark"] == 6
    assert len(active["claims"]) == 1
    projected = active["claims"][0]
    assert projected["claim_id"] == claim["claim_id"]
    assert projected["resource_scopes"] == claim["resource_scopes"]
    assert projected["excluded_scopes"] == claim["excluded_scopes"]
