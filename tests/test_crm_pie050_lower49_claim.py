import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_lower49_claim_fences_completed_token4_and_preserves_authority():
    active = load("docs/state/v2/active-claims.json")
    assert active["fencing_high_watermark"] == 5
    assert len(active["claims"]) == 1
    c = active["claims"][0]
    assert c["claim_id"] == "CLAIM-CRM-PIE050-LOWER49-005"
    assert c["fencing_token"] == 5 and c["state"] == "ACTIVE"
    assert "PIE_050_LOWER_49_PROVIDER_IDENTITY" in c["semantic_scopes"]
    old = load("docs/state/v2/claims/CLAIM-CRM-PIE050-CAPTURED27-TAKEOVER-004.json")
    assert old["state"] == "RELEASED" and old["fencing_token"] == 4
    p = load("docs/state/v2/project-state.json")
    f = p["live_frontier"]
    assert f["provider_identity_review_completed"] == 47
    assert f["provider_identity_review_pending"] == 0
    assert f["lower_similarity_tail"] == 49
    assert f["active_canonical"] == 690
    assert f["terminal_mappings"] == 657
    assert f["reconcile_required"] == 1404
    assert f["next_h_id"] == "H-0691_UNALLOCATED"
    assert p["authority_advanced"] is False
    assert p["h_id_allocation_allowed"] is False
    assert p["outbound_allowed"] is False

def test_next_is_lower49_and_all_mutation_gates_fail_closed():
    n = load("docs/state/NEXT_META_EXECUTION_2026-08-30.json")
    assert n["next_route"] == "PIE_050_LOWER_49_QUEUE_RECONSTRUCTION_AND_PROVIDER_IDENTITY"
    assert n["fencing_token"] == 5
    h = n["hard_invariants"]
    assert h["crm_universe_complete"] is False
    assert h["outbound"] == "CLOSED" and h["send_allowed"] == 0
    assert h["canonical_id_reservations_from_staging"] == 0
    assert h["authority_from_canary_or_cache"] is False
    assert h["irreversible_external_actions"] == 0

def test_context_pack_and_project_state_share_exact_scope_revision():
    c = load("docs/state/v2/context-pack.json")
    p = load("docs/state/v2/project-state.json")
    assert c["base_main_sha"] == p["main_sha_observed"]
    assert c["authority_revision"] == p["authority_revision"]
    assert c["active_claim_ids"] == p["active_claim_ids"] == ["CLAIM-CRM-PIE050-LOWER49-005"]
    assert c["event_watermark"] == p["event_watermark"]
    assert c["projection_revision"] == p["projection_revision"]
