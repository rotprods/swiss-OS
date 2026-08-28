from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "handoff_frontier_guard.py"
SPEC = importlib.util.spec_from_file_location("handoff_frontier_guard", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HandoffFrontierGuardTests(unittest.TestCase):
    def _root(self, *, next_verified: int = 40, state_verified: int = 40) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "docs" / "state").mkdir(parents=True)

        for sub, cumulative, remaining in ((1, 20, 80), (2, 40, 60)):
            payload = {
                "schema_version": "ECV-RESULT-SUMMARY-1.0",
                "project": "SWITZERLAND_JOB_OS",
                "batch_id": f"SNAP:WORK:0001:SUB:{sub:04d}",
                "cumulative_current_detail_verified": cumulative,
                "remaining_never_verified": remaining,
                "pending_requeue": 0,
                "ecv_packet_sha256": f"{sub:064x}",
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound": "CLOSED",
                "send_allowed": 0,
            }
            (root / "docs" / "state" / f"ECV_BATCH_0001_SUB{sub:04d}_RESULT.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )

        next_payload = {
            "ecv_frontier": {
                "current_detail_verified": next_verified,
                "remaining_unverified": 60,
                "pending_requeue": 0,
                "latest_subbatch_id": "SNAP:WORK:0001:SUB:0002",
                "latest_subbatch_packet_sha256": f"{2:064x}",
            },
            "authority_advance_allowed": False,
            "canonical_id_allocation_allowed": False,
            "outbound_allowed": False,
        }
        (root / "docs" / "state" / "NEXT.json").write_text(json.dumps(next_payload), encoding="utf-8")
        (root / "STATE.md").write_text(
            "\n".join(
                [
                    f"ECV verified frontier             {state_verified} / 100",
                    "ECV remaining never verified      60",
                    "OUTBOUND                        CLOSED",
                    "send_allowed                      0",
                ]
            ),
            encoding="utf-8",
        )
        return root

    def test_accepts_current_frontier(self) -> None:
        self.assertEqual(MODULE.validate_handoff(self._root()), [])

    def test_rejects_stale_next(self) -> None:
        errors = MODULE.validate_handoff(self._root(next_verified=20))
        self.assertTrue(any("current_detail_verified" in error for error in errors))

    def test_rejects_stale_state(self) -> None:
        errors = MODULE.validate_handoff(self._root(state_verified=20))
        self.assertTrue(any("ECV verified frontier=20" in error for error in errors))

    def test_rejects_unsafe_result(self) -> None:
        root = self._root()
        path = root / "docs" / "state" / "ECV_BATCH_0001_SUB0002_RESULT.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["h_id_allocations"] = 1
        path.write_text(json.dumps(payload), encoding="utf-8")
        errors = MODULE.validate_handoff(root)
        self.assertTrue(any("h_id_allocations" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
