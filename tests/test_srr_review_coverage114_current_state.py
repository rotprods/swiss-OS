import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs" / "state"


def load(name: str):
    return json.loads((STATE / name).read_text(encoding="utf-8"))


def test_current_review_coverage_conserves_exact_unresolved_universe():
    coverage = load("SOURCE_RESOLUTION_REVIEW_COVERAGE_114_CURRENT_2026-08-30.json")
    bands = coverage["bands"]
    classification = coverage["classification"]

    assert coverage["current_unresolved_records"] == 1403
    assert bands["ge600000"]["current_unresolved"] == 20
    assert bands["500000_599999"]["current_unresolved"] == 46
    assert bands["350000_499999"]["current_unresolved"] == 48
    assert bands["lt350000"]["current_unresolved"] == 1289
    assert 20 + 46 + 48 + 1289 == 1403

    assert classification["current_review_classified_records"] == 114
    assert classification["new_canonical_preauth"] == 19
    assert classification["distinctness_review_only"] == 93
    assert classification["relationship_unresolved"] == 2
    assert classification["fresh_research_frontier"] == 1289
    assert 19 + 93 + 2 + 1289 == 1403
    assert 114 + 1289 == 1403


def test_coverage_reuses_existing_current_evidence_without_changing_authority():
    coverage = load("SOURCE_RESOLUTION_REVIEW_COVERAGE_114_CURRENT_2026-08-30.json")
    ge1 = load("SRR_CURRENT_IDENTITY_EVIDENCE_GE600_WAVE1_2026-08-30.json")
    ge2 = load("SRR_CURRENT_IDENTITY_EVIDENCE_GE600_WAVE2_2026-08-30.json")
    mid1 = load("SRET_PROVIDER_IDENTITY_050_SUB01_33206402141.json")
    mid2 = load("SRET_PROVIDER_IDENTITY_050_SUB02_33206402141.json")
    mid27 = load("SRET_PROVIDER_IDENTITY_050_REVIEW27_33206402141.json")
    lower5 = load("PIE050_LOWER49_REVIEW_PACKET_05_2026-08-30.json")

    assert ge1["counts"]["reviewed"] == 10
    assert ge1["counts"]["new_canonical_preauth"] == 9
    assert ge1["counts"]["relationship_unresolved"] == 1
    assert ge2["counts"]["reviewed"] == 10
    assert ge2["counts"]["new_canonical_preauth"] == 10
    assert ge2["counts"]["relationship_unresolved"] == 0

    # Historical mid-band was 47 reviewed; FIVE East Wing subsequently
    # terminalized, leaving exactly 46 current unresolved survivors.
    assert mid1["selection"]["processed_items"] == 10
    assert mid2["selection"]["processed_items"] == 10
    assert mid27["summary"]["reviewed"] == 27
    assert 10 + 10 + 27 == 47
    assert "MD-7c70baeb19408c2e971b" in coverage["bands"]["500000_599999"]["already_terminalized_source_keys"]

    # Lower band had 47 ordinary distinctness reviews plus two special
    # relationship cases. Neu-Schönstatt later terminalized; Delta remains.
    assert lower5["reviewed_cumulative"] == 47
    assert lower5["pending_lower49_after"] == 2
    assert set(lower5["pending_special_relationship_keys"]) == {
        "MD-33d867e983644585e4b2",
        "MD-7976c173678dc89c9cf0",
    }
    assert coverage["bands"]["350000_499999"]["relationship_source_keys"] == [
        "MD-7976c173678dc89c9cf0"
    ]

    safety = coverage["safety"]
    assert coverage["mapping_frontier"]["terminal_source_mappings"] == 658
    assert coverage["mapping_frontier"]["reconcile_required"] == 1403
    assert coverage["mapping_frontier"]["authority_effect"] == "NONE"
    assert safety["authority_advanced"] is False
    assert safety["h_id_allocations"] == 0
    assert safety["canonical_id_reservations"] == 0
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0


def test_next_pointer_skips_redundant_mid_band_and_targets_fresh_frontier():
    coverage = load("SOURCE_RESOLUTION_REVIEW_COVERAGE_114_CURRENT_2026-08-30.json")
    nxt = load("NEXT.json")
    meta = load("NEXT_META_EXECUTION_2026-08-30.json")

    expected = "LOW_SIMILARITY_LT350_REVIEW_BATCH_0001"
    assert coverage["next"] == expected
    assert nxt["next_route"] == expected
    assert meta["next_route"] == expected
    assert nxt["review_coverage_frontier"]["fresh_lt350_research_frontier"] == 1289
    assert nxt["authority_advance_allowed"] is False
    assert nxt["canonical_id_allocation_allowed"] is False
    assert nxt["outbound_allowed"] is False
    assert meta["hard_invariants"]["outbound"] == "CLOSED"
    assert meta["hard_invariants"]["send_allowed"] == 0
