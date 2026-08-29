import json
from pathlib import Path

from swiss_os.v2_coordination import reduce_coordination, validate_claim, validate_event

ROOT = Path(__file__).resolve().parents[1]
CLAIM = "CLAIM-CRM-PIE050-CAPTURED27-D42F9A"
PROJECTION = "026559a7fa1df4b5f28315bd1169ce016872ac29db8c1d463e44eaca5ec214a3"
CONTEXT = "2e0a20306932d31500c13d960e1811c47cd8ac70268e36fafbdd937c937b4c1f"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_live_provider_domain_is_migrated_under_fenced_v2_claim():
    claim = load(f"docs/state/v2/claims/{CLAIM}.json")
    assert validate_claim(claim) == ()
    assert claim["state"] == "ACTIVE"
    assert claim["fencing_token"] == 3
    assert claim["authority_ceiling"] == "PREAUTH_REVIEW_ONLY_NO_CANONICAL_MUTATION"
    assert {"HOTELS_AUTHORITY_MUTATION","H_ID_ALLOCATION","OUTBOUND_EXECUTION"}.issubset(set(claim["excluded_scopes"]))

    events = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "docs/state/v2/events").glob("*.json"))]
    claims = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "docs/state/v2/claims").glob("*.json"))]
    assert all(validate_event(e) == () for e in events)
    projection = reduce_coordination(events, claims)
    assert projection["projection_revision"] == PROJECTION
    assert projection["active_claim_ids"] == [CLAIM]
    assert projection["claim_collisions"] == []
    assert projection["event_watermark"]["event_id"] == "EVT-20260829T223602Z-PIE050-WORK-STARTED"

    active = load("docs/state/v2/active-claims.json")
    state = load("docs/state/v2/project-state.json")
    context = load("docs/state/v2/context-pack.json")
    graph = load("docs/state/v2/graph-snapshot.json")
    assert active["fencing_high_watermark"] == 3
    assert [x["claim_id"] for x in active["claims"]] == [CLAIM]
    assert state["projection_revision"] == graph["projection_revision"] == PROJECTION
    assert state["context_pack_revision"] == graph["context_pack_revision"] == context["context_pack_revision"] == CONTEXT
    assert state["live_frontier"]["provider_evidence_050_059"] == "47/47"
    assert state["live_frontier"]["provider_identity_review_pending"] == 27
    assert state["live_frontier"]["reconcile_required"] == 1404
    assert state["authority_advanced"] is False
    assert state["h_id_allocation_allowed"] is False
    assert state["outbound_allowed"] is False
    assert graph["h_id_allocations"] == 0
    assert graph["outbound"] == "CLOSED"
    assert graph["send_allowed"] == 0
