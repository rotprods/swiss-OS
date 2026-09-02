from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json


LEASE_SCHEMA_VERSION = "WAVE-EXECUTION-LEASE-1.0"
LEASE_PROJECTION_SCHEMA_VERSION = "WAVE-EXECUTION-LEASE-PROJECTION-1.0"
DEFAULT_LEASE_STATE_PATH = Path("docs/state/execution-leases/current.json")


class LeaseState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"


class LeaseAdmissionKind(str, Enum):
    ACQUIRE_ALLOWED = "ACQUIRE_ALLOWED"
    RENEW_ALLOWED = "RENEW_ALLOWED"
    STALE_RECOVERY_ALLOWED = "STALE_RECOVERY_ALLOWED"
    READ_ONLY_FALLBACK = "READ_ONLY_FALLBACK"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


def _required_str(payload: Mapping[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamps must use UTC Z form")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"invalid UTC timestamp: {value}") from exc
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("timestamps must be UTC")
    return parsed.astimezone(timezone.utc)


def format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class LeaseRequest:
    project_id: str
    owner_agent_id: str
    run_id: str
    session_id: str
    wave_id: str
    parent_main_sha: str
    authority_epoch: str
    fencing_token: int

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LeaseRequest":
        allowed = {
            "project_id", "owner_agent_id", "run_id", "session_id", "wave_id",
            "parent_main_sha", "authority_epoch", "fencing_token",
        }
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError(f"unknown lease request keys: {', '.join(unknown)}")
        token = payload.get("fencing_token")
        if isinstance(token, bool) or not isinstance(token, int) or token <= 0:
            raise ValueError("fencing_token must be a positive integer")
        return cls(
            project_id=_required_str(payload, "project_id"),
            owner_agent_id=_required_str(payload, "owner_agent_id"),
            run_id=_required_str(payload, "run_id"),
            session_id=_required_str(payload, "session_id"),
            wave_id=_required_str(payload, "wave_id"),
            parent_main_sha=_required_str(payload, "parent_main_sha"),
            authority_epoch=_required_str(payload, "authority_epoch"),
            fencing_token=token,
        )

    @property
    def idempotency_key(self) -> str:
        return "|".join((
            self.project_id, self.wave_id, self.owner_agent_id, self.run_id,
            self.session_id, f"TOKEN{self.fencing_token}",
        ))


@dataclass(frozen=True)
class ExecutionLease:
    schema_version: str
    project_id: str
    lease_id: str
    owner_agent_id: str
    run_id: str
    session_id: str
    wave_id: str
    acquired_at: str
    expires_at: str
    parent_main_sha: str
    authority_epoch: str
    fencing_token: int
    state: LeaseState
    idempotency_key: str
    mutation_allowed: bool
    released_at: str | None = None
    release_reason: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ExecutionLease":
        if payload.get("schema_version") != LEASE_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {LEASE_SCHEMA_VERSION}")
        token = payload.get("fencing_token")
        if isinstance(token, bool) or not isinstance(token, int) or token <= 0:
            raise ValueError("fencing_token must be a positive integer")
        mutation_allowed = payload.get("mutation_allowed")
        if not isinstance(mutation_allowed, bool):
            raise ValueError("mutation_allowed must be a JSON boolean")
        try:
            state = LeaseState(_required_str(payload, "state"))
        except ValueError as exc:
            raise ValueError("state must be ACTIVE or RELEASED") from exc

        acquired_at = _required_str(payload, "acquired_at")
        expires_at = _required_str(payload, "expires_at")
        acquired = parse_utc(acquired_at)
        expires = parse_utc(expires_at)
        if expires <= acquired:
            raise ValueError("expires_at must be later than acquired_at")

        released_at = payload.get("released_at")
        if released_at is not None:
            if not isinstance(released_at, str):
                raise ValueError("released_at must be a UTC timestamp or null")
            if parse_utc(released_at) < acquired:
                raise ValueError("released_at cannot precede acquired_at")
        if state is LeaseState.ACTIVE and released_at is not None:
            raise ValueError("ACTIVE lease cannot have released_at")
        if state is LeaseState.RELEASED and released_at is None:
            raise ValueError("RELEASED lease requires released_at")
        if mutation_allowed != (state is LeaseState.ACTIVE):
            raise ValueError("mutation_allowed must be true only for ACTIVE leases")

        lease = cls(
            schema_version=LEASE_SCHEMA_VERSION,
            project_id=_required_str(payload, "project_id"),
            lease_id=_required_str(payload, "lease_id"),
            owner_agent_id=_required_str(payload, "owner_agent_id"),
            run_id=_required_str(payload, "run_id"),
            session_id=_required_str(payload, "session_id"),
            wave_id=_required_str(payload, "wave_id"),
            acquired_at=acquired_at,
            expires_at=expires_at,
            parent_main_sha=_required_str(payload, "parent_main_sha"),
            authority_epoch=_required_str(payload, "authority_epoch"),
            fencing_token=token,
            state=state,
            idempotency_key=_required_str(payload, "idempotency_key"),
            mutation_allowed=mutation_allowed,
            released_at=released_at,
            release_reason=payload.get("release_reason"),
        )
        request = LeaseRequest(
            project_id=lease.project_id,
            owner_agent_id=lease.owner_agent_id,
            run_id=lease.run_id,
            session_id=lease.session_id,
            wave_id=lease.wave_id,
            parent_main_sha=lease.parent_main_sha,
            authority_epoch=lease.authority_epoch,
            fencing_token=lease.fencing_token,
        )
        if lease.idempotency_key != request.idempotency_key:
            raise ValueError("idempotency_key does not match lease identity")
        if lease.lease_id != lease_id_for_key(request.idempotency_key):
            raise ValueError("lease_id does not match deterministic lease identity")
        return lease

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "lease_id": self.lease_id,
            "owner_agent_id": self.owner_agent_id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "wave_id": self.wave_id,
            "acquired_at": self.acquired_at,
            "expires_at": self.expires_at,
            "parent_main_sha": self.parent_main_sha,
            "authority_epoch": self.authority_epoch,
            "fencing_token": self.fencing_token,
            "state": self.state.value,
            "idempotency_key": self.idempotency_key,
            "mutation_allowed": self.mutation_allowed,
        }
        if self.released_at is not None:
            payload["released_at"] = self.released_at
        if self.release_reason is not None:
            payload["release_reason"] = self.release_reason
        return payload


@dataclass(frozen=True)
class LeaseAdmission:
    kind: LeaseAdmissionKind
    writer_allowed: bool
    read_only_fallback: bool
    reason: str
    current_lease_id: str | None = None
    stale_recovery: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "writer_allowed": self.writer_allowed,
            "read_only_fallback": self.read_only_fallback,
            "reason": self.reason,
            "current_lease_id": self.current_lease_id,
            "stale_recovery": self.stale_recovery,
        }


