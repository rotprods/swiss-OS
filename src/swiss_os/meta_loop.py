"""Bounded COLETTE activation controller.

The controller is side-effect free. It records measurable progress, blocks repeated
no-progress routes/actions, applies activation budgets and asks the MEP planner
for the next safe route. Actual mutations remain bounded WOP waves.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Mapping, Sequence

from .meta_execution import (
    NextPointer,
    PlannerContext,
    Route,
    RouteCandidate,
    RouteStatus,
    plan_next,
)


@dataclass(frozen=True)
class ProgressEvent:
    sequence: int
    wave_id: str
    action_class: str
    route: str
    progress_token: str
    artifact_sha256: str = ""
    closure_state: str = ""

    def validate(self) -> None:
        if self.sequence < 1:
            raise ValueError("event sequence must be positive")
        if not self.wave_id:
            raise ValueError("wave_id is required")
        if not self.action_class:
            raise ValueError("action_class is required")
        if not self.progress_token:
            raise ValueError("progress_token is required")


@dataclass(frozen=True)
class LoopGuardResult:
    triggered: bool
    blocked_route: str | None = None
    repeated_count: int = 0
    reason: str = ""


@dataclass
class ActivationJournal:
    events: list[ProgressEvent] = field(default_factory=list)

    def append(self, event: ProgressEvent) -> None:
        event.validate()
        if self.events and event.sequence <= self.events[-1].sequence:
            raise ValueError("event sequence must be strictly increasing")
        self.events.append(event)

    def latest_progress_token(self) -> str:
        return self.events[-1].progress_token if self.events else ""

    @staticmethod
    def _repetition_result(
        events: Sequence[ProgressEvent],
        *,
        threshold: int,
        label: str,
        blocked_route: str | None,
    ) -> LoopGuardResult:
        if threshold < 1:
            raise ValueError("threshold must be positive")
        if len(events) < threshold:
            return LoopGuardResult(False)
        tail = list(events[-threshold:])
        tokens = {event.progress_token for event in tail}
        artifacts = {event.artifact_sha256 for event in tail if event.artifact_sha256}
        if len(tokens) == 1 and len(artifacts) <= 1:
            return LoopGuardResult(
                triggered=True,
                blocked_route=blocked_route,
                repeated_count=len(tail),
                reason=f"{label} repeated {len(tail)} times without measurable progress",
            )
        return LoopGuardResult(False)

    def route_repetition_without_progress(
        self,
        route: str,
        *,
        threshold: int,
    ) -> LoopGuardResult:
        # Control-plane issue creation is evaluated by its own action guard. It
        # must never block the underlying REPO_ENGINEERING route.
        relevant = [
            event
            for event in self.events
            if event.route == route and event.action_class != "ISSUE_CREATE"
        ]
        return self._repetition_result(
            relevant,
            threshold=threshold,
            label=f"route {route}",
            blocked_route=route,
        )

    def action_repetition_without_progress(
        self,
        action_class: str,
        *,
        threshold: int,
    ) -> LoopGuardResult:
        relevant = [event for event in self.events if event.action_class == action_class]
        route = relevant[-1].route if relevant else None
        return self._repetition_result(
            relevant,
            threshold=threshold,
            label=f"action class {action_class}",
            blocked_route=route or None,
        )

    def as_dict(self) -> dict[str, Any]:
        return {"events": [event.__dict__ for event in self.events]}

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ActivationJournal":
        raw_events = payload.get("events", ())
        if not isinstance(raw_events, Sequence) or isinstance(raw_events, (str, bytes)):
            raise ValueError("journal events must be an array")
        journal = cls()
        for item in raw_events:
            if not isinstance(item, Mapping):
                raise ValueError("journal events must contain only objects")
            journal.append(
                ProgressEvent(
                    sequence=int(item.get("sequence", 0)),
                    wave_id=str(item.get("wave_id", "")),
                    action_class=str(item.get("action_class", "")),
                    route=str(item.get("route", "")),
                    progress_token=str(item.get("progress_token", "")),
                    artifact_sha256=str(item.get("artifact_sha256", "")),
                    closure_state=str(item.get("closure_state", "")),
                )
            )
        return journal


def _blocked_candidate(candidate: RouteCandidate, reason: str) -> RouteCandidate:
    blocked = tuple(
        sorted({*candidate.blocked_capabilities, f"LOOP_GUARD:{candidate.route.value}"})
    )
    return replace(
        candidate,
        status=RouteStatus.BLOCKED,
        blocked_capabilities=blocked,
        reason=reason,
    )


def plan_chained_next(
    context: PlannerContext,
    journal: ActivationJournal,
    *,
    now: datetime | None = None,
) -> tuple[NextPointer, tuple[LoopGuardResult, ...]]:
    """Apply no-progress guards, then emit deterministic durable NEXT."""

    results: list[LoopGuardResult] = []
    routes: list[RouteCandidate] = []
    threshold = context.budget.max_same_action_without_progress

    issue_guard = journal.action_repetition_without_progress(
        "ISSUE_CREATE",
        threshold=threshold,
    )
    if issue_guard.triggered:
        results.append(issue_guard)

    for candidate in context.routes:
        guard = journal.route_repetition_without_progress(
            candidate.route.value,
            threshold=threshold,
        )
        if guard.triggered:
            results.append(guard)
            routes.append(_blocked_candidate(candidate, guard.reason))
        else:
            routes.append(candidate)

    # Engineering remains possible while issue creation is locked.
    if issue_guard.triggered or context.budget.issue_create_locked:
        routes = [
            replace(
                candidate,
                blocked_capabilities=tuple(
                    sorted({*candidate.blocked_capabilities, "ISSUE_CREATE_LOCKED"})
                ),
            )
            if candidate.route == Route.REPO_ENGINEERING
            else candidate
            for candidate in routes
        ]

    pointer = plan_next(replace(context, routes=tuple(routes)), now=now)
    return pointer, tuple(results)
