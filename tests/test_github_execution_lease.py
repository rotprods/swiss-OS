from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from swiss_os.execution_lease import (
    LeaseAdmissionKind,
    LeaseProjection,
    LeaseRequest,
    acquire_lease,
    empty_projection,
)
from swiss_os.github_execution_lease import (
    LeaseStoreConflict,
    StoredProjection,
    acquire_atomic,
    release_atomic,
)

NOW = datetime(2026, 9, 12, 18, 45, tzinfo=timezone.utc)
MAIN = "21dff74b7518bb623a7bef4ce2ab4b464348a0f3"
EPOCH = "HS_ENTITY_EPOCH_2026-08-25_E4"


def request(
    *,
    owner: str = "AGENT-A",
    run: str = "RUN-A",
    session: str = "SES-A",
    wave: str = "WAVE-A",
    token: int = 19,
    parent: str = MAIN,
    epoch: str = EPOCH,
) -> LeaseRequest:
    return LeaseRequest(
        project_id="SWITZERLAND_JOB_OS",
        owner_agent_id=owner,
        run_id=run,
        session_id=session,
        wave_id=wave,
        parent_main_sha=parent,
        authority_epoch=epoch,
        fencing_token=token,
    )


class FakeCASStore:
    def __init__(self, projection: LeaseProjection):
        self.projection = projection
        self.blob_sha = "sha-0"
        self.writes = 0

    def read(self) -> StoredProjection:
        return StoredProjection(self.projection, self.blob_sha)

    def compare_and_swap(
        self,
        expected_blob_sha: str,
        projection: LeaseProjection,
        message: str,
    ) -> StoredProjection:
        if expected_blob_sha != self.blob_sha:
            raise LeaseStoreConflict("stale sha")
        self.writes += 1
        self.projection = projection
        self.blob_sha = f"sha-{self.writes}"
        return StoredProjection(self.projection, self.blob_sha)


class InjectedRaceStore(FakeCASStore):
    """Lets a foreign contender win immediately before caller's CAS."""

    def __init__(self, projection: LeaseProjection, foreign: LeaseRequest):
        super().__init__(projection)
        self.foreign = foreign
        self.injected = False

    def compare_and_swap(
        self,
        expected_blob_sha: str,
        projection: LeaseProjection,
        message: str,
    ) -> StoredProjection:
        if not self.injected:
            self.injected = True
            lease = acquire_lease(self.foreign, NOW, 1800)
            self.projection = LeaseProjection(
                project_id=self.projection.project_id,
                generation=self.projection.generation + 1,
                fencing_high_watermark=self.foreign.fencing_token,
                active_lease=lease,
                last_lease=self.projection.last_lease,
                last_transition={"kind": "ACQUIRE", "winner": "foreign"},
            )
            self.writes += 1
            self.blob_sha = f"sha-{self.writes}"
        if expected_blob_sha != self.blob_sha:
            raise LeaseStoreConflict("stale sha")
        return super().compare_and_swap(expected_blob_sha, projection, message)


