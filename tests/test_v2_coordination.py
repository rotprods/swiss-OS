import copy
import unittest

from swiss_os.v2_coordination import *

GIT_SHA = "a" * 40
SCOPE_REV = "b" * 64


def event(event_id="EVT-1", idempotency="idem-1", event_type="WORK_STARTED", causation=None):
    payload = {
        "schema_version": "COS-V2-EVENT-1.0",
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": "2026-08-29T21:42:00Z",
        "project_id": "P",
        "agent_id": "A",
        "session_id": "S",
        "workstream_id": "W",
        "objective_id": "O",
        "correlation_id": "C",
        "repo": "owner/repo",
        "main_sha_observed": GIT_SHA,
        "base_sha": GIT_SHA,
        "authority_ceiling": "PREAUTHORITY",
        "summary": "x",
        "next_action": "y",
        "idempotency_key": idempotency,
        "canonical_hotel_mutation_allowed": False,
        "h_id_allocation_allowed": False,
        "outbound_allowed": False,
    }
    if causation is not None:
        payload["causation"] = causation
    return payload


def claim(claim_id="CL-1", scopes=None, semantics=None, token=1, state="ACTIVE"):
    return {
        "schema_version": "COS-V2-CLAIM-1.0",
        "claim_id": claim_id,
        "project_id": "P",
        "agent_id": "A",
        "session_id": "S",
        "workstream_id": "W",
        "objective_id": "O",
        "correlation_id": "C",
        "state": state,
        "claimed_at": "2026-08-29T21:42:00Z",
        "base_sha": GIT_SHA,
        "branch": "branch",
        "resource_scopes": scopes or ["architecture"],
        "semantic_scopes": semantics or ["ARCHITECTURE"],
        "excluded_scopes": ["OUTBOUND"],
        "fencing_token": token,
        "authority_ceiling": "PREAUTHORITY",
        "idempotency_key": claim_id,
    }


