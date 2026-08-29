import hashlib
import json
from pathlib import Path

ARTIFACT = Path("docs/state/SRET_PROVIDER_IDENTITY_050_SUB02_33206402141.json")


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_provider_identity_sub02_is_review_only_and_conservative():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    selection = data["selection"]
    keys = selection["processed_source_keys"]
    assert selection["processed_items"] == len(keys) == 10
    assert selection["remaining_items_in_bucket"] == 27
    assert selection["processed_source_keys_sha256"] == _sha(keys) == "2f7c897bea1a0606ced6c5c78a0327f68c4ab72cf3e0904108e0e633db4a8213"
    assert len(data["provider_response_sha256"]) == 10
    assert data["provider_enrichment"]["state"] == "EXECUTED_VALIDATED_REVIEW_ONLY"
    assert data["provider_enrichment"]["results_count"] == 10
    assert data["review"]["review_state"] == "NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED"
    assert data["result_counts"]["NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED"] == 10
    assert data["mapping_effect"]["terminal_mappings"] == 0
    assert data["mapping_effect"]["reconcile_required_delta"] == 0
    assert data["mapping_effect"]["effective_reconcile_required"] == 1404
    inv = data["hard_invariants"]
    assert inv["authority_advanced"] is False
    assert inv["h_id_allocations"] == 0
    assert inv["canonical_id_reservations"] == 0
    assert inv["crm_universe_complete"] is False
    assert inv["outbound"] == "CLOSED"
    assert inv["send_allowed"] == 0
