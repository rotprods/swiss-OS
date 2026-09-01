from __future__ import annotations

import unittest

from swiss_os.v2_coordination import (
    CoordinationError,
    FORWARD_EVENT_SCHEMA,
    LEGACY_EVENT_SCHEMA,
    build_forward_event,
    validate_event,
)

GIT_SHA = "a" * 40


def base_event(event_type: str = "CLAIM_ACQUIRED") -> dict:
    return {
        "schema_version": LEGACY_EVENT_SCHEMA,
        "event_id": "EVT-FORWARD-TEST",
        "event_type": event_type,
        "occurred_at": "2026-09-01T21:39:00Z",
        "project_id": "P",
        "agent_id": "A",
        "session_id": "S",
        "workstream_id": "W",
        "objective_id": "O",
        "correlation_id": "C",
        "repo": "owner/repo",
        "main_sha_observed": GIT_SHA,
        "base_sha": GIT_SHA,
        "authority_ceiling": "COORDINATION_ONLY",
        "summary": "test",
        "next_action": "test next",
        "idempotency_key": "idem",
        "canonical_hotel_mutation_allowed": False,
        "h_id_allocation_allowed": False,
        "outbound_allowed": False,
    }


class ForwardEventContractTests(unittest.TestCase):
    def test_legacy_lifecycle_remains_replayable_without_explicit_claim(self):
        payload = base_event()
        self.assertEqual(payload["schema_version"], LEGACY_EVENT_SCHEMA)
        self.assertEqual(validate_event(payload), ())

    def test_forward_lifecycle_missing_claim_causation_is_rejected(self):
        payload = base_event()
        payload["schema_version"] = FORWARD_EVENT_SCHEMA
        errors = validate_event(payload)
        self.assertIn("INVALID_CAUSATION_ARRAY", errors)
        self.assertIn("MISSING_EXPLICIT_CLAIM_CAUSATION", errors)

    def test_forward_lifecycle_multiple_claim_causations_is_rejected(self):
        payload = base_event()
        payload["schema_version"] = FORWARD_EVENT_SCHEMA
        payload["causation"] = ["claim:CL-1", "claim:CL-2", "issue:426"]
        self.assertIn("AMBIGUOUS_CLAIM_CAUSATION", validate_event(payload))

    def test_forward_lifecycle_exactly_one_claim_causation_passes(self):
        payload = base_event()
        payload["schema_version"] = FORWARD_EVENT_SCHEMA
        payload["causation"] = ["claim:CL-1", "issue:426"]
        self.assertEqual(validate_event(payload), ())

    def test_forward_non_lifecycle_event_does_not_require_claim(self):
        payload = base_event("WORK_STARTED")
        payload["schema_version"] = FORWARD_EVENT_SCHEMA
        self.assertEqual(validate_event(payload), ())

    def test_canonical_builder_forces_forward_schema(self):
        payload = base_event()
        payload["causation"] = ["claim:CL-1"]
        built = build_forward_event(payload)
        self.assertEqual(built["schema_version"], FORWARD_EVENT_SCHEMA)
        self.assertEqual(validate_event(built), ())

    def test_canonical_builder_cannot_emit_invalid_lifecycle_event(self):
        with self.assertRaises(CoordinationError):
            build_forward_event(base_event())


if __name__ == "__main__":
    unittest.main()