class T(unittest.TestCase):
    def test_event(self):
        self.assertEqual(validate_event(event()), ())
        x = event()
        x["outbound_allowed"] = "false"
        self.assertIn("INVALID_OUTBOUND_ALLOWED_BOOLEAN", validate_event(x))
        x = event()
        x["base_sha"] = "b" * 64
        self.assertIn("INVALID_BASE_SHA", validate_event(x))

    def test_claim(self):
        self.assertEqual(validate_claim(claim()), ())
        self.assertIn("INVALID_FENCING_TOKEN", validate_claim(claim(token=0)))
        self.assertIn("INVALID_FENCING_TOKEN", validate_claim(claim(token=True)))

    def test_collision(self):
        self.assertEqual(len(detect_claim_collisions([claim("A"), claim("B")])), 1)
        self.assertEqual(
            detect_claim_collisions(
                [claim("A", ["x"], ["X"]), claim("B", ["y"], ["Y"])]
            ),
            [],
        )

    def test_duplicate_idem(self):
        projection = reduce_coordination(
            [event("E1", "same"), event("E2", "same")], []
        )
        self.assertTrue(
            any(
                value.startswith("DUPLICATE_IDEMPOTENCY_KEY:")
                for value in projection["violations"]
            )
        )

    def test_duplicate_event(self):
        projection = reduce_coordination(
            [event("E1", "i1"), event("E1", "i2")], []
        )
        self.assertIn("DUPLICATE_EVENT_ID:E1", projection["violations"])

    def test_explicit_release_is_event_derived(self):
        released = claim("CL-1", state="RELEASED")
        release_event = event(
            "E-REL", "rel", "CLAIM_RELEASED", causation=["claim:CL-1"]
        )
        projection = reduce_coordination([release_event], [released])
        self.assertEqual(projection["violations"], [])
        self.assertEqual(projection["claim_states"]["CL-1"], "RELEASED")
        self.assertEqual(projection["active_claim_ids"], [])
        self.assertEqual(projection["claim_lifecycle"][0]["binding_mode"], "EXPLICIT_CAUSATION")

    def test_terminal_event_exposes_stale_claim_file(self):
        stale = claim("CL-1", state="ACTIVE")
        release_event = event(
            "E-REL", "rel", "CLAIM_RELEASED", causation=["claim:CL-1"]
        )
        projection = reduce_coordination([release_event], [stale])
        self.assertEqual(projection["claim_states"]["CL-1"], "RELEASED")
        self.assertEqual(projection["active_claim_ids"], [])
        self.assertIn("CLAIM_STATE_DRIFT:CL-1:ACTIVE!=RELEASED", projection["violations"])

    def test_supersession_removes_claim_from_collision_set(self):
        old = claim("OLD", scopes=["same"], semantics=["SAME"], token=1, state="SUPERSEDED")
        new = claim("NEW", scopes=["same"], semantics=["SAME"], token=2, state="ACTIVE")
        supersede = event("E-SUP", "sup", "CLAIM_SUPERSEDED", causation=["claim:OLD"])
        projection = reduce_coordination([supersede], [old, new])
        self.assertEqual(projection["violations"], [])
        self.assertEqual(projection["active_claim_ids"], ["NEW"])
        self.assertEqual(projection["claim_collisions"], [])

    def test_legacy_lifecycle_binding_requires_unique_identity(self):
        released = claim("LEGACY", state="RELEASED")
        legacy_event = event("E-LEGACY", "legacy", "CLAIM_RELEASED")
        projection = reduce_coordination([legacy_event], [released])
        self.assertEqual(projection["violations"], [])
        self.assertEqual(projection["claim_lifecycle"][0]["binding_mode"], "LEGACY_SESSION_IDENTITY")

    def test_legacy_acquire_prefers_exact_claimed_at(self):
        old = claim("OLD", scopes=["same"], semantics=["SAME"], token=3, state="SUPERSEDED")
        old["claimed_at"] = "2026-08-29T21:00:00Z"
        old["session_id"] = "OLD-SESSION"
        current = claim("CURRENT", scopes=["same"], semantics=["SAME"], token=4, state="ACTIVE")
        current["claimed_at"] = "2026-08-29T21:42:00Z"
        current["session_id"] = "CURRENT-SESSION"
        lifecycle_event = event("E-ACQ", "acq", "CLAIM_ACQUIRED")
        lifecycle_event["semantic_scopes"] = ["SAME"]
        lifecycle_event["session_id"] = "CURRENT-SESSION"
        states, bindings, errors = derive_claim_lifecycle([lifecycle_event], [old, current])
        self.assertEqual(errors, [])
        self.assertEqual(states["CURRENT"], "ACTIVE")
        self.assertEqual(bindings[0]["claim_id"], "CURRENT")
        self.assertEqual(bindings[0]["binding_mode"], "LEGACY_LIFECYCLE_TIMESTAMP")

    def test_legacy_release_can_target_predecessor_from_successor_session(self):
        predecessor = claim("PREDECESSOR", scopes=["same"], semantics=["SAME"], token=4, state="RELEASED")
        predecessor["claimed_at"] = "2026-08-29T21:00:00Z"
        predecessor["released_at"] = "2026-08-29T21:42:00Z"
        predecessor["session_id"] = "PREDECESSOR-SESSION"
        successor = claim("SUCCESSOR", scopes=["same"], semantics=["SAME"], token=5, state="ACTIVE")
        successor["claimed_at"] = "2026-08-29T21:41:00Z"
        successor["session_id"] = "SUCCESSOR-SESSION"
        lifecycle_event = event("E-REL", "release", "CLAIM_RELEASED")
        lifecycle_event["semantic_scopes"] = ["SAME"]
        lifecycle_event["session_id"] = "SUCCESSOR-SESSION"
        states, bindings, errors = derive_claim_lifecycle([lifecycle_event], [predecessor, successor])
        self.assertEqual(errors, [])
        self.assertEqual(states["PREDECESSOR"], "RELEASED")
        self.assertEqual(bindings[0]["claim_id"], "PREDECESSOR")
        self.assertEqual(bindings[0]["binding_mode"], "LEGACY_LIFECYCLE_TIMESTAMP")

    def test_legacy_branch_identity_precedes_session(self):
        old = claim("OLD", semantics=["SAME"], token=3, state="SUPERSEDED")
        old["claimed_at"] = "2026-08-29T21:00:00Z"
        old["branch"] = "old-branch"
        old["session_id"] = "S"
        current = claim("CURRENT", semantics=["SAME"], token=4, state="ACTIVE")
        current["claimed_at"] = "2026-08-29T21:10:00Z"
        current["branch"] = "current-branch"
        current["session_id"] = "OTHER"
        lifecycle_event = event("E-ACQ-BRANCH", "branch", "CLAIM_ACQUIRED")
        lifecycle_event["semantic_scopes"] = ["SAME"]
        lifecycle_event["branch"] = "current-branch"
        states, bindings, errors = derive_claim_lifecycle([lifecycle_event], [old, current])
        self.assertEqual(errors, [])
        self.assertEqual(states["CURRENT"], "ACTIVE")
        self.assertEqual(bindings[0]["claim_id"], "CURRENT")
        self.assertEqual(bindings[0]["binding_mode"], "LEGACY_BRANCH_IDENTITY")

    def test_legacy_highest_fencing_token_resolves_successor_session_release(self):
        old = claim("OLD", semantics=["SAME"], token=3, state="SUPERSEDED")
        old["claimed_at"] = "2026-08-29T20:00:00Z"
        old["session_id"] = "OLD"
        current = claim("CURRENT", semantics=["SAME"], token=4, state="RELEASED")
        current["claimed_at"] = "2026-08-29T21:00:00Z"
        current["session_id"] = "CURRENT"
        lifecycle_event = event("E-REL-HIGH", "high", "CLAIM_RELEASED")
        lifecycle_event["semantic_scopes"] = ["SAME"]
        lifecycle_event["session_id"] = "SUCCESSOR"
        states, bindings, errors = derive_claim_lifecycle([lifecycle_event], [old, current])
        self.assertEqual(errors, [])
        self.assertEqual(states["CURRENT"], "RELEASED")
        self.assertEqual(bindings[0]["claim_id"], "CURRENT")
        self.assertEqual(bindings[0]["binding_mode"], "LEGACY_HIGHEST_FENCING_TOKEN")

    def test_legacy_exact_timestamp_tie_fails_closed(self):
        one = claim("ONE", semantics=["SAME"], state="RELEASED")
        two = claim("TWO", semantics=["SAME"], token=2, state="RELEASED")
        one["released_at"] = "2026-08-29T21:42:00Z"
        two["released_at"] = "2026-08-29T21:42:00Z"
        one["session_id"] = "ONE"
        two["session_id"] = "TWO"
        lifecycle_event = event("E-TIE", "tie", "CLAIM_RELEASED")
        lifecycle_event["semantic_scopes"] = ["SAME"]
        lifecycle_event["session_id"] = "THIRD"
        projection = reduce_coordination([lifecycle_event], [one, two])
        self.assertIn("UNBOUND_CLAIM_LIFECYCLE_EVENT:E-TIE:2", projection["violations"])

    def test_legacy_ambiguous_lifecycle_fails_closed(self):
        one = claim("ONE", token=2, state="RELEASED")
        two = claim("TWO", token=2, state="RELEASED")
        one["session_id"] = "ONE"
        two["session_id"] = "TWO"
        one["branch"] = "one"
        two["branch"] = "two"
        legacy_event = event("E-AMB", "amb", "CLAIM_RELEASED")
        legacy_event["session_id"] = "THIRD"
        legacy_event["branch"] = "third"
        projection = reduce_coordination([legacy_event], [one, two])
        self.assertIn("UNBOUND_CLAIM_LIFECYCLE_EVENT:E-AMB:2", projection["violations"])

    def test_unknown_explicit_claim_causation_fails_closed(self):
        lifecycle_event = event("E-UNKNOWN", "unknown", "CLAIM_RELEASED", causation=["claim:MISSING"])
        projection = reduce_coordination([lifecycle_event], [claim("KNOWN")])
        self.assertIn("UNKNOWN_CLAIM_CAUSATION:E-UNKNOWN:MISSING", projection["violations"])

    def test_context_descendant_head_without_scope_drift_is_valid(self):
        projection = reduce_coordination([event()], [claim()])
        pack = build_context_pack(
            project_id="P", base_main_sha=GIT_SHA, authority_revision="A",
            projection=projection, state_refs=[], relevant_paths=["ARCHITECTURE.md"],
            relevant_scope_revision=SCOPE_REV, blockers=[], next_safe_actions=[],
        )
        self.assertEqual(validate_context_pack(
            pack, base_is_ancestor=True,
            current_projection_revision=projection["projection_revision"],
            current_relevant_scope_revision=SCOPE_REV,
            current_authority_revision="A",
        ), ())

    def test_context_rejects_nonancestor_or_relevant_drift(self):
        projection = reduce_coordination([event()], [claim()])
        pack = build_context_pack(
            project_id="P", base_main_sha=GIT_SHA, authority_revision="A",
            projection=projection, state_refs=[], relevant_paths=["ARCHITECTURE.md"],
            relevant_scope_revision=SCOPE_REV, blockers=[], next_safe_actions=[],
        )
        self.assertIn("BASE_NOT_ANCESTOR", validate_context_pack(
            pack, base_is_ancestor=False,
            current_projection_revision=projection["projection_revision"],
            current_relevant_scope_revision=SCOPE_REV,
            current_authority_revision="A",
        ))
        self.assertIn("RELEVANT_SCOPE_DRIFT", validate_context_pack(
            pack, base_is_ancestor=True,
            current_projection_revision=projection["projection_revision"],
            current_relevant_scope_revision="c" * 64,
            current_authority_revision="A",
        ))

    def test_context_tamper_and_authority_drift(self):
        projection = reduce_coordination([event()], [claim()])
        pack = build_context_pack(
            project_id="P", base_main_sha=GIT_SHA, authority_revision="A",
            projection=projection, state_refs=[], relevant_paths=["ARCHITECTURE.md"],
            relevant_scope_revision=SCOPE_REV, blockers=[], next_safe_actions=[],
        )
        tampered = copy.deepcopy(pack)
        tampered["blockers"].append("x")
        errors = validate_context_pack(
            tampered, base_is_ancestor=True,
            current_projection_revision=projection["projection_revision"],
            current_relevant_scope_revision=SCOPE_REV,
            current_authority_revision="B",
        )
        self.assertIn("CONTEXT_PACK_HASH_MISMATCH", errors)
        self.assertIn("STALE_AUTHORITY_REVISION", errors)

    def test_state(self):
        state = {
            "schema_version": "COS-V2-PROJECT-STATE-1.0",
            "project_id": "P", "repo": "r", "main_sha_observed": GIT_SHA,
            "authority_epoch": "E", "authority_revision": "R", "state": "I",
            "current_objective_id": "O", "authority_advanced": False,
            "h_id_allocation_allowed": False, "outbound_allowed": False,
        }
        self.assertEqual(validate_project_state(state), ())
        state["outbound_allowed"] = True
        self.assertIn("V2_ARCHITECTURE_STATE_MUST_NOT_OPEN_OUTBOUND", validate_project_state(state))

    def test_death(self):
        self.assertIn("north_star_ref", death_drill({}))
        state = {
            "north_star_ref": "G", "current_objective_id": "O",
            "main_sha_observed": GIT_SHA, "event_watermark": {"e": 1},
            "projection_revision": "P", "active_claim_ids": [], "open_prs": [],
            "verified_work": [], "unverified_work": [], "blockers": [], "risks": [],
            "next_safe_actions": ["x"], "authority_revision": "A",
        }
        self.assertEqual(death_drill(state), ())

    def test_deterministic(self):
        self.assertEqual(
            reduce_coordination([event()], [claim()])["projection_revision"],
            reduce_coordination([event()], [claim()])["projection_revision"],
        )


if __name__ == "__main__":
    unittest.main()