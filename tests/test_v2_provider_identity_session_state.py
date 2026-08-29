import json
from pathlib import Path

from swiss_os.v2_coordination import reduce_coordination, validate_claim, validate_event

ROOT = Path(__file__).resolve().parents[1]
CLAIM_ID = "CLAIM-CRM-PIE050-CAPTURED27-B91D7E"
SESSION_ID = "SES-20260829T222900Z-PIE050-B91D7E"
PROJECTION = "b60e5c938e165659c109a9ef92a0a9cb73c3126b70bea0bb107aceaf2e7b627b"
CONTEXT = "d52dad925a04a27fdac248e419e1ba49f3b6d705c7fc86deee5d520def8eed2b"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_provider_identity_workstream_is_first_class_and_fail_closed():
    claim = load(f"docs/state/v2/claims/{CLAIM_ID}.json")
    assert validate_claim(claim) == ()
    assert claim["state"] == "ACTIVE"
    assert claim["session_id"] == SESSION_ID
    assert claim["fencing_token"] == 2
    assert claim["authority_ceiling"] == "PREAUTH_REVIEW_ONLY_NO_CANONICAL_MUTATION"
    assert "H_ID_ALLOCATION" in claim["excluded_scopes"]
    assert "OUTBOUND_EXECUTION" in claim["excluded_scopes"]

    events = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "docs/state/v2/events").glob("*.json"))]
    claims = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "docs/state/v2/claims").glob("*.json"))]
    assert all(validate_event(event) == () for event in events)
    projection = reduce_coordination(events, claims)
    assert projection["projection_revision"] == PROJECTION
    assert projection["active_claim_ids"] == [CLAIM_ID]
    assert projection["claim_collisions"] == []
    assert projection["event_watermark"]["event_id"] == "EVT-20260829T222902Z-PIE050-WORK-STARTED"

    active = load("docs/state/v2/active-claims.json")
    state = load("docs/state/v2/project-state.json")
    context = load("docs/state/v2/context-pack.json")
    graph = load("docs/state/v2/graph-snapshot.json")
    assert [x["claim_id"] for x in active["claims"]] == [CLAIM_ID]
    assert active["fencing_high_watermark"] == 2
    assert state["projection_revision"] == projection["projection_revision"]
    assert state["context_pack_revision"] == context["context_pack_revision"] == CONTEXT
    assert state["live_frontier"]["provider_evidence_050_059"] == "47/47"
    assert state["live_frontier"]["provider_identity_review_pending"] == 27
    assert state["live_frontier"]["reconcile_required"] == 1404
    assert state["authority_advanced"] is False
    assert state["h_id_allocation_allowed"] is False
    assert state["outbound_allowed"] is False
    assert graph["authority_advanced"] is False
    assert graph["h_id_allocations"] == 0
    assert graph["outbound"] == "CLOSED"
    assert graph["send_allowed"] == 0
