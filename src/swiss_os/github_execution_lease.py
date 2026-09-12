from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .execution_lease import (
    LeaseAdmission,
    LeaseAdmissionKind,
    LeaseProjection,
    LeaseRequest,
    acquire_lease,
    evaluate_lease,
    format_utc,
    release_lease,
    renew_lease,
    same_holder,
)

DEFAULT_LEASE_BRANCH = "coordination/execution-lease"
DEFAULT_LEASE_PATH = "docs/state/execution-leases/current.json"


class LeaseStoreError(RuntimeError):
    pass


class LeaseStoreConflict(LeaseStoreError):
    pass


@dataclass(frozen=True)
class StoredProjection:
    projection: LeaseProjection
    blob_sha: str


class LeaseStore(Protocol):
    def read(self) -> StoredProjection: ...

    def compare_and_swap(
        self,
        expected_blob_sha: str,
        projection: LeaseProjection,
        message: str,
    ) -> StoredProjection: ...


class GitHubContentsLeaseStore:
    """Single-file durable CAS store backed by GitHub Contents API.

    GitHub's required `sha` on file updates acts as compare-and-swap. Two writers
    that read the same blob SHA cannot both commit an update: the loser receives
    HTTP 409/422 and must re-read instead of blind-retrying the mutation.
    """

    def __init__(
        self,
        repo: str,
        token: str,
        *,
        branch: str = DEFAULT_LEASE_BRANCH,
        path: str = DEFAULT_LEASE_PATH,
        api_url: str = "https://api.github.com",
    ):
        if not token:
            raise ValueError("GitHub token is required")
        if repo.count("/") != 1:
            raise ValueError("repo must be owner/name")
        self.repo = repo
        self.token = token
        self.branch = branch
        self.path = path
        self.api_url = api_url.rstrip("/")

    def _request(
        self,
        method: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        url = f"{self.api_url}/repos/{self.repo}/contents/{quote(self.path, safe='/')}"
        if method == "GET":
            url += f"?ref={quote(self.branch, safe='')}"
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        req = Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "swiss-os-execution-lease/2.0",
            },
        )
        try:
            with urlopen(req, timeout=30) as response:
                raw = response.read()
                value = json.loads(raw) if raw else {}
                if not isinstance(value, dict):
                    raise LeaseStoreError("GitHub lease store returned non-object JSON")
                return value
        except HTTPError as exc:
            body = exc.read().decode(errors="replace")
            if exc.code in {409, 422}:
                raise LeaseStoreConflict(f"GitHub CAS conflict ({exc.code})") from exc
            raise LeaseStoreError(f"GitHub lease store HTTP {exc.code}: {body[:500]}") from exc
        except (URLError, OSError, TimeoutError) as exc:
            raise LeaseStoreError(f"GitHub lease store unavailable: {exc}") from exc

    def read(self) -> StoredProjection:
        payload = self._request("GET")
        try:
            raw = base64.b64decode(str(payload["content"]).replace("\n", ""))
            blob_sha = str(payload["sha"])
            obj = json.loads(raw.decode())
        except Exception as exc:
            raise LeaseStoreError("invalid lease store response") from exc
        return StoredProjection(LeaseProjection.from_mapping(obj), blob_sha)

    def compare_and_swap(
        self,
        expected_blob_sha: str,
        projection: LeaseProjection,
        message: str,
    ) -> StoredProjection:
        content = json.dumps(
            projection.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ) + "\n"
        response = self._request(
            "PUT",
            {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": self.branch,
                "sha": expected_blob_sha,
            },
        )
        try:
            new_sha = str(response["content"]["sha"])
        except Exception as exc:
            raise LeaseStoreError("GitHub CAS response missing content sha") from exc
        return StoredProjection(projection, new_sha)


@dataclass(frozen=True)
class AtomicLeaseResult:
    admission: LeaseAdmission
    stored: StoredProjection
    committed: bool


def _transition(kind: str, now: datetime, request: LeaseRequest, **extra: Any) -> dict[str, Any]:
    out = {
        "kind": kind,
        "occurred_at": format_utc(now),
        "session_id": request.session_id,
        "run_id": request.run_id,
        "fencing_token": request.fencing_token,
        "parent_main_sha": request.parent_main_sha,
        "authority_epoch": request.authority_epoch,
    }
    out.update(extra)
    return out


