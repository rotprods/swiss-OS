import json
from pathlib import Path

STATE = Path("docs/state/SSR_RUNTIME_CAPABILITY_2026-08-30.json")


def test_ssr_runtime_boundary_is_fail_closed():
    data = json.loads(STATE.read_text(encoding="utf-8"))
    assert data["parent_git_sha"] == "ff65e9bd79945294accae55536faeb42f3135a16"
    structured = data["structured_acquisition"]
    assert structured["project"] == "dsod-hs"
    assert structured["subscription_key_required_for_all_api_requests"] is True
    assert structured["runtime_subscription_key_present"] is False
    assert structured["live_capture_executed"] is False
    assert structured["state"] == "BLOCKED_PROVIDER_CREDENTIAL_BOUNDARY"
    fallback = data["qualified_fallback"]
    assert fallback["records"] == 2061
    assert fallback["candidate_records"] == 1438
    assert fallback["exact_current_verified"] == 1438
    assert fallback["ssr_1_0_promotion_allowed"] is False


def test_ssr_capability_wave_respects_live_claim_and_safety_locks():
    data = json.loads(STATE.read_text(encoding="utf-8"))
    concurrency = data["concurrency"]
    assert concurrency["overlapping_live_claim_detected"] is True
    assert concurrency["fencing_token"] == 3
    assert concurrency["collision_avoided"] is True
    inv = data["hard_invariants"]
    assert inv == {
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "crm_universe_complete": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "external_irreversible_actions": 0,
    }
    assert data["next_pointer"]["next_route"] == "READ_ONLY_CROSS_PLANE_AUTHORITY_RECONCILIATION_AUDIT"
