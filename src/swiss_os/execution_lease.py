from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping

LEASE_SCHEMA_VERSION = "WAVE-EXECUTION-LEASE-2.0"
LEASE_PROJECTION_SCHEMA_VERSION = "WAVE-EXECUTION-LEASE-PROJECTION-2.0"


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

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "owner_agent_id",
            "run_id",
            "session_id",
            "wave_id",
            "parent_main_sha",
            "authority_epoch",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.fencing_token, bool) or not isinstance(self.fencing_token, int) or self.fencing_token <= 0:
            raise ValueError("fencing_token must be a positive integer")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LeaseRequest":
        allowed = {
            "project_id",
            "owner_agent_id",
            "run_id",
            "session_id",
            "wave_id",
            "parent_main_sha",
            "authority_epoch",
            "fencing_token",
        }
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError(f"unknown lease request keys: {', '.join(unknown)}")
        return cls(
            project_id=_required_str(payload, "project_id"),
            owner_agent_id=_required_str(payload, "owner_agent_id"),
            run_id=_required_str(payload, "run_id"),
            session_id=_required_str(payload, "session_id"),
            wave_id=_required_str(payload, "wave_id"),
            parent_main_sha=_required_str(payload, "parent_main_sha"),
            authority_epoch=_required_str(payload, "authority_epoch"),
            fencing_token=payload.get("fencing_token"),
        )

    @property
    def idempotency_key(self) -> str:
        return "|".join(
            (
                self.project_id,
                self.wave_id,
                self.owner_agent_id,
                self.run_id,
                self.session_id,
                f"TOKEN{self.fencing_token}",
            )
        )


def lease_id_for_key(idempotency_key: str) -> str:
    return f"LEASE-{sha256(idempotency_key.encode('utf-8')).hexdigest()[:20]}"


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
            lease.project_id,
            lease.owner_agent_id,
            lease.run_id,
            lease.session_id,
            lease.wave_id,
            lease.parent_main_sha,
            lease.authority_epoch,
            lease.fencing_token,
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


def same_holder(lease: ExecutionLease, request: LeaseRequest) -> bool:
    return all(
        (
            lease.project_id == request.project_id,
            lease.owner_agent_id == request.owner_agent_id,
            lease.run_id == request.run_id,
            lease.session_id == request.session_id,
            lease.wave_id == request.wave_id,
            lease.parent_main_sha == request.parent_main_sha,
            lease.authority_epoch == request.authority_epoch,
            lease.fencing_token == request.fencing_token,
        )
    )


@dataclass(frozen=True)
class LeaseAdmission:
    kind: LeaseAdmissionKind
    writer_allowed: bool
    read_only_fallback: bool
    reason: str
    current_lease_id: str | None = None
    stale_recovery: bool = False
    cas_conflict: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "writer_allowed": self.writer_allowed,
            "read_only_fallback": self.read_only_fallback,
            "reason": self.reason,
            "current_lease_id": self.current_lease_id,
            "stale_recovery": self.stale_recovery,
            "cas_conflict": self.cas_conflict,
        }


@dataclass(frozen=True)
class LeaseProjection:
    project_id: str
    generation: int
    fencing_high_watermark: int
    active_lease: ExecutionLease | None
    last_lease: ExecutionLease | None
    last_transition: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LeaseProjection":
        if payload.get("schema_version") != LEASE_PROJECTION_SCHEMA_VERSION:
            raise ValueError(f"projection schema_version must be {LEASE_PROJECTION_SCHEMA_VERSION}")
        project_id = _required_str(payload, "project_id")
        generation = payload.get("generation")
        watermark = payload.get("fencing_high_watermark")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
            raise ValueError("generation must be a non-negative integer")
        if isinstance(watermark, bool) or not isinstance(watermark, int) or watermark < 0:
            raise ValueError("fencing_high_watermark must be a non-negative integer")

        active_raw = payload.get("active_lease")
        last_raw = payload.get("last_lease")
        active = ExecutionLease.from_mapping(active_raw) if isinstance(active_raw, Mapping) else None
        last = ExecutionLease.from_mapping(last_raw) if isinstance(last_raw, Mapping) else None
        if active_raw is not None and active is None:
            raise ValueError("active_lease must be object or null")
        if last_raw is not None and last is None:
            raise ValueError("last_lease must be object or null")
        if active and active.state is not LeaseState.ACTIVE:
            raise ValueError("active_lease must be ACTIVE")
        if last and last.state is not LeaseState.RELEASED:
            raise ValueError("last_lease must be RELEASED")
        for lease in (active, last):
            if lease and lease.project_id != project_id:
                raise ValueError("lease project_id must match projection")
            if lease and lease.fencing_token > watermark:
                raise ValueError("watermark cannot trail a persisted lease token")
        transition = payload.get("last_transition", {})
        if not isinstance(transition, Mapping):
            raise ValueError("last_transition must be an object")
        return cls(project_id, generation, watermark, active, last, dict(transition))

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": LEASE_PROJECTION_SCHEMA_VERSION,
            "project_id": self.project_id,
            "generation": self.generation,
            "fencing_high_watermark": self.fencing_high_watermark,
            "active_lease": self.active_lease.as_dict() if self.active_lease else None,
            "last_lease": self.last_lease.as_dict() if self.last_lease else None,
            "last_transition": dict(self.last_transition),
        }


