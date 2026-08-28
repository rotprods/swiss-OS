from __future__ import annotations

from datetime import datetime, timezone
import unittest

from swiss_os.meta_execution import (
    ActivationBudget,
    PlannerContext,
    Route,
    RouteCandidate,
    RouteScore,
    RouteStatus,
)
from swiss_os.meta_loop import ActivationJournal, ProgressEvent, plan_chained_next


NOW = datetime(2026, 8, 28, 13, 0, tzinfo=timezone.utc)


def route(name: Route, value: int) -> RouteCandidate:
    return RouteCandidate(
        route=name,
        status=RouteStatus.READY,
        safe=True,
        score=RouteScore(
            bottleneck_reduction=value,
            prerequisite_unlock=value,
            capability_fit=100,
            evidence_quality=100,
            reversibility=100,
        ),
        reason=f"execute {name.value}",
    )


def context(*routes: RouteCandidate, budget: ActivationBudget | None = None) -> PlannerContext:
    return PlannerContext(
        project="SWITZERLAND_JOB_OS",
        activation_id="ACT-LOOP",
        last_wave_id="WAVE-LOOP",
        last_closure_state="COMPLETE_READ_ONLY",
        parent_main_sha="d" * 40,
        authority_epoch="E4",
        authority_manifest="V12",
        active_goal_id="G-0500",
        active_checkpoint_id="CP-0750",
        routes=tuple(routes),
        budget=budget or ActivationBudget(max_same_action_without_progress=2),
    )


class ActivationJournalTests(unittest.TestCase):
    def test_sequence_must_be_strictly_increasing(self) -> None:
        journal = ActivationJournal()
        journal.append(ProgressEvent(1, "W1", "DATA", "CACHE_HARVEST", "P1"))
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            journal.append(ProgressEvent(1, "W2", "DATA", "CACHE_HARVEST", "P2"))

    def test_route_repetition_requires_same_progress_token(self) -> None:
        journal = ActivationJournal([
            ProgressEvent(1, "W1", "DATA", "CACHE_HARVEST", "P1"),
            ProgressEvent(2, "W2", "DATA", "CACHE_HARVEST", "P2"),
        ])
        self.assertFalse(journal.route_repetition_without_progress("CACHE_HARVEST", threshold=2).triggered)

    def test_same_route_same_progress_triggers(self) -> None:
        journal = ActivationJournal([
            ProgressEvent(1, "W1", "DATA", "CACHE_HARVEST", "P1"),
            ProgressEvent(2, "W2", "DATA", "CACHE_HARVEST", "P1"),
        ])
        result = journal.route_repetition_without_progress("CACHE_HARVEST", threshold=2)
        self.assertTrue(result.triggered)
        self.assertEqual(result.blocked_route, "CACHE_HARVEST")

    def test_new_artifact_hash_counts_as_progress(self) -> None:
        journal = ActivationJournal([
            ProgressEvent(1, "W1", "DATA", "CACHE_HARVEST", "P1", "a" * 64),
            ProgressEvent(2, "W2", "DATA", "CACHE_HARVEST", "P1", "b" * 64),
        ])
        self.assertFalse(journal.route_repetition_without_progress("CACHE_HARVEST", threshold=2).triggered)

    def test_issue_events_do_not_block_underlying_engineering_route(self) -> None:
        journal = ActivationJournal([
            ProgressEvent(1, "W1", "ISSUE_CREATE", "REPO_ENGINEERING", "same"),
            ProgressEvent(2, "W2", "ISSUE_CREATE", "REPO_ENGINEERING", "same"),
        ])
        self.assertFalse(journal.route_repetition_without_progress("REPO_ENGINEERING", threshold=2).triggered)
        self.assertTrue(journal.action_repetition_without_progress("ISSUE_CREATE", threshold=2).triggered)

    def test_journal_round_trip(self) -> None:
        journal = ActivationJournal()
        journal.append(ProgressEvent(1, "W1", "QA", "REPO_ENGINEERING", "T14"))
        restored = ActivationJournal.from_mapping(journal.as_dict())
        self.assertEqual(restored.events, journal.events)


class ChainedPlannerTests(unittest.TestCase):
    def test_looped_high_value_route_falls_back_to_next_route(self) -> None:
        journal = ActivationJournal([
            ProgressEvent(1, "W1", "DATA", "CACHE_HARVEST", "same"),
            ProgressEvent(2, "W2", "DATA", "CACHE_HARVEST", "same"),
        ])
        pointer, guards = plan_chained_next(
            context(route(Route.CACHE_HARVEST, 100), route(Route.DIRECTORY_MANIFEST, 80)),
            journal,
            now=NOW,
        )
        self.assertEqual(pointer.selected_route, Route.DIRECTORY_MANIFEST.value)
        self.assertTrue(guards)

    def test_issue_create_loop_locks_issue_mutation_not_repo_engineering(self) -> None:
        journal = ActivationJournal([
            ProgressEvent(1, "W1", "ISSUE_CREATE", "REPO_ENGINEERING", "same"),
            ProgressEvent(2, "W2", "ISSUE_CREATE", "REPO_ENGINEERING", "same"),
        ])
        pointer, guards = plan_chained_next(context(route(Route.REPO_ENGINEERING, 90)), journal, now=NOW)
        self.assertEqual(pointer.selected_route, Route.REPO_ENGINEERING.value)
        self.assertIn("ISSUE_CREATE_LOCKED", pointer.blocked_capabilities)
        self.assertTrue(any("ISSUE_CREATE" in result.reason for result in guards))

    def test_budget_issue_lock_is_visible_without_blocking_implementation(self) -> None:
        pointer, _ = plan_chained_next(
            context(route(Route.REPO_ENGINEERING, 90), budget=ActivationBudget(max_new_issues=1, new_issues_used=1)),
            ActivationJournal(),
            now=NOW,
        )
        self.assertTrue(pointer.issue_create_locked)
        self.assertIn("ISSUE_CREATE_LOCKED", pointer.blocked_capabilities)


if __name__ == "__main__":
    unittest.main()
