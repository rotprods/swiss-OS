from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
HANDOFF = ROOT / "docs/state/CRM_CURRENT_META_HANDOFF_33339392661_2026-08-31.json"
NEXT = ROOT / "docs/state/NEXT.json"
META = ROOT / "docs/state/META_GRAPH_CRM_CURRENT_33339392661_2026-08-31.json"
STATE = ROOT / "STATE.md"

PARENT = "02dad1a5bd82219b34430b5fd1cee3ee088642b6"
AUTH = "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
SOURCE_HASH = "b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_payload_hash(data: dict) -> None:
    expected = data.pop("payload_sha256")
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == expected


def test_current_handoff_reconstructs_exact_frontier() -> None:
    data = _load(HANDOFF)
    assert data["parent_git_sha"] == PARENT
    assert data["authority"]["epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority"]["materialized_sha256"] == AUTH
    assert data["authority"]["canonical_rows"] == 690
    assert data["authority"]["next_physical_id"] == "H-0691_UNALLOCATED"
    assert data["current_source"]["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert data["current_source"]["artifact_id"] == 9740219406
    assert data["current_source"]["coverage_complete"] is True
    assert data["current_source"]["records"] == 2061
    assert data["current_source"]["pages"] == 172
    assert data["current_source"]["records_sha256"] == SOURCE_HASH
    assert data["mapping_frontier"]["terminal_source_mappings"] == 658
    assert data["mapping_frontier"]["reconcile_required"] == 1403
    assert data["mapping_frontier"]["terminal_source_mappings"] + data["mapping_frontier"]["reconcile_required"] == 2061
    _verify_payload_hash(data)


def test_next_is_productive_and_fail_closed() -> None:
    data = _load(NEXT)
    assert data["parent_git_sha"] == PARENT
    assert data["authority_epoch"] == "HS_ENTITY_EPOCH_2026-08-25_E4"
    assert data["authority_parent_materialized_sha256"] == AUTH
    assert data["source_frontier"]["snapshot_id"] == "HS-MEMBER-DE-33339392661"
    assert data["source_frontier"]["coverage_complete"] is True
    assert data["mapping_frontier"]["reconcile_required"] == 1403
    assert data["productive_route_available"] is True
    assert data["next_route"] == "CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION"
    assert data["authority_advance_allowed"] is False
    assert data["canonical_id_allocation_allowed"] is False
    assert data["safety"]["h_id_allocations"] == 0
    assert data["safety"]["canonical_id_reservations"] == 0
    assert data["safety"]["outbound"] == "CLOSED"
    assert data["safety"]["send_allowed"] == 0


def test_meta_graph_routes_provider_failure_without_idle() -> None:
    data = _load(META)
    by_id = {node["id"]: node for node in data["nodes"]}
    assert by_id["ROUTE:ENTITY_RESOLUTION_1403"]["state"] == "READY"
    assert by_id["ROUTE:DISCOVER_SSR"]["state"] == "BLOCKED_PROVIDER_CREDENTIAL"
    assert by_id["ROUTE:E4_AUTHORITY_PROMOTION"]["state"] == "BLOCKED_DB_FIRST_EGRESS"
    assert data["safety"]["authority_advanced"] is False
    assert data["safety"]["h_id_allocations"] == 0
    assert data["safety"]["outbound"] == "CLOSED"
    _verify_payload_hash(data)


def test_state_pointer_names_current_source_and_locks() -> None:
    text = STATE.read_text(encoding="utf-8")
    assert "HS-MEMBER-DE-33339392661" in text
    assert "CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION" in text
    assert "H-0691 UNALLOCATED" in text
    assert "OUTBOUND                        CLOSED" in text
    assert "send_allowed                      0" in text