def empty_projection(
    project_id: str,
    *,
    fencing_high_watermark: int = 0,
    transition: Mapping[str, Any] | None = None,
) -> LeaseProjection:
    return LeaseProjection(project_id, 0, fencing_high_watermark, None, None, dict(transition or {}))


def acquire_lease(request: LeaseRequest, now: datetime, ttl_seconds: int) -> ExecutionLease:
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be a positive integer")
    acquired = now.astimezone(timezone.utc).replace(microsecond=0)
    return ExecutionLease(
        LEASE_SCHEMA_VERSION,
        request.project_id,
        lease_id_for_key(request.idempotency_key),
        request.owner_agent_id,
        request.run_id,
        request.session_id,
        request.wave_id,
        format_utc(acquired),
        format_utc(acquired + timedelta(seconds=ttl_seconds)),
        request.parent_main_sha,
        request.authority_epoch,
        request.fencing_token,
        LeaseState.ACTIVE,
        request.idempotency_key,
        True,
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


def evaluate_lease(
    current: ExecutionLease | None,
    request: LeaseRequest | None,
    now: datetime,
    *,
    canonical_parent_sha: str | None = None,
    canonical_authority_epoch: str | None = None,
    fencing_high_watermark: int = 0,
) -> LeaseAdmission:
    now = now.astimezone(timezone.utc)
    if request is not None:
        if request.fencing_token <= fencing_high_watermark and (current is None or not same_holder(current, request)):
            return LeaseAdmission(
                LeaseAdmissionKind.RECOVERY_REQUIRED,
                False,
                True,
                "requested fencing token is not above durable high-watermark",
                current.lease_id if current else None,
            )
        if canonical_parent_sha is not None and request.parent_main_sha != canonical_parent_sha:
            return LeaseAdmission(
                LeaseAdmissionKind.RECOVERY_REQUIRED,
                False,
                True,
                "activation parent SHA is stale relative to canonical main",
                current.lease_id if current else None,
            )
        if canonical_authority_epoch is not None and request.authority_epoch != canonical_authority_epoch:
            return LeaseAdmission(
                LeaseAdmissionKind.RECOVERY_REQUIRED,
                False,
                True,
                "activation authority epoch does not match canonical authority",
                current.lease_id if current else None,
            )

    if current is None:
        return LeaseAdmission(LeaseAdmissionKind.ACQUIRE_ALLOWED, True, False, "no active execution lease")

    if current.state is LeaseState.RELEASED:
        if request is None:
            return LeaseAdmission(LeaseAdmissionKind.ACQUIRE_ALLOWED, True, False, "previous lease is released", current.lease_id)
        if same_holder(current, request):
            return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "released lease identity is terminal", current.lease_id)
        if request.fencing_token <= current.fencing_token:
            return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "successor lease requires a higher fencing token", current.lease_id)
        return LeaseAdmission(LeaseAdmissionKind.ACQUIRE_ALLOWED, True, False, "previous lease is released and successor token is higher", current.lease_id)

    if now < parse_utc(current.expires_at):
        if request is not None and same_holder(current, request):
            return LeaseAdmission(LeaseAdmissionKind.RENEW_ALLOWED, True, False, "same live holder may renew", current.lease_id)
        return LeaseAdmission(LeaseAdmissionKind.READ_ONLY_FALLBACK, False, True, "another writer lease is live", current.lease_id)

    if request is None:
        return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "active lease is expired; recovery requires new session and higher token", current.lease_id)
    if same_holder(current, request) or request.session_id == current.session_id or request.run_id == current.run_id:
        return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "expired lease cannot be resumed by same run/session", current.lease_id)
    if request.fencing_token <= current.fencing_token:
        return LeaseAdmission(LeaseAdmissionKind.RECOVERY_REQUIRED, False, True, "stale takeover requires a higher fencing token", current.lease_id)
    return LeaseAdmission(
        LeaseAdmissionKind.STALE_RECOVERY_ALLOWED,
        True,
        False,
        "expired lease may be recovered by new run/session with higher token",
        current.lease_id,
        True,
    )