def lease_id_for_key(idempotency_key: str) -> str:
    return f"LEASE-{sha256(idempotency_key.encode('utf-8')).hexdigest()[:20]}"


def acquire_lease(request: LeaseRequest, now: datetime, ttl_seconds: int) -> ExecutionLease:
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be a positive integer")
    acquired = now.astimezone(timezone.utc).replace(microsecond=0)
    return ExecutionLease(
        schema_version=LEASE_SCHEMA_VERSION,
        project_id=request.project_id,
        lease_id=lease_id_for_key(request.idempotency_key),
        owner_agent_id=request.owner_agent_id,
        run_id=request.run_id,
        session_id=request.session_id,
        wave_id=request.wave_id,
        acquired_at=format_utc(acquired),
        expires_at=format_utc(acquired + timedelta(seconds=ttl_seconds)),
        parent_main_sha=request.parent_main_sha,
        authority_epoch=request.authority_epoch,
        fencing_token=request.fencing_token,
        state=LeaseState.ACTIVE,
        idempotency_key=request.idempotency_key,
        mutation_allowed=True,
    )


def renew_lease(lease: ExecutionLease, now: datetime, ttl_seconds: int) -> ExecutionLease:
    if lease.state is not LeaseState.ACTIVE:
        raise ValueError("only ACTIVE leases can be renewed")
    current = now.astimezone(timezone.utc)
    if current >= parse_utc(lease.expires_at):
        raise ValueError("expired lease cannot be renewed; use a new session and higher fencing token")
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be a positive integer")
    return replace(lease, expires_at=format_utc(current + timedelta(seconds=ttl_seconds)))