class GitHubExecutionLeaseTests(unittest.TestCase):
    def test_first_contender_commits_and_second_is_read_only(self) -> None:
        store = FakeCASStore(empty_projection("SWITZERLAND_JOB_OS", fencing_high_watermark=18))
        first = acquire_atomic(
            store,
            request(),
            NOW,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertTrue(first.committed)
        self.assertEqual(store.projection.fencing_high_watermark, 19)

        second = acquire_atomic(
            store,
            request(owner="AGENT-B", run="RUN-B", session="SES-B", wave="WAVE-B", token=20),
            NOW + timedelta(seconds=1),
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertFalse(second.committed)
        self.assertEqual(second.admission.kind, LeaseAdmissionKind.READ_ONLY_FALLBACK)
        self.assertTrue(second.admission.read_only_fallback)
        self.assertEqual(store.projection.active_lease.owner_agent_id, "AGENT-A")

    def test_same_snapshot_race_has_exactly_one_cas_winner(self) -> None:
        foreign = request(owner="AGENT-B", run="RUN-B", session="SES-B", wave="WAVE-B", token=19)
        store = InjectedRaceStore(
            empty_projection("SWITZERLAND_JOB_OS", fencing_high_watermark=18),
            foreign,
        )
        ours = acquire_atomic(
            store,
            request(),
            NOW,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertFalse(ours.committed)
        self.assertTrue(ours.admission.cas_conflict)
        self.assertFalse(ours.admission.writer_allowed)
        self.assertEqual(store.projection.active_lease.owner_agent_id, "AGENT-B")
        self.assertEqual(store.projection.fencing_high_watermark, 19)

    def test_release_preserves_watermark_and_same_token_cannot_reenter(self) -> None:
        store = FakeCASStore(empty_projection("SWITZERLAND_JOB_OS", fencing_high_watermark=18))
        holder = request()
        acquired = acquire_atomic(
            store,
            holder,
            NOW,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertTrue(acquired.committed)
        released = release_atomic(store, holder, NOW + timedelta(minutes=1), "complete")
        self.assertTrue(released.committed)
        self.assertIsNone(store.projection.active_lease)
        self.assertEqual(store.projection.fencing_high_watermark, 19)
        self.assertEqual(store.projection.last_lease.fencing_token, 19)

        reused = acquire_atomic(
            store,
            request(owner="AGENT-B", run="RUN-B", session="SES-B", wave="WAVE-B", token=19),
            NOW + timedelta(minutes=2),
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertFalse(reused.committed)
        self.assertEqual(reused.admission.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)

        successor = acquire_atomic(
            store,
            request(owner="AGENT-B", run="RUN-B", session="SES-B", wave="WAVE-B", token=20),
            NOW + timedelta(minutes=2),
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertTrue(successor.committed)
        self.assertEqual(store.projection.fencing_high_watermark, 20)

    def test_stale_parent_and_epoch_never_reach_cas(self) -> None:
        store = FakeCASStore(empty_projection("SWITZERLAND_JOB_OS", fencing_high_watermark=18))
        stale_parent = acquire_atomic(
            store,
            request(parent="old-main"),
            NOW,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        stale_epoch = acquire_atomic(
            store,
            request(epoch="OLD"),
            NOW,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertFalse(stale_parent.committed)
        self.assertFalse(stale_epoch.committed)
        self.assertEqual(store.writes, 0)

    def test_expired_takeover_requires_new_identity_and_higher_token(self) -> None:
        lease = acquire_lease(request(), NOW, 60)
        store = FakeCASStore(
            LeaseProjection(
                project_id="SWITZERLAND_JOB_OS",
                generation=1,
                fencing_high_watermark=19,
                active_lease=lease,
                last_lease=None,
                last_transition={"kind": "ACQUIRE"},
            )
        )
        later = NOW + timedelta(minutes=2)

        same_holder = acquire_atomic(
            store,
            request(),
            later,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertFalse(same_holder.committed)
        self.assertEqual(same_holder.admission.kind, LeaseAdmissionKind.RECOVERY_REQUIRED)

        stale_token = acquire_atomic(
            store,
            request(owner="AGENT-B", run="RUN-B", session="SES-B", wave="WAVE-B", token=19),
            later,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertFalse(stale_token.committed)

        takeover = acquire_atomic(
            store,
            request(owner="AGENT-B", run="RUN-B", session="SES-B", wave="WAVE-B", token=20),
            later,
            1800,
            canonical_parent_sha=MAIN,
            canonical_authority_epoch=EPOCH,
        )
        self.assertTrue(takeover.committed)
        self.assertEqual(store.projection.active_lease.fencing_token, 20)
        self.assertEqual(store.projection.fencing_high_watermark, 20)


if __name__ == "__main__":
    unittest.main()
