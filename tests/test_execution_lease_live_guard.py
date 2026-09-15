from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from scripts import execution_lease_live_guard as guard
from swiss_os.execution_lease import LeaseProjection, LeaseRequest, acquire_lease, empty_projection
from swiss_os.github_execution_lease import StoredProjection

NOW = datetime(2026, 9, 13, 18, 5, tzinfo=timezone.utc)


def request(token: int = 23, parent: str = "main-sha") -> LeaseRequest:
    return LeaseRequest(
        project_id="SWITZERLAND_JOB_OS",
        owner_agent_id="AGENT-GPT56SOL-CONVERGENCE-023",
        run_id="RUN-20260913-180300-terminalization-parity",
        session_id="SES-20260913T180300Z-CONVERGENCE-023",
        wave_id="WAVE-20260913-CONVERGENCE-TERMINALIZATION-005",
        parent_main_sha=parent,
        authority_epoch="E4",
        fencing_token=token,
    )


def claim(token: int = 23, parent: str = "main-sha") -> dict[str, object]:
    return {
        "claim_id": "CLAIM-CONVERGENCE-TERMINALIZATION-023",
        "agent_id": "AGENT-GPT56SOL-CONVERGENCE-023",
        "session_id": "SES-20260913T180300Z-CONVERGENCE-023",
        "base_sha": parent,
        "fencing_token": token,
        "state": "ACTIVE",
        "preconditions": {"authority_epoch": "E4"},
    }


class FakeStore:
    def __init__(self, stored: StoredProjection):
        self.stored = stored

    def read(self) -> StoredProjection:
        return self.stored


class ExecutionLeaseLiveGuardTests(unittest.TestCase):
    def evaluate_with(self, active_claims, projection, *, canonical_main="main-sha"):
        stored = StoredProjection(projection=projection, blob_sha="blob-sha")
        with patch.object(guard, "active_claims", return_value=active_claims), patch.object(
            guard, "GitHubContentsLeaseStore", return_value=FakeStore(stored)
        ):
            return guard.evaluate(
                NOW,
                repo="rotprods/swiss-OS",
                token="test-token",
                canonical_main=canonical_main,
            )

    def test_no_active_claim_rejects_orphan_global_lease(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        projection = LeaseProjection(
            project_id="SWITZERLAND_JOB_OS",
            generation=11,
            fencing_high_watermark=23,
            active_lease=lease,
            last_lease=None,
            last_transition={"kind": "ACQUIRE"},
        )
        ok, receipt = self.evaluate_with([], projection)
        self.assertFalse(ok)
        self.assertFalse(receipt["pass"])
        self.assertEqual(receipt["status"], "NO_ACTIVE_CLAIM")
        self.assertIn("GLOBAL_LEASE_WITHOUT_ACTIVE_CLAIM", "\n".join(receipt["violations"]))

    def test_no_active_claim_accepts_released_writer_slot(self) -> None:
        projection = empty_projection("SWITZERLAND_JOB_OS", fencing_high_watermark=23)
        ok, receipt = self.evaluate_with([], projection)
        self.assertTrue(ok)
        self.assertTrue(receipt["pass"])
        self.assertIsNone(receipt["lease"])
        self.assertEqual(receipt["status"], "NO_ACTIVE_CLAIM")

    def test_zero_claim_state_requires_global_lease_readback(self) -> None:
        with patch.object(guard, "active_claims", return_value=[]):
            ok, receipt = guard.evaluate(
                NOW,
                repo="rotprods/swiss-OS",
                token="",
                canonical_main="main-sha",
            )
        self.assertFalse(ok)
        self.assertFalse(receipt["pass"])
        self.assertEqual(receipt["status"], "NO_ACTIVE_CLAIM_LEASE_UNVERIFIED")
        self.assertIn("LIVE_LEASE_READBACK_REQUIRES_GITHUB_TOKEN", receipt["violations"])

    def test_matching_active_claim_and_lease_still_pass(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        projection = LeaseProjection(
            project_id="SWITZERLAND_JOB_OS",
            generation=11,
            fencing_high_watermark=23,
            active_lease=lease,
            last_lease=None,
            last_transition={"kind": "ACQUIRE"},
        )
        ok, receipt = self.evaluate_with([claim()], projection)
        self.assertTrue(ok)
        self.assertTrue(receipt["pass"])
        self.assertEqual(receipt["status"], "LIVE_LEASE_REQUIRED")
        self.assertEqual(receipt["lease"]["fencing_token"], 23)

    def test_token19_plus_requires_canonical_main_sha(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        projection = LeaseProjection(
            project_id="SWITZERLAND_JOB_OS",
            generation=11,
            fencing_high_watermark=23,
            active_lease=lease,
            last_lease=None,
            last_transition={"kind": "ACQUIRE"},
        )
        ok, receipt = self.evaluate_with([claim()], projection, canonical_main=None)
        self.assertFalse(ok)
        self.assertIn("CANONICAL_MAIN_SHA_REQUIRED_FOR_TOKEN19_PLUS", receipt["violations"])

    def test_self_consistent_but_stale_claim_and_lease_are_rejected(self) -> None:
        lease = acquire_lease(request(parent="old-main"), NOW, 600)
        projection = LeaseProjection(
            project_id="SWITZERLAND_JOB_OS",
            generation=11,
            fencing_high_watermark=23,
            active_lease=lease,
            last_lease=None,
            last_transition={"kind": "ACQUIRE"},
        )
        ok, receipt = self.evaluate_with(
            [claim(parent="old-main")],
            projection,
            canonical_main="new-main",
        )
        self.assertFalse(ok)
        joined = "\n".join(receipt["violations"])
        self.assertIn("ACTIVE_CLAIM_PARENT_STALE:old-main!=new-main", joined)
        self.assertIn("GLOBAL_LEASE_PARENT_STALE:old-main!=new-main", joined)

    def test_current_claim_with_stale_lease_is_rejected(self) -> None:
        lease = acquire_lease(request(parent="old-main"), NOW, 600)
        projection = LeaseProjection(
            project_id="SWITZERLAND_JOB_OS",
            generation=11,
            fencing_high_watermark=23,
            active_lease=lease,
            last_lease=None,
            last_transition={"kind": "ACQUIRE"},
        )
        ok, receipt = self.evaluate_with(
            [claim(parent="main-sha")],
            projection,
            canonical_main="main-sha",
        )
        self.assertFalse(ok)
        joined = "\n".join(receipt["violations"])
        self.assertIn("LEASE_PARENT_MISMATCH:old-main!=main-sha", joined)
        self.assertIn("GLOBAL_LEASE_PARENT_STALE:old-main!=main-sha", joined)


if __name__ == "__main__":
    unittest.main()
