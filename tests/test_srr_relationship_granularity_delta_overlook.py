import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_RELATIONSHIP_GRANULARITY_DELTA_OVERLOOK_2026-08-30.json"
NEXT = ROOT / "docs/state/NEXT.json"
PROTOCOL = ROOT / "docs/operations/ENTITY_GRANULARITY_REVIEW_PROTOCOL_1_0.md"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_relationship_granularity_resolves_without_identity_collapse_or_allocation():
    art = json.loads(ART.read_text(encoding="utf-8"))
    nxt = json.loads(NEXT.read_text(encoding="utf-8"))
    assert art["parent_git_sha"] == "a09f8cb722744c8e5c987a05278b8cd5192d9e11"
    assert art["claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert art["claim"]["fencing_token"] == 6
    assert art["authority"]["materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    decisions = art["decisions"]
    assert [d["source_record_key"] for d in decisions] == ["MD-7976c173678dc89c9cf0", "MD-6d39a6c4d43987703b3c"]
    assert _sha(decisions) == art["decisions_sha256"]
    assert all(d["action"] == "NEW_CANONICAL" for d in decisions)
    assert all(d["mapping_state"] == "RECONCILE_REQUIRED" for d in decisions)
    assert all(d["canonical_h_id_reserved"] is False and d["h_id_allocated"] is False for d in decisions)
    by_key = {d["source_record_key"]: d for d in decisions}
    assert by_key["MD-7976c173678dc89c9cf0"]["relationship"]["relation"] == "OPERATED_AS_SUBPROPERTY_OF"
    assert by_key["MD-7976c173678dc89c9cf0"]["relationship"]["parent_hotel_id"] == "H-0220"
    assert by_key["MD-6d39a6c4d43987703b3c"]["relationship"]["relation"] == "COMPONENT_OF_OR_OPERATED_WITHIN"
    assert by_key["MD-6d39a6c4d43987703b3c"]["relationship"]["parent_hotel_id"] == "H-0012"
    assert "H-0201" in by_key["MD-6d39a6c4d43987703b3c"]["suggested_hotel_ids"]
    assert art["counts"]["relationship_granularity_unresolved_after"] == 0
    assert art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 67
    assert art["mapping_effect"]["terminal_mappings_after"] == 658
    assert art["mapping_effect"]["reconcile_required_after"] == 1403
    assert art["safety"]["h_0691"] == "UNALLOCATED"
    assert art["safety"]["outbound"] == "CLOSED" and art["safety"]["send_allowed"] == 0
    assert nxt["next_route"] == "COMPILE_LOWER49_ORDINARY_PREAUTH_MATERIALIZATION_WORKSET"
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound_allowed"] is False


def test_egr_protocol_is_fail_closed_and_relationship_preserving():
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "shared operator" in text.lower()
    assert "never sufficient" in text.lower()
    assert "H-0012 CERVO Mountain Resort" in text
    assert "H-0201 Nomad Lodge by CERVO Mountain Resort" in text
    assert "canonical_id_reservation_from_staging = 0" in text
    assert "OUTBOUND                              = CLOSED" in text