def acquire_atomic(
    store: LeaseStore,
    request: LeaseRequest,
    now: datetime,
    ttl_seconds: int,
    *,
    canonical_parent_sha: str,
    canonical_authority_epoch: str,
) -> AtomicLeaseResult:
    before = store.read()
    projection = before.projection
    current = projection.active_lease or projection.last_lease
    admission = evaluate_lease(
        current,
        request,
        now,
        canonical_parent_sha=canonical_parent_sha,
        canonical_authority_epoch=canonical_authority_epoch,
        fencing_high_watermark=projection.fencing_high_watermark,
    )
    if not admission.writer_allowed:
        return AtomicLeaseResult(admission, before, False)

    if admission.kind is LeaseAdmissionKind.RENEW_ALLOWED and projection.active_lease:
        lease = renew_lease(projection.active_lease, now, ttl_seconds)
        transition_kind = "RENEW"
    else:
        lease = acquire_lease(request, now, ttl_seconds)
        transition_kind = "ACQUIRE"

    candidate = LeaseProjection(
        projection.project_id,
        projection.generation + 1,
        max(projection.fencing_high_watermark, request.fencing_token),
        lease,
        projection.last_lease,
        _transition(transition_kind, now, request),
    )
    try:
        after = store.compare_and_swap(
            before.blob_sha,
            candidate,
            f"coordination: {transition_kind.lower()} execution lease token{request.fencing_token}",
        )
    except LeaseStoreConflict:
        latest = store.read()
        current = latest.projection.active_lease or latest.projection.last_lease
        denied = evaluate_lease(
            current,
            request,
            now,
            canonical_parent_sha=canonical_parent_sha,
            canonical_authority_epoch=canonical_authority_epoch,
            fencing_high_watermark=latest.projection.fencing_high_watermark,
        )
        if denied.writer_allowed:
            denied = LeaseAdmission(
                LeaseAdmissionKind.READ_ONLY_FALLBACK,
                False,
                True,
                "CAS lost to concurrent writer; fail closed and re-read before any retry",
                current.lease_id if current else None,
                cas_conflict=True,
            )
        else:
            denied = LeaseAdmission(
                denied.kind,
                denied.writer_allowed,
                denied.read_only_fallback,
                denied.reason,
                denied.current_lease_id,
                denied.stale_recovery,
                True,
            )
        return AtomicLeaseResult(denied, latest, False)
    return AtomicLeaseResult(admission, after, True)


def release_atomic(
    store: LeaseStore,
    request: LeaseRequest,
    now: datetime,
    reason: str,
) -> AtomicLeaseResult:
    before = store.read()
    projection = before.projection
    lease = projection.active_lease
    if lease is None or not same_holder(lease, request):
        admission = LeaseAdmission(
            LeaseAdmissionKind.READ_ONLY_FALLBACK,
            False,
            True,
            "release denied: caller does not own active lease",
            lease.lease_id if lease else None,
        )
        return AtomicLeaseResult(admission, before, False)

    released = release_lease(lease, now, reason)
    candidate = LeaseProjection(
        projection.project_id,
        projection.generation + 1,
        max(projection.fencing_high_watermark, released.fencing_token),
        None,
        released,
        _transition("RELEASE", now, request, reason=reason),
    )
    try:
        after = store.compare_and_swap(
            before.blob_sha,
            candidate,
            f"coordination: release execution lease token{request.fencing_token}",
        )
    except LeaseStoreConflict:
        latest = store.read()
        admission = LeaseAdmission(
            LeaseAdmissionKind.READ_ONLY_FALLBACK,
            False,
            True,
            "release CAS conflict; fail closed",
            latest.projection.active_lease.lease_id if latest.projection.active_lease else None,
            cas_conflict=True,
        )
        return AtomicLeaseResult(admission, latest, False)
    return AtomicLeaseResult(
        LeaseAdmission(
            LeaseAdmissionKind.ACQUIRE_ALLOWED,
            False,
            False,
            "lease released",
            released.lease_id,
        ),
        after,
        True,
    )
