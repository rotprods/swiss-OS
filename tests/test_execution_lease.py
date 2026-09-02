from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.wave_lease_guard import evaluate as evaluate_guard
from swiss_os.execution_lease import (
    LEASE_PROJECTION_SCHEMA_VERSION,
    LeaseAdmission,
    LeaseAdmissionKind,
    LeaseRequest,
    acquire_lease,
    evaluate_lease,
    release_lease,
    renew_lease,
)
from swiss_os.meta_execution import ExecutionMode, MetaCapabilities, MetaRoute, choose_meta_route


NOW = datetime(2026, 9, 2, 16, 0, 0, tzinfo=timezone.utc)


def request(*, run: str = "RUN-16", session: str = "SES-16", token: int = 16, parent: str = "main-16", epoch: str = "E4") -> LeaseRequest:
    return LeaseRequest(
        project_id="SWITZERLAND_JOB_OS",
        owner_agent_id="AGENT-1",
        run_id=run,
        session_id=session,
        wave_id="WAVE-16",
        parent_main_sha=parent,
        authority_epoch=epoch,
        fencing_token=token,
    )


class ExecutionLeaseTests(unittest.TestCase):
    def test_acquire_is_deterministic_and_time_bounded(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        duplicate = acquire_lease(request(), NOW, 600)
        self.assertEqual(lease.lease_id, duplicate.lease_id)
        self.assertEqual(lease.idempotency_key, duplicate.idempotency_key)
        self.assertEqual(lease.acquired_at, "2026-09-02T16:00:00Z")
        self.assertEqual(lease.expires_at, "2026-09-02T16:10:00Z")
        self.assertTrue(lease.mutation_allowed)

    def test_foreign_live_lease_forces_read_only_fallback(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        other = request(run="RUN-17", session="SES-17", token=17)
        decision = evaluate_lease(lease, other, NOW)
        self.assertEqual(decision.kind, LeaseAdmissionKind.READ_ONLY_FALLBACK)
        self.assertFalse(decision.writer_allowed)
        self.assertTrue(decision.read_only_fallback)

    def test_same_live_holder_may_renew_idempotently(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        decision = evaluate_lease(lease, request(), NOW)
        self.assertEqual(decision.kind, LeaseAdmissionKind.RENEW_ALLOWED)
        renewed = renew_lease(lease, datetime(2026, 9, 2, 16, 5, tzinfo=timezone.utc), 600)
        self.assertEqual(renewed.lease_id, lease.lease_id)
        self.assertEqual(renewed.expires_at, "2026-09-02T16:15:00Z")

    def test_expired_lease_cannot_be_resurrected_by_same_run(self) -> None:
        lease = acquire_lease(request(), NOW, 60)
        later = datetime(2026, 9, 2, 16, 2, tzinfo=timezone.utc)
        decision = evaluate_lease(lease, request(), later)
        self.assertEqual(decision.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)
        self.assertFalse(decision.writer_allowed)
        with self.assertRaisesRegex(ValueError, "expired lease cannot be renewed"):
            renew_lease(lease, later, 60)

    def test_expired_lease_recovery_requires_new_run_session_and_higher_token(self) -> None:
        lease = acquire_lease(request(), NOW, 60)
        later = datetime(2026, 9, 2, 16, 2, tzinfo=timezone.utc)
        same_token = evaluate_lease(lease, request(run="RUN-17", session="SES-17", token=16), later)
        self.assertEqual(same_token.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)
        recovered = evaluate_lease(lease, request(run="RUN-17", session="SES-17", token=17), later)
        self.assertEqual(recovered.kind, LeaseAdmissionKind.STALE_RECOVERY_ALLOWED)
        self.assertTrue(recovered.writer_allowed)
        self.assertTrue(recovered.stale_recovery)

    def test_canonical_parent_and_authority_mismatch_fail_closed(self) -> None:
        parent = evaluate_lease(None, request(parent="old-main"), NOW, canonical_parent_sha="new-main")
        self.assertEqual(parent.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)
        self.assertFalse(parent.writer_allowed)
        epoch = evaluate_lease(None, request(epoch="OLD"), NOW, canonical_authority_epoch="E4")
        self.assertEqual(epoch.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)
        self.assertFalse(epoch.writer_allowed)

    def test_release_is_terminal_for_same_identity(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        released = release_lease(lease, datetime(2026, 9, 2, 16, 1, tzinfo=timezone.utc), "wave complete")
        self.assertFalse(released.mutation_allowed)
        same = evaluate_lease(released, request(), datetime(2026, 9, 2, 16, 2, tzinfo=timezone.utc))
        self.assertEqual(same.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)
        successor = evaluate_lease(released, request(run="RUN-17", session="SES-17", token=17), datetime(2026, 9, 2, 16, 2, tzinfo=timezone.utc))
        self.assertEqual(successor.kind, LeaseAdmissionKind.ACQUIRE_ALLOWED)

    def test_invalid_ttl_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive integer"):
            acquire_lease(request(), NOW, 0)

    def test_meta_execution_downgrades_mutating_route_when_writer_denied(self) -> None:
        admission = LeaseAdmission(
            kind=LeaseAdmissionKind.READ_ONLY_FALLBACK,
            writer_allowed=False,
            read_only_fallback=True,
            reason="foreign writer live",
            current_lease_id="LEASE-OTHER",
        )
        decision = choose_meta_route(
            MetaCapabilities(
                constrained_db_write=True,
                native_sheets_write=True,
                operational_graph_write=True,
                intelligence_write=True,
                observability_write=True,
                promotion_ready=True,
            ),
            lease_admission=admission,
        )
        self.assertEqual(decision.execution_mode, ExecutionMode.READ_ONLY_RESEARCH)
        self.assertEqual(decision.route, MetaRoute.LEASE_READ_ONLY_FALLBACK)
        self.assertFalse(decision.authority_advance_allowed)
        self.assertFalse(decision.canonical_id_allocation_allowed)
        self.assertFalse(decision.outbound_allowed)
        self.assertIn("EXECUTION_LEASE_READ_ONLY_FALLBACK", decision.hard_blocks)

    def test_meta_execution_keeps_existing_read_only_route_under_foreign_lease(self) -> None:
        admission = LeaseAdmission(
            kind=LeaseAdmissionKind.READ_ONLY_FALLBACK,
            writer_allowed=False,
            read_only_fallback=True,
            reason="foreign writer live",
        )
        decision = choose_meta_route(
            MetaCapabilities(member_directory_evidence=True, web_research=True),
            lease_admission=admission,
        )
        self.assertEqual(decision.execution_mode, ExecutionMode.READ_ONLY_RESEARCH)
        self.assertEqual(decision.route, MetaRoute.MEMBER_DIRECTORY_MANIFEST)

    def test_guard_passes_empty_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current.json"
            path.write_text(json.dumps({
                "schema_version": LEASE_PROJECTION_SCHEMA_VERSION,
                "project_id": "SWITZERLAND_JOB_OS",
                "active_lease": None,
            }))
            ok, receipt = evaluate_guard(path, NOW)
        self.assertTrue(ok)
        self.assertEqual(receipt["status"], "NO_ACTIVE_LEASE")

    def test_guard_rejects_expired_active_projection(self) -> None:
        lease = acquire_lease(request(), NOW, 60)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current.json"
            path.write_text(json.dumps({
                "schema_version": LEASE_PROJECTION_SCHEMA_VERSION,
                "project_id": "SWITZERLAND_JOB_OS",
                "active_lease": lease.as_dict(),
            }))
            ok, receipt = evaluate_guard(path, datetime(2026, 9, 2, 16, 2, tzinfo=timezone.utc))
        self.assertFalse(ok)
        self.assertEqual(receipt["status"], "EXPIRED_ACTIVE_LEASE")
        self.assertTrue(any(str(v).startswith("EXPIRED_ACTIVE_LEASE_REQUIRES_RECOVERY") for v in receipt["violations"]))


if __name__ == "__main__":
    unittest.main()
