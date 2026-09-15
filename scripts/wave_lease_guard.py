#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from swiss_os.execution_lease import LeaseRequest, parse_utc
from swiss_os.github_execution_lease import (
    DEFAULT_LEASE_BRANCH,
    DEFAULT_LEASE_PATH,
    GitHubContentsLeaseStore,
    LeaseStoreError,
    acquire_atomic,
    release_atomic,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_store(args: argparse.Namespace) -> GitHubContentsLeaseStore:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise LeaseStoreError("GITHUB_TOKEN is required for live execution-lease operations")
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "rotprods/swiss-OS")
    return GitHubContentsLeaseStore(repo, token, branch=args.branch, path=args.path)


def request_from_args(args: argparse.Namespace) -> LeaseRequest:
    return LeaseRequest(
        project_id=args.project_id,
        owner_agent_id=args.owner_agent_id,
        run_id=args.run_id,
        session_id=args.session_id,
        wave_id=args.wave_id,
        parent_main_sha=args.parent_main_sha,
        authority_epoch=args.authority_epoch,
        fencing_token=args.fencing_token,
    )


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def status(args: argparse.Namespace) -> int:
    stored = build_store(args).read()
    projection = stored.projection
    active = projection.active_lease
    now = parse_utc(args.now) if args.now else utc_now()
    expired = bool(active and now >= parse_utc(active.expires_at))
    emit(
        {
            "schema_version": "WAVE-EXECUTION-LEASE-STATUS-2.0",
            "project_id": projection.project_id,
            "generation": projection.generation,
            "fencing_high_watermark": projection.fencing_high_watermark,
            "blob_sha": stored.blob_sha,
            "active_lease": active.as_dict() if active else None,
            "last_lease": projection.last_lease.as_dict() if projection.last_lease else None,
            "expired": expired,
            "writer_slot_available": active is None,
        }
    )
    return 2 if expired else 0


def acquire(args: argparse.Namespace) -> int:
    store = build_store(args)
    req = request_from_args(args)
    now = parse_utc(args.now) if args.now else utc_now()
    result = acquire_atomic(
        store,
        req,
        now,
        args.ttl_seconds,
        canonical_parent_sha=args.canonical_parent_sha,
        canonical_authority_epoch=args.canonical_authority_epoch,
    )
    emit(
        {
            "schema_version": "WAVE-EXECUTION-LEASE-ACTION-2.0",
            "action": "ACQUIRE_OR_RENEW",
            "committed": result.committed,
            "admission": result.admission.as_dict(),
            "blob_sha": result.stored.blob_sha,
            "projection": result.stored.projection.as_dict(),
        }
    )
    return 0 if result.committed else 3


def release(args: argparse.Namespace) -> int:
    store = build_store(args)
    req = request_from_args(args)
    now = parse_utc(args.now) if args.now else utc_now()
    result = release_atomic(store, req, now, args.reason)
    emit(
        {
            "schema_version": "WAVE-EXECUTION-LEASE-ACTION-2.0",
            "action": "RELEASE",
            "committed": result.committed,
            "admission": result.admission.as_dict(),
            "blob_sha": result.stored.blob_sha,
            "projection": result.stored.projection.as_dict(),
        }
    )
    return 0 if result.committed else 3


def add_store_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo")
    parser.add_argument("--branch", default=DEFAULT_LEASE_BRANCH)
    parser.add_argument("--path", default=DEFAULT_LEASE_PATH)
    parser.add_argument("--now", help="UTC timestamp in Z form; defaults to wall clock")


def add_request_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-id", default="SWITZERLAND_JOB_OS")
    parser.add_argument("--owner-agent-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--wave-id", required=True)
    parser.add_argument("--parent-main-sha", required=True)
    parser.add_argument("--authority-epoch", required=True)
    parser.add_argument("--fencing-token", type=int, required=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Operate the globally serialized SWISS-OS execution lease.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status")
    add_store_args(p)
    p.set_defaults(func=status)

    p = sub.add_parser("acquire")
    add_store_args(p)
    add_request_args(p)
    p.add_argument("--canonical-parent-sha", required=True)
    p.add_argument("--canonical-authority-epoch", required=True)
    p.add_argument("--ttl-seconds", type=int, default=1800)
    p.set_defaults(func=acquire)

    p = sub.add_parser("release")
    add_store_args(p)
    add_request_args(p)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=release)

    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (LeaseStoreError, ValueError) as exc:
        emit({"status": "BLOCKED", "error": str(exc), "writer_allowed": False})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
