import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_review_coverage_reconciles_current_antijoin_without_authority_effect():
    coverage = _load("docs/state/SOURCE_RESOLUTION_REVIEW_COVERAGE_114_33206402141.json")
    anti = _load("docs/state/SOURCE_RESOLUTION_REVIEW_UNRESOLVED_1403_33206402141.json")

    assert anti["anti_join"]["unresolved_candidate_records"] == 1403
    assert anti["review_priority"]["bands"] == {
        "ge600000": 20,
        "500000_599999": 46,
        "350000_499999": 48,
        "lt350000": 1289,
    }

    assert coverage["current_unresolved_records"] == 1403
    assert coverage["bands"]["ge600000"]["current_unresolved"] == 20
    assert coverage["bands"]["500000_599999"]["current_unresolved"] == 46
    assert coverage["bands"]["350000_499999"]["current_unresolved"] == 48
    assert coverage["bands"]["lt350000"]["current_unresolved"] == 1289
    assert coverage["current_review_classified_records"] == 114
    assert coverage["current_distinctness_reviewed_records"] == 113
    assert coverage["current_relationship_only_records"] == 1
    assert coverage["current_low_similarity_unreviewed_records"] == 1289
    assert 114 + 1289 == 1403

    frontier = coverage["mapping_frontier"]
    assert frontier == {
        "authority_effect": "NONE",
        "reconcile_required": 1403,
        "reverse_authority_source_gaps": 34,
        "terminal_source_mappings": 658,
        "unique_canonical_targets": 656,
    }

    guards = coverage["decision_guards"]
    assert guards["similarity_is_authority"] is False
    assert guards["distinctness_is_new_canonical_authority"] is False
    assert guards["relationship_is_identity_collapse"] is False
    assert guards["terminal_decision_allowed_from_this_coverage_artifact"] is False

    safety = coverage["safety"]
    assert safety["authority_advanced"] is False
    assert safety["canonical_id_reservations"] == 0
    assert safety["h_id_allocations"] == 0
    assert safety["h_0691"] == "UNALLOCATED"
    assert safety["crm_universe_complete"] is False
    assert safety["outbound"] == "CLOSED"
    assert safety["send_allowed"] == 0
    assert safety["irreversible_external_actions"] == 0


def test_ge600_historical_identity_review_is_exactly_reusable_for_current_20():
    coverage = _load("docs/state/SOURCE_RESOLUTION_REVIEW_COVERAGE_114_33206402141.json")
    high = _load("docs/state/SRET_HIGH_RISK20_PROVIDER_IDENTITY_33206402141.json")

    assert len(high["items"]) == 20
    assert all(
        item["decision_state"] == "NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED"
        for item in high["items"]
    )
    assert coverage["bands"]["ge600000"]["reviewed"] == 20
    assert coverage["bands"]["ge600000"]["terminal_delta"] == 0


def test_historical_mid_and_lower_review_subtractions_are_explicit_and_nonterminal():
    coverage = _load("docs/state/SOURCE_RESOLUTION_REVIEW_COVERAGE_114_33206402141.json")

    mid = coverage["bands"]["500000_599999"]
    assert mid["historical_queue"] == 47
    assert mid["historical_review_completed"] == 47
    assert mid["already_terminalized_source_keys"] == ["MD-7c70baeb19408c2e971b"]
    assert mid["current_unresolved"] == 46
    assert mid["terminal_delta"] == 0

    lower = coverage["bands"]["350000_499999"]
    assert lower["historical_queue"] == 49
    assert lower["ordinary_nonterminal_distinctness"] == 47
    assert lower["historical_special_relationship_cases"] == 2
    assert lower["already_terminalized_source_keys"] == ["MD-33d867e983644585e4b2"]
    assert lower["relationship_only_source_keys"] == ["MD-7976c173678dc89c9cf0"]
    assert lower["current_unresolved"] == 48
    assert lower["current_distinctness_reviewed"] == 47
    assert lower["current_relationship_only"] == 1
    assert lower["terminal_delta"] == 0


def test_recovery_inputs_referenced_by_coverage_exist():
    coverage = _load("docs/state/SOURCE_RESOLUTION_REVIEW_COVERAGE_114_33206402141.json")
    required = {
        coverage["input_unresolved_antijoin"],
        coverage["bands"]["ge600000"]["evidence_path"],
        coverage["bands"]["ge600000"]["handoff_path"],
        coverage["bands"]["500000_599999"]["queue_path"],
        *coverage["bands"]["500000_599999"]["evidence_paths"],
    }
    assert all((ROOT / path).exists() for path in required)
