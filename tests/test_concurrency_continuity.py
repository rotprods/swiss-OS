from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from swiss_os.concurrency import AuthorityFence, ContextPack, ContractError, EventEnvelope, ScopeClaim, ScopeCollisionError, SessionIdentity, StaleWriterError, assert_no_claim_collision, validate_writer

MAIN = "d6c49f158c3691f44868cb9a55a52bc6c6aea225"
PARENT = "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"


def iso(delta=0):
    return (datetime.now(timezone.utc) + timedelta(seconds=delta)).isoformat()


def identity():
    return SessionIdentity.new(project_id="SWITZERLAND_JOB_OS", agent_id="AGT:unittest", workstream_id="WS:graph-v2", objective_id="OBJ:concurrency-kernel")


def fence(token=7, watermark=11, main=MAIN):
    return AuthorityFence(main_sha=main, authority_epoch="HS_ENTITY_EPOCH_2026-08-25_E4", authority_parent_sha256=PARENT, projection_revision="PROJ:657", event_watermark=watermark, fencing_token=token)


def context(i=None, f=None):
    i, f = i or identity(), f or fence()
    return ContextPack(context_pack_id="CTX:test", created_at=iso(), identity=i, authority=f, state_sha256="a" * 64, contract_versions={"MEP": "2.0", "WOP": "1.1", "CCP": "2.0"}, next_safe_actions=("provider-identity-050-remaining",))


def claim(i, *, resource="repo/docs", semantic="source-resolution", mode="WRITE", token=7, delta=60):
    return ScopeClaim(claim_id=f"CLM:{i.session_id}:{resource}:{semantic}", session_id=i.session_id, resource_scope=resource, semantic_scope=semantic, mode=mode, lease_expires_at=iso(delta), fencing_token=token)


class ConcurrencyContinuityTests(unittest.TestCase):
    def test_parallel_disjoint_write_claims_are_allowed(self):
        a, b = identity(), identity()
        ca = claim(a, resource="repo/docs/architecture", semantic="architecture")
        cb = claim(b, resource="repo/docs/state", semantic="provider-review")
        assert_no_claim_collision(cb, [ca], now=iso())

    def test_overlapping_write_claims_fail_closed(self):
        a, b = identity(), identity()
        ca = claim(a, resource="repo/docs/state", semantic="source-resolution")
        cb = claim(b, resource="repo/docs/state/sret", semantic="source-resolution/review")
        with self.assertRaises(ScopeCollisionError):
            assert_no_claim_collision(cb, [ca], now=iso())

    def test_expired_claim_is_stale(self):
        with self.assertRaises(StaleWriterError):
            claim(identity(), delta=-1).validate(iso())

    def test_context_pack_rejects_moved_main(self):
        with self.assertRaises(StaleWriterError):
            context().validate(live_main_sha="0" * 40, live_authority_parent_sha256=PARENT, live_event_watermark=11, live_fencing_token=7)

    def test_context_pack_rejects_event_watermark_drift(self):
        with self.assertRaises(StaleWriterError):
            context().validate(live_main_sha=MAIN, live_authority_parent_sha256=PARENT, live_event_watermark=12, live_fencing_token=7)

    def test_fencing_token_rejects_stale_writer(self):
        i = identity(); ctx = context(i, fence(token=8)); c = claim(i, token=7)
        with self.assertRaises(StaleWriterError):
            validate_writer(claim=c, context=ctx, now=iso(), live_main_sha=MAIN, live_authority_parent_sha256=PARENT, live_event_watermark=11, live_fencing_token=8)

    def test_writer_validation_passes_on_exact_live_fence(self):
        i = identity(); ctx = context(i); c = claim(i)
        validate_writer(claim=c, context=ctx, now=iso(), live_main_sha=MAIN, live_authority_parent_sha256=PARENT, live_event_watermark=11, live_fencing_token=7)

    def test_event_digest_is_deterministic_and_payload_sensitive(self):
        i = identity()
        event = EventEnvelope(event_id="EVT:test-1", event_type="WORK_STARTED", occurred_at="2026-08-29T21:39:00+00:00", identity=i, causation_id=None, authority=fence(), aggregate_type="SESSION", aggregate_id=i.session_id, expected_version=0, payload={"scope": "architecture"})
        event.validate()
        self.assertEqual(event.digest(), event.digest())
        self.assertNotEqual(event.digest(), replace(event, payload={"scope": "other"}).digest())

    def test_material_writer_requires_write_claim(self):
        i = identity(); ctx = context(i); c = claim(i, mode="READ")
        with self.assertRaises(ContractError):
            validate_writer(claim=c, context=ctx, now=iso(), live_main_sha=MAIN, live_authority_parent_sha256=PARENT, live_event_watermark=11, live_fencing_token=7)


if __name__ == "__main__":
    unittest.main()
