import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "docs/state/SRET_PROVIDER_IDENTITY_050_REVIEW27_33206402141.json"


def load():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_review27_closes_bounded_review_without_terminal_or_authority_effect():
    data = load()
    assert data["schema_version"] == "SRET-PIE050-REVIEW27-1.0"
    assert data["parent_main_sha"] == "138578c7fc77aa15dccdae7d19b64139b71f52bd"
    assert data["claim_id"] == "CLAIM-CRM-PIE050-CAPTURED27-TAKEOVER-004"
    assert data["fencing_token"] == 4
    records = data["records"]
    assert len(records) == 27
    assert len({r["key"] for r in records}) == 27
    assert all(r["decision"] == "REVIEWED_NO_TERMINAL_MATCH_PROVEN" for r in records)
    assert all(r["terminal_mapping_effect"] is False for r in records)
    assert all(r["reconcile_required_delta"] == 0 for r in records)
    s = data["summary"]
    assert s["review_pending_before"] == 27
    assert s["review_pending_after"] == 0
    assert s["provider_reviewed_before"] == 20
    assert s["provider_reviewed_after"] == 47
    assert s["terminal_mappings"] == 657
    assert s["reconcile_required"] == 1404
    assert s["authority_advanced"] is False
    assert s["canonical_id_reservations"] == 0
    assert s["h_id_allocations"] == 0
    assert s["next_h_id"] == "H-0691_UNALLOCATED"
    assert s["crm_universe_complete"] is False
    assert s["outbound"] == "CLOSED"
    assert s["send_allowed"] == 0


def test_review27_adversarial_confusables_do_not_collapse_distinct_properties():
    data = load()
    dis = {x["key"]: x for x in data["adversarial_disambiguations"]}
    assert dis["MD-8b6c2242e364c6468f0a"]["result"] == "DISTINCT_PROPERTIES"
    assert "Josefstrasse 13" in " ".join(dis["MD-8b6c2242e364c6468f0a"]["evidence"])
    assert "Hirschengraben 64/68" in " ".join(dis["MD-8b6c2242e364c6468f0a"]["evidence"])
    assert dis["MD-eaa9591c67a4016cf6c4"]["result"] == "DISTINCT_PROPERTIES"
    assert dis["MD-6c3153de9fbb5a337f6f"]["result"] == "NO_SAME_PROPERTY_PROOF"


def test_review27_next_is_lower49_and_requires_fresh_claim():
    data = load()
    nxt = data["next"]
    assert nxt["route"] == "PIE_050_LOWER_49_PROVIDER_IDENTITY"
    assert nxt["required_new_claim"] is True
    assert nxt["authority_ceiling"] == "PREAUTH_REVIEW_ONLY_NO_CANONICAL_MUTATION"
    assert "subscription key" in nxt["blocker"]
    assert data["qa"]["authority_write"] is False
    assert data["qa"]["h_id_reservation"] is False
    assert data["qa"]["outbound"] is False
