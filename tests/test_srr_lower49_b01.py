import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_LOWER49_P1_B01_2026-08-30.json"
STATE = ROOT / "STATE.md"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_lower49_b01_exact_batch_and_fail_closed_safety():
    art = json.loads(ART.read_text(encoding="utf-8"))
    expected = [
        "MD-00447e4a1c8634a7711d","MD-009d9c619a7da469e4cd","MD-0ccac9a0d3b6144a3783",
        "MD-0f8ed600f086c0fdaa04","MD-111c7f5cd4b1f3060482","MD-21303c8f807f932b1609",
        "MD-29671ff37e9eb4c0f842","MD-2f5b900fce66b8f76eef","MD-33afe41aa0273852418b",
        "MD-3d8dd299140519ac9269",
    ]
    assert art["parent_git_sha"] == "aa7b9964acefc5f86548cf618c3d91e3c68edaf7"
    assert art["claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert art["claim"]["fencing_token"] == 6
    assert art["authority"]["materialized_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert art["batch"]["batch_id"] == "L49-P1-B01"
    assert art["batch"]["source_record_keys"] == expected
    decisions = art["decisions"]
    assert [d["source_record_key"] for d in decisions] == expected
    assert _sha(decisions) == art["decisions_sha256"]
    assert all(d["action"] == "NEW_CANONICAL" for d in decisions)
    assert all(d["mapping_state"] == "RECONCILE_REQUIRED" for d in decisions)
    assert all(d["canonical_h_id_reserved"] is False and d["h_id_allocated"] is False for d in decisions)
    assert all(any(e["type"] == "CURRENT_SOURCE_WEB" for e in d["evidence"]) for d in decisions)
    assert all(any(e["type"] == "CANONICAL_COMPARATOR_READBACK" for e in d["evidence"]) for d in decisions)
    assert all(any(e["type"] == "HISTORICAL_CURRENT_DISTINCTNESS_EVIDENCE_ONLY" and e["authority"] == "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY" for e in d["evidence"]) for d in decisions)
    assert art["review_frontier"]["lower49_typed_srr_after"] == 10
    assert art["review_frontier"]["lower49_remaining_after"] == 37
    assert art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"] == 77
    assert art["mapping_effect"] == {"reconcile_required_after": 1403, "reconcile_required_before": 1403, "terminal_mappings_after": 658, "terminal_mappings_before": 658}
    assert art["safety"]["h_0691"] == "UNALLOCATED"
    assert art["safety"]["outbound"] == "CLOSED" and art["safety"]["send_allowed"] == 0
    assert art["safety"]["authority_advanced"] is False
    assert art["safety"]["canonical_id_reservations"] == 0 and art["safety"]["h_id_allocations"] == 0


def test_state_points_to_next_lower49_batch():
    text = STATE.read_text(encoding="utf-8")
    assert "lower49 typed SRR materialized              10 / 47" in text
    assert "cumulative NEW_CANONICAL preauthority         77" in text
    assert "L49-P1-B02" in text
    assert "H-0691 UNALLOCATED" in text
    assert "OUTBOUND                        CLOSED" in text
