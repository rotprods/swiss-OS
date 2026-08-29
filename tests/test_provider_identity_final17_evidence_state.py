import json
from pathlib import Path

EVIDENCE = Path("docs/state/SRET_PROVIDER_IDENTITY_050_FINAL17_33206402141.json")
NEXT = Path("docs/state/NEXT.json")


def test_final17_evidence_closes_provider_fetch_not_identity_authority():
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    enrich = data["provider_enrichment"]
    assert enrich["github_actions_run_id"] == 33278374703
    assert enrich["github_actions_job_id"] == 99169076312
    assert enrich["artifact_id"] == 9722212725
    assert enrich["artifact_digest_sha256"] == "bfa30d4c89193d62ea02ca5b0120e55977f6508c9ba84cafce120afa4faa8a0e"
    assert enrich["artifact_json_sha256"] == "633e4f38047dfe2e5db41ce3a80f5b69845ffd6235e2c3e769d3f787db112b7f"
    assert enrich["packet_sha256"] == "422f27d7d0e85c5bbba12ac55b77eafc7930204d5e8fec2c3d24f51395b06d7e"
    assert enrich["results_sha256"] == "63bf8781509a968227cbfc1d470a5638aab49b14cf0582e201fefe646e7d0f65"
    assert enrich["results_count"] == len(data["processed_source_keys"]) == len(data["provider_response_sha256"]) == 17
    assert len(set(data["processed_source_keys"])) == 17
    assert data["review"]["review_state"] == "EVIDENCE_CAPTURED_REVIEW_REQUIRED"
    assert data["review"]["terminal_decision_allowed"] is False
    assert data["mapping_effect"] == {"terminal_mappings": 0, "reconcile_required_delta": 0, "effective_reconcile_required": 1404}
    assert data["frontier"] == {"provider_evidence_executed": 47, "identity_review_completed": 20, "identity_review_pending_from_evidence": 27, "unprocessed_in_050_059": 0, "lower_similarity_tail_remaining": 49}
    inv = data["hard_invariants"]
    assert inv["authority_advanced"] is False
    assert inv["h_id_allocations"] == 0
    assert inv["canonical_id_reservations"] == 0
    assert inv["crm_universe_complete"] is False
    assert inv["outbound"] == "CLOSED"
    assert inv["send_allowed"] == 0


def test_next_preserves_authority_and_points_to_independent_review():
    data = json.loads(NEXT.read_text(encoding="utf-8"))
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority_state"]["next_physical_id"] == "H-0691_UNALLOCATED"
    assert data["authority_state"]["crm_universe_complete"] is False
    assert data["authority_state"]["outbound"] == "CLOSED"
    assert data["authority_state"]["send_allowed"] == 0
    p = data["provider_identity_frontier"]
    assert (p["provider_evidence_executed"], p["identity_review_completed"], p["identity_review_pending_from_evidence"], p["unprocessed"]) == (47, 20, 27, 0)
    assert data["mapping_frontier"]["reconcile_required"] == 1404
    assert data["next_route"] == "PIE_050_CAPTURED_27_IDENTITY_REVIEW_THEN_LOWER_49"
    assert data["authority_advance_allowed"] is False
    assert data["canonical_id_allocation_allowed"] is False
    assert data["outbound_allowed"] is False
