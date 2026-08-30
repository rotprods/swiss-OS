import json
from pathlib import Path

ART = Path("docs/recovery/DB_EGRESS_CAPABILITY_GAUNTLET_2026-08-30.json")


def test_db_egress_failure_family_is_generalized_and_fail_closed():
    data = json.loads(ART.read_text(encoding="utf-8"))
    assert data["schema_version"] == "DB-EGRESS-CAPABILITY-GAUNTLET-1.0"
    assert data["authority"] == "RECOVERY_EVIDENCE_ONLY"
    assert data["parent_main_sha"] == "f21a69ec240727167cb7aba87a138f93cc0b9d74"
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["reconstructed_db"]["source_v13_sha256"] == "0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5"
    assert data["reconstructed_db"]["exact_e4_sha256"] == data["authority_materialized_sha256"]
    assert data["reconstructed_db"]["sqlite_integrity_check"] == "ok"
    assert data["reconstructed_db"]["foreign_key_violations"] == 0

    probes = data["fallback_probes"]
    assert len(probes) == 2
    assert all(p["result"] == "BLOCKED_FILE_REFERENCE" for p in probes)
    assert all(p["publication_occurred"] is False for p in probes)
    capsule = probes[1]["input"]
    assert capsule["gzip_size_bytes"] == 290689
    assert capsule["gzip_sha256"] == "97c6e617cde0d98967afec8633a4bba3d63df49787985199ca93d8bd0816483a"
    assert capsule["base64_length"] == 387588
    assert capsule["text_capsule_sha256"] == "e8e0484e907b1ef826e400bfdbd207924cb887a69786caf21d778f37934dd34a"

    family = data["failure_family"]
    assert family["classification"] == "GENERATED_LOCAL_FILE_REFERENCE_EGRESS_UNAVAILABLE"
    assert family["sqlite_mime_specific"] is False
    assert family["retry_same_strategy_allowed"] is False

    effect = data["authority_effect"]
    assert effect["authority_advanced"] is False
    assert effect["hotels_master_mutations"] == effect["terminal_mapping_delta"] == 0
    assert effect["h_id_allocations"] == effect["canonical_id_reservations"] == 0
    assert effect["crm_universe_complete"] is False
    assert effect["outbound"] == "CLOSED" and effect["send_allowed"] == 0
    assert effect["irreversible_external_actions"] == 0
    assert data["next"]["verify_live_truth_before_execution"] is True
