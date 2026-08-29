from swiss_os.alias_semantics import validate_alias_semantics
from swiss_os.asr_repair import (
    apply_plan_to_alias_rows,
    plan_phantom_alias_quarantine,
)


def _fixture():
    catalog = [
        {"hotel_id": "H-0610", "canonical_name": "Hôtel Alpe Fleurie", "city": "Villars-sur-Ollon"},
        {"hotel_id": "H-0624", "canonical_name": "Hôtel Le Mont Paisible", "city": "Crans-Montana"},
        {"hotel_id": "H-0629", "canonical_name": "Stiftung Lilienberg Unternehmerforum", "city": "Ermatingen"},
        {"hotel_id": "H-0630", "canonical_name": "Strandhotel Iseltwald", "city": "Iseltwald"},
        {"hotel_id": "H-0656", "canonical_name": "Hotel Murtenhof & Krone", "city": "Murten"},
        {"hotel_id": "H-0639", "canonical_name": "Hotel Alpbach", "city": "Meiringen"},
        {"hotel_id": "H-0638", "canonical_name": "Jugendherberge Seelisberg", "city": "Seelisberg"},
        {"hotel_id": "H-0640", "canonical_name": "Hotel Central Luzern", "city": "Luzern"},
    ]
    aliases = [
        {"alias_hotel_id": "H-0610", "canonical_hotel_id": "H-0656"},
        {"alias_hotel_id": "H-0624", "canonical_hotel_id": "H-0639"},
        {"alias_hotel_id": "H-0629", "canonical_hotel_id": "H-0638"},
        {"alias_hotel_id": "H-0630", "canonical_hotel_id": "H-0640"},
    ]
    resolutions = [
        {"candidate_name": "Hotel Murtenhof & Krone", "candidate_city": "Murten", "notes": "H-0610 superseded"},
        {"candidate_name": "Hotel Alpbach", "candidate_city": "Meiringen", "notes": "H-0624 superseded"},
        {"candidate_name": "Jugendherberge Seelisberg", "candidate_city": "Seelisberg", "notes": "H-0629 superseded"},
        {"candidate_name": "Hotel Central Luzern", "candidate_city": "Luzern", "notes": "H-0630 superseded"},
    ]
    return catalog, aliases, resolutions


def test_issue_89_phantom_aliases_are_canary_eligible():
    catalog, aliases, resolutions = _fixture()
    initial = validate_alias_semantics(catalog, aliases, resolutions)
    assert initial.state == "RECONCILE_REQUIRED"
    assert {v.code for v in initial.violations} == {"ALIAS_IDENTITY_MISMATCH"}

    plan = plan_phantom_alias_quarantine(catalog, aliases, resolutions)
    assert plan.canary_eligible is True
    assert len(plan.actions) == 4
    assert plan.blocked_alias_ids == ()
    assert plan.authority_advanced is False
    assert plan.h_id_allocations == 0
    assert plan.outbound_opened is False
    assert plan.send_allowed == 0

    canary_aliases = apply_plan_to_alias_rows(aliases, plan)
    assert canary_aliases == ()
    repaired = validate_alias_semantics(catalog, canary_aliases, resolutions)
    assert repaired.valid is True


def test_duplicate_target_identity_blocks_automatic_quarantine():
    catalog, aliases, resolutions = _fixture()
    catalog.append(
        {
            "hotel_id": "H-0700",
            "canonical_name": "Hotel Murtenhof & Krone",
            "city": "Murten",
        }
    )
    plan = plan_phantom_alias_quarantine(catalog, aliases, resolutions)
    assert plan.canary_eligible is False
    assert "H-0610" in plan.blocked_alias_ids


def test_missing_resolution_blocks_repair_plan():
    catalog, aliases, resolutions = _fixture()
    plan = plan_phantom_alias_quarantine(catalog, aliases, resolutions[:-1])
    assert plan.canary_eligible is False
    assert "H-0630" in plan.blocked_alias_ids


def test_non_eligible_plan_cannot_be_applied():
    catalog, aliases, resolutions = _fixture()
    plan = plan_phantom_alias_quarantine(catalog, aliases, resolutions[:-1])
    try:
        apply_plan_to_alias_rows(aliases, plan)
    except ValueError as exc:
        assert "not canary eligible" in str(exc)
    else:
        raise AssertionError("expected fail-closed ValueError")
