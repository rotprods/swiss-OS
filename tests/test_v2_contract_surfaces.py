from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    "GRAPH_REFACTOR_V2.md",
    "ARCHITECTURE.md",
    "TASKS.md",
    "HANDOFF.md",
    "docs/architecture/HYPERGRAPH_ARCHITECTURE_V2.md",
    "docs/architecture/LEXICON_V2.md",
    "docs/audits/GRAPH_REFACTOR_V2_GAUNTLET.md",
    "docs/audits/HISTORICAL_REGRESSION_V2.md",
    "docs/decisions/ADR-0001-HYPERGRAPH-KERNEL.md",
    "docs/decisions/GRAPH_REFACTOR_V2_DECISION_LEDGER.md",
    "docs/operations/GRAPH_REFACTOR_V2_IMPLEMENTATION_PROGRAM.md",
    "docs/graph/v2/canonical_seed.json",
    "docs/state/v2/NEXT.json",
    "docs/state/v2/NEXT_ITERATION_METAPROMPT.md",
    "src/swiss_os/v2_kernel.py",
    "src/swiss_os/v2_loop_guard.py",
    "scripts/compile_graph_v2.py",
    ".github/workflows/graph-v2-guard.yml",
)

STABLE_INDEX_PATHS = (
    "GRAPH_REFACTOR_V2.md",
    "ARCHITECTURE.md",
    "TASKS.md",
    "HANDOFF.md",
)

MUTABLE_OPERATIONAL_PATTERNS = (
    re.compile(r"\bH-\d{4}\b"),
    re.compile(r"\bHS_ENTITY_EPOCH_\d{4}-\d{2}-\d{2}_E\d+\b"),
    re.compile(r"\bOPERATIONAL_DB_SHADOW_MANIFEST_V\d+\b"),
    re.compile(r"\b\d{1,4}\s*/\s*(?:750|1000|2050|2061)\b"),
)


class V2ContractSurfaceTests(unittest.TestCase):
    def test_required_surfaces_exist(self) -> None:
        missing = [path for path in REQUIRED_PATHS if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_stable_indices_do_not_copy_live_frontier(self) -> None:
        violations: list[str] = []
        for relative in STABLE_INDEX_PATHS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for pattern in MUTABLE_OPERATIONAL_PATTERNS:
                match = pattern.search(text)
                if match:
                    violations.append(f"{relative}:{match.group(0)}")
        self.assertEqual(violations, [])

    def test_no_foundation_document_claims_v2_final(self) -> None:
        claims: list[str] = []
        for relative in REQUIRED_PATHS:
            if not relative.endswith(".md"):
                continue
            text = (ROOT / relative).read_text(encoding="utf-8")
            if re.search(r"status\s*:\s*\*\*V2_FINAL\*\*", text, re.I):
                claims.append(relative)
        self.assertEqual(claims, [])

    def test_next_pointer_is_fail_closed(self) -> None:
        payload = json.loads(
            (ROOT / "docs/state/v2/NEXT.json").read_text(encoding="utf-8")
        )
        self.assertTrue(payload["verify_live_truth_before_execution"])
        self.assertFalse(payload["authority_advance_allowed"])
        self.assertFalse(payload["canonical_id_allocation_allowed"])
        self.assertFalse(payload["outbound_allowed"])
        self.assertEqual(payload["send_allowed"], 0)
        self.assertIn("V2-T12", payload["required_tasks"])
        self.assertIn("V2-T16", payload["required_tasks"])

    def test_seed_references_are_closed(self) -> None:
        seed = json.loads(
            (ROOT / "docs/graph/v2/canonical_seed.json").read_text(
                encoding="utf-8"
            )
        )
        engines = set(seed["engines"])
        tests = set(seed["tests"])
        components = {item["id"] for item in seed["components"]}
        self.assertEqual(len(components), len(seed["components"]))
        for component in seed["components"]:
            self.assertIn(component["owner"], engines)
            self.assertIn(component["test"], tests)
        for invariant in seed["invariants"]:
            self.assertIn(invariant["owner"], engines)
            self.assertIn(invariant["test"], tests)
        self.assertFalse(seed["operational_authority_mutated"])
        self.assertEqual(seed["authority_ceiling"], "ARCHITECTURE_ONLY")

    def test_architecture_markers_present(self) -> None:
        architecture = (
            ROOT / "docs/architecture/HYPERGRAPH_ARCHITECTURE_V2.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "Temporal Hypergraph",
            "Session / Claim / Lease",
            "ContextPack",
            "COS 20D",
            "Single-source-of-truth",
            "Security model",
            "Recovery model",
            "OUTBOUND",
        ):
            self.assertIn(marker.lower(), architecture.lower())

    def test_gauntlet_has_bug_family_and_all_gates(self) -> None:
        gauntlet = (
            ROOT / "docs/audits/GRAPH_REFACTOR_V2_GAUNTLET.md"
        ).read_text(encoding="utf-8")
        for gate in range(21):
            self.assertIn(f"G{gate:02d}", gauntlet)
        self.assertIn("BUG-V2-001", gauntlet)
        self.assertIn("MutationLoopGuard", gauntlet)

    def test_program_has_all_checkpoints_and_tasks(self) -> None:
        program = (
            ROOT / "docs/operations/GRAPH_REFACTOR_V2_IMPLEMENTATION_PROGRAM.md"
        ).read_text(encoding="utf-8")
        for checkpoint in range(15):
            self.assertIn(f"CP{checkpoint}", program)
        for task in range(18):
            self.assertIn(f"V2-T{task:02d}", program)

    def test_public_docs_keep_outbound_closed(self) -> None:
        entry = (ROOT / "GRAPH_REFACTOR_V2.md").read_text(encoding="utf-8")
        next_prompt = (
            ROOT / "docs/state/v2/NEXT_ITERATION_METAPROMPT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("OUTBOUND = CLOSED", entry)
        self.assertIn("OUTBOUND = CLOSED", next_prompt)
        self.assertNotIn("OUTBOUND = OPEN", entry + next_prompt)


if __name__ == "__main__":
    unittest.main()
