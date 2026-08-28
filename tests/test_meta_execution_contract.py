from __future__ import annotations

import json
from pathlib import Path
import unittest

from swiss_os.meta_execution import ExecutionRoute, select_execution_route


ROOT = Path(__file__).resolve().parents[1]


class MetaExecutionContractTests(unittest.TestCase):
    def test_canonical_contract_files_exist(self) -> None:
        for relative in (
            "docs/operations/META_EXECUTION_PROTOCOL.md",
            "schemas/next-pointer.schema.json",
            "config/meta_execution_routes.json",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_agents_is_bound_to_mep_and_next(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for marker in (
            "META_EXECUTION_PROTOCOL.md",
            "COLETTE",
            "NEXT-1.0",
            "RUNTIME_LIMIT_HANDOFF",
            "Do not stop after one wave or PR",
        ):
            self.assertIn(marker, agents)

    def test_mep_has_activation_and_fallback_invariants(self) -> None:
        mep = (ROOT / "docs/operations/META_EXECUTION_PROTOCOL.md").read_text(
            encoding="utf-8"
        )
        for marker in (
            "MEP-2.0",
            "COLETTE loop",
            "Enter the next wave immediately",
            "Meta-PR chaining",
            "NEXT pointer hard invariants",
            "BLOCKED_EXTERNAL_ALL_ROUTES",
            "OUTBOUND = CLOSED",
        ):
            self.assertIn(marker, mep)

    def test_route_registry_is_valid_and_deterministic(self) -> None:
        payload = json.loads(
            (ROOT / "config/meta_execution_routes.json").read_text(encoding="utf-8")
        )
        routes = tuple(ExecutionRoute.from_mapping(item) for item in payload)
        self.assertEqual(len(routes), 7)
        self.assertEqual(len({route.route_id for route in routes}), len(routes))

        selection = select_execution_route(
            routes,
            {
                "discover_swiss_key": False,
                "network": True,
                "valid_api_manifest": False,
                "complete_directory_manifest": False,
                "freeze_eligible_candidate": False,
                "constrained_staging_db": True,
                "staged_unresolved_records": True,
                "web_evidence": True,
                "github_write": True,
                "ci": True,
                "recovery_artifacts": True,
            },
        )
        self.assertIsNotNone(selection.selected)
        self.assertEqual(selection.selected.route_id, "R4_EXACT_CURRENT_ENTITY_RESOLUTION")


if __name__ == "__main__":
    unittest.main()