def release_lease(lease: ExecutionLease, released_at: datetime, reason: str) -> ExecutionLease:
    if lease.state is LeaseState.RELEASED:
        return lease
    reason = reason.strip()
    if not reason:
        raise ValueError("release reason must be non-empty")
    released = released_at.astimezone(timezone.utc)
    if released < parse_utc(lease.acquired_at):
        raise ValueError("released_at cannot precede acquired_at")
    return replace(
        lease,
        state=LeaseState.RELEASED,
        mutation_allowed=False,
        released_at=format_utc(released),
        release_reason=reason,
    )


def _same_holder(lease: ExecutionLease, request: LeaseRequest) -> bool:
    return (
        lease.project_id == request.project_id
        and lease.owner_agent_id == request.owner_agent_id
        and lease.run_id == request.run_id
        and lease.session_id == request.session_id
        and lease.wave_id == request.wave_id
        and lease.parent_main_sha == request.parent_main_sha
        and lease.authority_epoch == request.authority_epoch
        and lease.fencing_token == request.fencing_token
    )


def evaluate_lease(
    current: ExecutionLease | None,
    request: LeaseRequest | None,
    now: datetime,
    *,
    canonical_parent_sha: str | None = None,
    canonical_authority_epoch: str | None = None,
) -> LeaseAdmission:
    """Evaluate writer admission without replacing fencing or heartbeat authority.

    A foreign live lease always degrades the activation to read-only. An expired
    lease is never resumed by the same run/session: recovery requires a new
    run/session and a strictly higher fencing token.
    """
    now = now.astimezone(timezone.utc)
    if request is not None:
        if canonical_parent_sha is not None and request.parent_main_sha != canonical_parent_sha:
            return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "activation parent SHA is stale relative to canonical main", current.lease_id if current else None)
        if canonical_authority_epoch is not None and request.authority_epoch != canonical_authority_epoch:
            return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "activation authority epoch does not match canonical authority", current.lease_id if current else None)

    if current is None:
        return LeaseAdmission(LeaseAdmissionKind.ACQUIRE_ALLOWED, True, False, "no active execution lease")

    if current.state is LeaseState.RELEASED:
        if request is None:
            return LeaseAdmission(LeaseAdmissionKind.ACQUIRE_ALLOWED, True, False, "previous lease is released", current.lease_id)
        if _same_holder(current, request):
            return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "released lease identity is terminal and cannot be resurrected", current.lease_id)
        if request.fencing_token <= current.fencing_token:
            return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "successor lease requires a higher fencing token", current.lease_id)
        return LeaseAdmission(LeaseAdmissionKind.ACQUIRE_ALLOWED, True, False, "previous lease is released and successor fencing token is higher", current.lease_id)

    if now < parse_utc(current.expires_at):
        if request is not None and _same_holder(current, request):
            return LeaseAdmission(LeaseAdmissionKind.RENEW_ALLOWED, True, False, "same live lease holder may renew idempotently", current.lease_id)
        return LeaseAdmission(LeaseAdmissionKind.READ_ONLY_FALLBACK, False, True, "another writer lease is live; activation must remain read-only", current.lease_id)

    if request is None:
        return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "active lease is expired; recovery requires a new session and higher fencing token", current.lease_id)
    if _same_holder(current, request) or request.session_id == current.session_id or request.run_id == current.run_id:
        return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "expired lease cannot be renewed or resumed by the same run/session", current.lease_id)
    if request.fencing_token <= current.fencing_token:
        return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "stale-lease takeover requires a higher fencing token", current.lease_id)
    return LeaseAdmission(LeaseAdmissionKind.STALE_RECOVERY_ALLOWED, True, False, "expired lease may be recovered by a new run/session with a higher fencing token", current.lease_id, stale_recovery=True)


def load_lease_projection(path: str | Path = DEFAULT_LEASE_STATE_PATH) -> ExecutionLease | None:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("lease projection must be a JSON object")
    if payload.get("schema_version") != LEASE_PROJECTION_SCHEMA_VERSION:
        raise ValueError(f"lease projection schema_version must be {LEASE_PROJECTION_SCHEMA_VERSION}")
    project_id = payload.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise ValueError("lease projection project_id must be non-empty")
    active = payload.get("active_lease")
    if active is None:
        return None
    if not isinstance(active, dict):
        raise ValueError("active_lease must be an object or null")
    lease = ExecutionLease.from_mapping(active)
    if lease.project_id != project_id:
        raise ValueError("active lease project_id must match projection project_id")
    if lease.state is not LeaseState.ACTIVE:
        raise ValueError("active_lease projection may contain only ACTIVE lease state")
    return lease
