import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/recovery/PIE050_TOKEN6_STALE_BRANCH_QUARANTINE_2026-08-30.json"
PRECHECK = ROOT / "docs/recovery/PIE050_LOWER49_COMPLETION_PRECHECK_2026-08-30.json"
ACTIVE = ROOT / "docs/state/v2/active-claims.json"
CLAIM5 = ROOT / "docs/state/v2/claims/CLAIM-CRM-PIE050-LOWER49-005.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_stale_token6_branch_is_quarantined_not_promoted():
    art = load(ART)
    precheck = load(PRECHECK)
    active = load(ACTIVE)
    claim5 = load(CLAIM5)

    assert art["schema_version"] == "PIE050-TOKEN6-STALE-BRANCH-QUARANTINE-1.0"
    assert art["authority"] == "RECOVERY_AND_MIGRATION_GUIDANCE_ONLY"
    assert art["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert art["authority_revision_sha256"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"

    stale = art["stale_branch"]
    assert stale["name"] == "state/crm-pie050-close-token5-srr-token6-20260830"
    assert stale["last_observed_head_sha"] == "f00430437a17adec97f73b188ad341dac94a1c32"
    assert stale["merge_base_sha"] == "11a528dd1584b3606fed83356c006065e9785778"
    assert stale["ahead_by"] == 15
    assert stale["behind_by"] == 38
    assert stale["status"] == "DIVERGED_NONAUTHORITATIVE"
    assert stale["merge_allowed"] is False
    assert stale["blind_cherry_pick_allowed"] is False

    assert precheck["expected"]["classification_coverage"] == "49/49"
    reproved = art["superseded_or_reproved_content"]["lower49_exact_classification"]
    assert reproved["state"] == "REPROVED_ON_FRESH_MAIN"
    assert reproved["merge_pr"] == 344
    assert reproved["coverage"] == "49/49"
    assert reproved["terminalized_from_similarity"] == 0

    assert claim5["state"] == "ACTIVE"
    assert claim5["fencing_token"] == 5
    assert [c["claim_id"] for c in active["claims"]] == ["CLAIM-CRM-PIE050-LOWER49-005"]
    assert active["fencing_high_watermark"] == 5
    assert art["active_claim_on_main"]["claim_id"] == claim5["claim_id"]
    assert art["active_claim_on_main"]["fencing_token"] == claim5["fencing_token"]


def test_quarantine_prevents_stale_coordination_overwrite_and_keeps_hard_locks():
    art = load(ART)
    stale_paths = set(art["stale_transition_surfaces_do_not_import"])

    required_protected = {
        "STATE.md",
        "docs/state/NEXT.json",
        "docs/state/NEXT_META_EXECUTION_2026-08-30.json",
        "docs/state/v2/active-claims.json",
        "docs/state/v2/claims/CLAIM-CRM-PIE050-LOWER49-005.json",
        "docs/state/v2/claims/CLAIM-CRM-SRR-SPECIAL-006.json",
        "docs/state/v2/context-pack.json",
        "docs/state/v2/project-state.json",
    }
    assert required_protected <= stale_paths

    transition = art["safe_successor_transition"]
    assert "fresh main" in transition["required_strategy"].lower()
    assert "do not merge or cherry-pick" in transition["required_strategy"].lower()
    assert set(transition["forbidden_effects"]) == {
        "CANONICAL_AUTHORITY_ADVANCE",
        "H_ID_ALLOCATION",
        "CANONICAL_ID_RESERVATION",
        "TERMINAL_MAPPING_FROM_SIMILARITY_OR_DISTINCTNESS",
        "OUTBOUND_OPEN",
        "SEND_ALLOWED_1",
    }

    safety = art["safety"]
    assert safety == {
        "h_0691": "UNALLOCATED",
        "terminal_source_mappings": 657,
        "reconcile_required": 1404,
        "crm_universe_complete": False,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }
    assert art["verify_live_truth_before_execution"] is True
