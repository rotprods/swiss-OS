"""Concurrency and continuity primitives for SWITZERLAND_JOB_OS.

This module does not replace MEP/WOP or operational authority. It provides
fail-closed identity, scope-claim, fencing, event-envelope and ContextPack
validation so concurrent agents cannot silently write from stale context.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
import uuid
from typing import Iterable, Mapping, Any

_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")


class ContractError(ValueError):
    """A fail-closed contract violation."""


class StaleWriterError(ContractError):
    """Writer no longer owns a valid fence/parent."""


class ScopeCollisionError(ContractError):
    """Two live claims overlap incompatibly."""


def _utc(ts: str) -> datetime:
    value = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ContractError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _canon(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class SessionIdentity:
    project_id: str
    agent_id: str
    session_id: str
    workstream_id: str
    objective_id: str
    correlation_id: str

    @classmethod
    def new(cls, *, project_id: str, agent_id: str, workstream_id: str, objective_id: str) -> "SessionIdentity":
        return cls(project_id, agent_id, f"SES:{uuid.uuid4()}", workstream_id, objective_id, f"COR:{uuid.uuid4()}")

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{name} must be non-empty")
        if not self.session_id.startswith("SES:"):
            raise ContractError("session_id must be globally unique SES:*")
        if not self.correlation_id.startswith("COR:"):
            raise ContractError("correlation_id must be COR:*")


@dataclass(frozen=True)
class AuthorityFence:
    main_sha: str
    authority_epoch: str
    authority_parent_sha256: str
    projection_revision: str
    event_watermark: int
    fencing_token: int

    def validate(self) -> None:
        if not _SHA_RE.fullmatch(self.main_sha):
            raise ContractError("main_sha must be a 40/64-char lowercase hex SHA")
        if not re.fullmatch(r"[0-9a-f]{64}", self.authority_parent_sha256):
            raise ContractError("authority_parent_sha256 must be SHA-256")
        if self.event_watermark < 0 or self.fencing_token < 1:
            raise ContractError("event_watermark >= 0 and fencing_token >= 1 required")
        if not self.authority_epoch or not self.projection_revision:
            raise ContractError("authority epoch and projection revision are required")


@dataclass(frozen=True)
class ScopeClaim:
    claim_id: str
    session_id: str
    resource_scope: str
    semantic_scope: str
    mode: str
    lease_expires_at: str
    fencing_token: int
    state: str = "ACTIVE"

    def validate(self, now: str) -> None:
        if self.mode not in {"READ", "WRITE"}:
            raise ContractError("claim mode must be READ or WRITE")
        if self.state not in {"ACTIVE", "RELEASED", "EXPIRED", "SUPERSEDED"}:
            raise ContractError("invalid claim state")
        if self.fencing_token < 1:
            raise ContractError("fencing_token must be positive")
        if self.state == "ACTIVE" and _utc(self.lease_expires_at) <= _utc(now):
            raise StaleWriterError("active claim lease expired")


def scopes_overlap(a: str, b: str) -> bool:
    aa, bb = a.rstrip("/"), b.rstrip("/")
    return aa == bb or aa.startswith(bb + "/") or bb.startswith(aa + "/")


def assert_no_claim_collision(candidate: ScopeClaim, active_claims: Iterable[ScopeClaim], *, now: str) -> None:
    candidate.validate(now)
    for other in active_claims:
        if other.claim_id == candidate.claim_id or other.state != "ACTIVE":
            continue
        try:
            other.validate(now)
        except StaleWriterError:
            continue
        if candidate.session_id == other.session_id:
            continue
        if candidate.mode == "WRITE" or other.mode == "WRITE":
            if scopes_overlap(candidate.resource_scope, other.resource_scope) and scopes_overlap(candidate.semantic_scope, other.semantic_scope):
                raise ScopeCollisionError(f"claim collision: {candidate.claim_id} overlaps {other.claim_id}")


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    event_type: str
    occurred_at: str
    identity: SessionIdentity
    causation_id: str | None
    authority: AuthorityFence
    aggregate_type: str
    aggregate_id: str
    expected_version: int
    payload: Mapping[str, Any]
    schema_version: str = "EVENT-2.0"

    def validate(self) -> None:
        self.identity.validate(); self.authority.validate(); _utc(self.occurred_at)
        if not self.event_id.startswith("EVT:"):
            raise ContractError("event_id must be EVT:*")
        if self.expected_version < 0:
            raise ContractError("expected_version must be >= 0")
        if not self.event_type or not self.aggregate_type or not self.aggregate_id:
            raise ContractError("event/aggregate identifiers required")
        if not isinstance(self.payload, Mapping):
            raise ContractError("payload must be an object")

    def digest(self) -> str:
        return sha256(_canon(asdict(self)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ContextPack:
    context_pack_id: str
    created_at: str
    identity: SessionIdentity
    authority: AuthorityFence
    state_sha256: str
    contract_versions: Mapping[str, str]
    active_barriers: tuple[str, ...] = ()
    active_claim_ids: tuple[str, ...] = ()
    next_safe_actions: tuple[str, ...] = ()
    schema_version: str = "CONTEXTPACK-2.0"

    def validate(self, *, live_main_sha: str, live_authority_parent_sha256: str, live_event_watermark: int, live_fencing_token: int) -> None:
        self.identity.validate(); self.authority.validate(); _utc(self.created_at)
        if not re.fullmatch(r"[0-9a-f]{64}", self.state_sha256):
            raise ContractError("state_sha256 must be SHA-256")
        if self.authority.main_sha != live_main_sha:
            raise StaleWriterError("ContextPack main SHA is stale")
        if self.authority.authority_parent_sha256 != live_authority_parent_sha256:
            raise StaleWriterError("ContextPack authority parent is stale")
        if self.authority.event_watermark != live_event_watermark:
            raise StaleWriterError("ContextPack event watermark is stale")
        if self.authority.fencing_token != live_fencing_token:
            raise StaleWriterError("ContextPack fencing token is stale")

    def digest(self) -> str:
        return sha256(_canon(asdict(self)).encode("utf-8")).hexdigest()


def validate_writer(*, claim: ScopeClaim, context: ContextPack, now: str, live_main_sha: str, live_authority_parent_sha256: str, live_event_watermark: int, live_fencing_token: int) -> None:
    """Single cognitive barrier immediately before a material mutation."""
    if claim.mode != "WRITE":
        raise ContractError("material mutation requires WRITE claim")
    claim.validate(now)
    if claim.session_id != context.identity.session_id:
        raise ContractError("claim/session mismatch")
    if claim.fencing_token != context.authority.fencing_token:
        raise StaleWriterError("claim fence differs from ContextPack fence")
    context.validate(live_main_sha=live_main_sha, live_authority_parent_sha256=live_authority_parent_sha256, live_event_watermark=live_event_watermark, live_fencing_token=live_fencing_token)
