from __future__ import annotations

import unittest

from swiss_os.meta_next import NextPointer


BASE = {
    "project": "SWITZERLAND_JOB_OS",
    "generated_at": "2026-08-28T14:00:00+02:00",
    "cycle_id": "META-CYCLE-TEST",
    "parent_git_sha": "a" * 40,
    "authority_epoch": "E4",
    "authority_parent": "V12",
    "execution_mode": "DEGRADED_CANARY",
    "selected_route": "MEMBER_DIRECTORY_MANIFEST",
    "next_route": "SOURCE_SCOPE_RECONCILIATION",
    "goal_id": "G-0500",
    "checkpoint_id": "CRM_UNIVERSE_COMPLETE",
    "graph_impact": "META",
}


class NextPointerTests(unittest.TestCase):
    def test_valid_pointer_defaults_fail_closed(self) -> None:
        pointer = NextPointer.from_mapping(BASE)
        self.assertFalse(pointer.authority_advance_allowed)
        self.assertFalse(pointer.canonical_id_allocation_allowed)
        self.assertFalse(pointer.outbound_allowed)
        self.assertEqual(pointer.validate(), ())

    def test_outbound_cannot_be_pre_authorized(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot pre-authorize outbound"):
            NextPointer.from_mapping({**BASE, "outbound_allowed": True})

    def test_missing_required_field_fails(self) -> None:
        payload = dict(BASE)
        payload["next_route"] = ""
        with self.assertRaisesRegex(ValueError, "next_route"):
            NextPointer.from_mapping(payload)

    def test_unknown_field_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown NEXT pointer keys"):
            NextPointer.from_mapping({**BASE, "mystery": 1})

    def test_graph_impact_is_typed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid graph_impact"):
            NextPointer.from_mapping({**BASE, "graph_impact": "MAYBE"})

    def test_arrays_are_required_for_collection_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "dependencies must be an array"):
            NextPointer.from_mapping({**BASE, "dependencies": "one"})


if __name__ == "__main__":
    unittest.main()
