from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from swiss_os.execution_lease import (
    LEASE_PROJECTION_SCHEMA_VERSION,
    LeaseAdmissionKind,
    LeaseProjection,
    LeaseRequest,
    LeaseState,
    acquire_lease,
    empty_projection,
    evaluate_lease,
    release_lease,
    renew_lease,
)

NOW = datetime(2026, 9, 12, 18, 45, tzinfo=timezone.utc)


def request(
    *,
    owner: str = "AGENT-A",
    run: str = "RUN-A",
    session: str = "SES-A",
    token: int = 19,
    parent: str = "main-sha",
    epoch: str = "E4",
) -> LeaseRequest:
    return LeaseRequest(
        project_id="SWITZERLAND_JOB_OS",
        owner_agent_id=owner,
        run_id=run,
        session_id=session,
        wave_id="WAVE-A",
        parent_main_sha=parent,
        authority_epoch=epoch,
        fencing_token=token,
    )


class ExecutionLeaseTests(unittest.TestCase):
    def test_acquire_is_deterministic_and_bounded(self) -> None:
        first = acquire_lease(request(), NOW, 600)
        duplicate = acquire_lease(request(), NOW, 600)
        self.assertEqual(first.lease_id, duplicate.lease_id)
        self.assertEqual(first.expires_at, "2026-09-12T18:55:00Z")
        self.assertTrue(first.mutation_allowed)
        self.assertEqual(first.state, LeaseState.ACTIVE)

    def test_foreign_live_lease_forces_read_only(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        other = request(owner="AGENT-B", run="RUN-B", session="SES-B", token=20)
        admission = evaluate_lease(
            lease,
            other,
            NOW,
            canonical_parent_sha="main-sha",
            canonical_authority_epoch="E4",
            fencing_high_watermark=19,
        )
        self.assertEqual(admission.kind, LeaseAdmissionKind.READ_ONLY_FALLBACK)
        self.assertFalse(admission.writer_allowed)
        self.assertTrue(admission.read_only_fallback)

    def test_stale_parent_and_epoch_fail_closed(self) -> None:
        no_lease = None
        stale_parent = evaluate_lease(
            no_lease,
            request(parent="old"),
            NOW,
            canonical_parent_sha="main-sha",
            canonical_authority_epoch="E4",
            fencing_high_watermark=18,
        )
        stale_epoch = evaluate_lease(
            no_lease,
            request(epoch="old"),
            NOW,
            canonical_parent_sha="main-sha",
            canonical_authority_epoch="E4",
            fencing_high_watermark=18,
        )
        self.assertFalse(stale_parent.writer_allowed)
        self.assertFalse(stale_epoch.writer_allowed)

    def test_expired_lease_requires_new_identity_and_higher_token(self) -> None:
        lease = acquire_lease(request(), NOW, 60)
        later = NOW + timedelta(minutes=2)
        same = evaluate_lease(lease, request(), later, fencing_high_watermark=19)
        successor = evaluate_lease(
            lease,
            request(owner="AGENT-B", run="RUN-B", session="SES-B", token=20),
            later,
            fencing_high_watermark=19,
        )
        self.assertEqual(same.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)
        self.assertEqual(successor.kind, LeaseAdmissionKind.STALE_RECOVERY_ALLOWED)
        self.assertTrue(successor.writer_allowed)

    def test_release_is_terminal_and_watermark_survives_projection(self) -> None:
        lease = acquire_lease(request(), NOW, 600)
        released = release_lease(lease, NOW + timedelta(minutes=1), "wave complete")
        projection = LeaseProjection(
            project_id="SWITZERLAND_JOB_OS",
            generation=3,
            fencing_high_watermark=19,
            active_lease=None,
            last_lease=released,
            last_transition={"kind": "RELEASE"},
        )
        round_trip = LeaseProjection.from_mapping(projection.as_dict())
        self.assertEqual(round_trip.fencing_high_watermark, 19)
        self.assertEqual(round_trip.last_lease.state, LeaseState.RELEASED)
        reused = evaluate_lease(
            round_trip.last_lease,
            request(owner="AGENT-B", run="RUN-B", session="SES-B", token=19),
            NOW + timedelta(minutes=2),
            fencing_high_watermark=round_trip.fencing_high_watermark,
        )
        self.assertFalse(reused.writer_allowed)

    def test_projection_rejects_watermark_behind_active_token(self) -> None:
        lease = acquire_lease(request(token=19), NOW, 600)
        payload = {
            "schema_version": LEASE_PROJECTION_SCHEMA_VERSION,
            "project_id": "SWITZERLAND_JOB_OS",
            "generation": 1,
            "fencing_high_watermark": 18,
            "active_lease": lease.as_dict(),
            "last_lease": None,
            "last_transition": {},
        }
        with self.assertRaisesRegex(ValueError, "watermark"):
            LeaseProjection.from_mapping(payload)

    def test_renew_rejects_expired_lease(self) -> None:
        lease = acquire_lease(request(), NOW, 60)
        with self.assertRaisesRegex(ValueError, "expired lease"):
            renew_lease(lease, NOW + timedelta(minutes=2), 60)

    def test_empty_projection_preserves_prior_watermark(self) -> None:
        projection = empty_projection("SWITZERLAND_JOB_OS", fencing_high_watermark=18)
        self.assertEqual(projection.fencing_high_watermark, 18)
        self.assertIsNone(projection.active_lease)


if __name__ == "__main__":
    unittest.main()
