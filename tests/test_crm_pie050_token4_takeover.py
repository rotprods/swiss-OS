import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_crm_takeover_fences_stale_claim_without_authority_advance():
    old = load("docs/state/v2/claims/CLAIM-CRM-PIE050-CAPTURED27-D42F9A.json")
    new = load("docs/state/v2/claims/CLAIM-CRM-PIE050-CAPTURED27-TAKEOVER-004.json")
    active = load("docs/state/v2/active-claims.json")
    state = load("docs/state/v2/project-state.json")
    graph = load("docs/state/v2/graph-snapshot.json")
    assert old["state"] == "SUPERSEDED"
    assert old["fencing_token"] == 3
    assert old["superseded_by_claim_id"] == new["claim_id"]
    assert new["state"] == "ACTIVE"
    assert new["fencing_token"] == 4
    assert active["fencing_high_watermark"] == 4
    assert [c["claim_id"] for c in active["claims"]] == [new["claim_id"]]
    assert active["collisions"] == []
    assert state["authority_advanced"] is False
    assert state["h_id_allocation_allowed"] is False
    assert state["outbound_allowed"] is False
    assert state["live_frontier"]["active_canonical"] == 690
    assert state["live_frontier"]["next_h_id"] == "H-0691 UNALLOCATED"
    assert graph["authority_advanced"] is False
    assert graph["h_id_allocations"] == 0
    assert graph["outbound"] == "CLOSED"
    assert graph["send_allowed"] == 0


def test_takeover_context_and_projection_are_current_and_fail_closed():
    active = load("docs/state/v2/active-claims.json")
    state = load("docs/state/v2/project-state.json")
    pack = load("docs/state/v2/context-pack.json")
    assert active["as_of_main_sha"] == "26be95e927d089b79223482703aaf6ffe37be635"
    assert state["main_sha_observed"] == "26be95e927d089b79223482703aaf6ffe37be635"
    assert pack["base_main_sha"] == "26be95e927d089b79223482703aaf6ffe37be635"
    assert state["projection_revision"] == "2e2d1fc65476260fd475ff815e1347fbf480177dfae1d592ac32537b26e5851f"
    assert pack["projection_revision"] == state["projection_revision"]
    assert pack["active_claim_ids"] == ["CLAIM-CRM-PIE050-CAPTURED27-TAKEOVER-004"]
    assert state["authority_revision"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert pack["authority_revision"] == state["authority_revision"]
    assert any("SSR-1.0" in x for x in state["blockers"])
    assert any("OUTBOUND=CLOSED" in x for x in state["next_safe_actions"])
