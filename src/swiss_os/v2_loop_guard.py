from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .v2_kernel import ContractError, stable_digest


class MutationClass(str, Enum):
    READ = "READ"
    REVERSIBLE_WRITE = "REVERSIBLE_WRITE"
    IRREVERSIBLE_CREATE = "IRREVERSIBLE_CREATE"
    IRREVERSIBLE_EXTERNAL = "IRREVERSIBLE_EXTERNAL"


class LoopDecision(str, Enum):
    ALLOW = "ALLOW"
    SUPPRESS_DUPLICATE = "SUPPRESS_DUPLICATE"
    CHANGE_STRATEGY = "CHANGE_STRATEGY"
    STUCK_LOOP = "STUCK_LOOP"


@dataclass(frozen=True)
class MutationAttempt:
    action: str
    target_scope: str
    mutation_class: MutationClass
    idempotency_key: str
    strategy_id: str
    result: str
    durable_object_id: str = ""

    @property
    def identity(self) -> str:
        return stable_digest({
            "action": self.action,
            "target_scope": self.target_scope,
            "mutation_class": self.mutation_class.value,
            "idempotency_key": self.idempotency_key,
        })


class MutationLoopGuard:
    """Prevent repeated create/external mutations and identical stuck strategies.

    The guard is intentionally in-memory at the kernel layer; production callers
    persist attempts as events and rebuild it through replay. It never grants
    authority or external-action permission.
    """

    def __init__(self, *, max_identical_strategy_attempts: int = 3) -> None:
        if isinstance(max_identical_strategy_attempts, bool) or not isinstance(max_identical_strategy_attempts, int):
            raise ContractError("max_identical_strategy_attempts must be an integer")
        if max_identical_strategy_attempts < 1:
            raise ContractError("max_identical_strategy_attempts must be positive")
        self.max_identical_strategy_attempts = max_identical_strategy_attempts
        self._attempts: list[MutationAttempt] = []
        self._durable_by_identity: dict[str, str] = {}

    @property
    def attempts(self) -> tuple[MutationAttempt, ...]:
        return tuple(self._attempts)

    def rebuild(self, attempts: Iterable[MutationAttempt]) -> None:
        self._attempts = []
        self._durable_by_identity = {}
        for attempt in attempts:
            self.record(attempt)

    def assess(
        self,
        *,
        action: str,
        target_scope: str,
        mutation_class: MutationClass,
        idempotency_key: str,
        strategy_id: str,
    ) -> LoopDecision:
        for label, value in (
            ("action", action), ("target_scope", target_scope),
            ("idempotency_key", idempotency_key), ("strategy_id", strategy_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{label} must be non-empty")
        if mutation_class in {MutationClass.IRREVERSIBLE_CREATE, MutationClass.IRREVERSIBLE_EXTERNAL}:
            if idempotency_key.strip().lower() in {"none", "na", "n/a", "unknown"}:
                raise ContractError("irreversible mutation requires a real idempotency key")
        probe = MutationAttempt(action, target_scope, mutation_class, idempotency_key, strategy_id, "PROBE")
        if probe.identity in self._durable_by_identity:
            return LoopDecision.SUPPRESS_DUPLICATE
        identical_strategy_failures = sum(
            1 for attempt in self._attempts
            if attempt.action == action
            and attempt.target_scope == target_scope
            and attempt.strategy_id == strategy_id
            and attempt.result in {"FAIL", "NO_PROGRESS"}
        )
        if identical_strategy_failures >= self.max_identical_strategy_attempts:
            return LoopDecision.STUCK_LOOP
        if identical_strategy_failures == self.max_identical_strategy_attempts - 1:
            return LoopDecision.CHANGE_STRATEGY
        return LoopDecision.ALLOW

    def record(self, attempt: MutationAttempt) -> None:
        decision = self.assess(
            action=attempt.action,
            target_scope=attempt.target_scope,
            mutation_class=attempt.mutation_class,
            idempotency_key=attempt.idempotency_key,
            strategy_id=attempt.strategy_id,
        )
        if decision == LoopDecision.SUPPRESS_DUPLICATE:
            raise ContractError("duplicate irreversible mutation result")
        if decision == LoopDecision.STUCK_LOOP:
            raise ContractError("STUCK_LOOP: maximum identical strategy attempts exceeded")
        self._attempts.append(attempt)
        if attempt.result == "SUCCESS" and attempt.durable_object_id:
            self._durable_by_identity[attempt.identity] = attempt.durable_object_id

    def durable_object(self, attempt: MutationAttempt) -> str | None:
        return self._durable_by_identity.get(attempt.identity)
