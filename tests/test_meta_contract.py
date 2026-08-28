from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MetaExecutionContractTests(unittest.TestCase):
    def read(self, path: str) -> str:
        target = ROOT / path
        self.assertTrue(target.exists(), f"missing required MEP contract: {path}")
        return target.read_text(encoding="utf-8")

    def test_required_files_exist(self) -> None:
        for path in (
            "docs/operations/META_EXECUTION_PROTOCOL.md",
            "src/swiss_os/meta_execution.py",
            "src/swiss_os/meta_loop.py",
            "src/swiss_os/meta_cli.py",
            "schemas/meta_next.schema.json",
            "examples/meta_planner_input.example.json",
            "examples/meta_journal.example.json",
        ):
            self.read(path)

    def test_mep_contains_session_level_hard_contracts(self) -> None:
        mep = self.read("docs/operations/META_EXECUTION_PROTOCOL.md")
        for marker in (
            "COLETTE loop",
            "No-idle invariant",
            "SAFE_UNBLOCKED_ROUTE_EXISTS",
            "Durable NEXT pointer",
            "Activation stop conditions",
            "Activation budget",
            "Mutation-loop guard",
            "Execution lease",
            "Git / meta-PR chain",
            "OUTBOUND remains CLOSED",
        ):
            self.assertIn(marker, mep)

    def test_agents_and_wop_reference_mep_and_next(self) -> None:
        agents = self.read("AGENTS.md")
        wop = self.read("docs/operations/WAVE_OPERATING_PROTOCOL.md")
        for text in (agents, wop):
            self.assertIn("META_EXECUTION_PROTOCOL.md", text)
            self.assertIn("NEXT", text)
            self.assertIn("SAFE_UNBLOCKED_ROUTE_EXISTS", text)
            self.assertIn("OUTBOUND", text)

    def test_stable_protocol_does_not_embed_live_hotel_frontier(self) -> None:
        mep = self.read("docs/operations/META_EXECUTION_PROTOCOL.md")
        forbidden = (
            re.compile(r"\bH-\d{4}\b"),
            re.compile(r"\bHS_ENTITY_EPOCH_\d{4}-\d{2}-\d{2}_E\d+\b"),
            re.compile(r"\bSV2-\d{3,}\b"),
            re.compile(r"\b\d{1,4}\s*/\s*(?:750|2050)\b"),
        )
        for pattern in forbidden:
            self.assertIsNone(pattern.search(mep), f"MEP contains mutable state: {pattern.pattern}")

    def test_issue_create_budget_and_loop_guard_are_executable(self) -> None:
        source = self.read("src/swiss_os/meta_execution.py") + self.read("src/swiss_os/meta_loop.py")
        self.assertIn("max_new_issues", source)
        self.assertIn("max_same_action_without_progress", source)
        self.assertIn("ISSUE_CREATE_LOCKED", source)
        self.assertIn("LOOP_GUARD", source)


if __name__ == "__main__":
    unittest.main()
