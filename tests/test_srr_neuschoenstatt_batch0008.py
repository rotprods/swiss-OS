import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/state/SOURCE_RESOLUTION_REVIEW_BATCH_0008_33206402141.json"
OVERLAY = ROOT / "docs/state/SOURCE_MAPPING_OVERLAY_SRR_BATCH_0008_ATTESTATION_33206402141.json"
FULL657 = ROOT / "docs/state/FULL_SOURCE_MAPPING_REBUILD_657_ATTESTATION_33206402141.json"
NEU = ROOT / "docs/state/PIE050_NEUSCHOENSTATT_SAME_PROPERTY_CANDIDATE_2026-08-30.json"
DELTA = ROOT / "docs/state/PIE050_DELTA_SUBPROPERTY_RELATION_2026-08-30.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha(payload):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_neuschoenstatt_is_one_bounded_preauthority_alias_delta():
    review = load(REVIEW)
    overlay = load(OVERLAY)
    full = load(FULL657)
    neu = load(NEU)
    delta = load(DELTA)

    assert review["schema_version"] == "SOURCE-RESOLUTION-EXPLICIT-REVIEWS-1.0"
    assert review["reviews_count"] == 1
    item = review["reviews"][0]
    assert item["source_record_key"] == neu["source_record_key"] == "MD-33d867e983644585e4b2"
    assert item["action"] == "ALIAS_EXISTING"
    assert item["canonical_hotel_id"] == neu["canonical_candidate"]["hotel_id"] == "H-0114"
    assert item["current_evidence_verified"] is True
    assert item["authority_action"] == "NONE_PREAUTH_REVIEW"
    assert review["application_semantics"]["authority_promotion"] == "FORBIDDEN"
    assert review["application_semantics"]["canonical_h_id_reservation"] == "FORBIDDEN"

    # H-0114 is already source-covered in the exact 657 rebuild; this is a second
    # provider/source alias, not a new canonical target and not an H-ID allocation.
    assert "H-0114" in full["recovery_recipe"]["exceptional_mappings"].values()
    assert "H-0114" not in full["ragr"]["gap_hotel_ids"]
    assert neu["source_record_key"] not in full["recovery_recipe"]["exceptional_mappings"]
    assert delta["source_record_key"] != item["source_record_key"]

    assert overlay["previous_terminal_mappings"] == 657
    assert overlay["effective_terminal_mappings"] == 658
    assert overlay["previous_reconcile_required"] == 1404
    assert overlay["effective_reconcile_required"] == 1403
    assert overlay["effective_unique_canonical_targets"] == 656
    assert overlay["cumulative_terminal_deltas"] == 34
    assert overlay["incremental_terminal_deltas"] == 1
    assert overlay["terminal_coverage_rebuild_pending"] is True
    assert canonical_sha(overlay["lineage_hash_recipe"]["payload"]) == overlay["cumulative_overlay_materialization_sha256"]


def test_batch0008_preserves_authority_and_outbound_locks_and_leaves_delta_unresolved():
    review = load(REVIEW)
    overlay = load(OVERLAY)
    delta = load(DELTA)

    for artifact in (review, overlay):
        assert artifact["authority_advanced"] is False
        assert artifact["h_id_allocations"] == 0
        assert artifact["crm_universe_complete"] is False
        assert artifact["outbound"] == "CLOSED"
        assert artifact["send_allowed"] == 0

    assert delta["terminal_mapping"]["allowed"] is False
    assert delta["new_identity_status"] == "UNALLOCATED_PREAUTH_CANDIDATE"
    assert delta["effect"]["canonical_id_reservations"] == 0
    assert delta["effect"]["h_id_allocations"] == 0
    assert delta["effect"]["outbound"] == "CLOSED"
    assert delta["effect"]["send_allowed"] == 0
