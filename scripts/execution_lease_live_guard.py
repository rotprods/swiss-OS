#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swiss_os.execution_lease import LeaseState, parse_utc
from swiss_os.github_execution_lease import GitHubContentsLeaseStore, LeaseStoreError
from swiss_os.v2_coordination import reduce_coordination

ROOT = Path(__file__).resolve().parents[1]
LEASE_ENFORCEMENT_TOKEN_FLOOR = 19


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def active_claims() -> list[dict[str, Any]]:
    events = [load_json(p) for p in sorted((ROOT / "docs/state/v2/events").glob("*.json"))]
    claims = [load_json(p) for p in sorted((ROOT / "docs/state/v2/claims").glob("*.json"))]
    projection = reduce_coordination(events, claims)
    violations = projection.get("violations", [])
    if violations:
        raise ValueError(f"coordination violations: {violations}")
    active_ids = set(projection.get("active_claim_ids", []))
    return [claim for claim in claims if claim.get("claim_id") in active_ids]


def evaluate(now: datetime, *, repo: str, token: str) -> tuple[bool, dict[str, Any]]:
    active = active_claims()
    receipt: dict[str, Any] = {
        "schema_version": "EXECUTION-LEASE-LIVE-GUARD-1.0",
        "observed_at": now.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "token_floor": LEASE_ENFORCEMENT_TOKEN_FLOOR,
        "active_claim_ids": [str(c.get("claim_id")) for c in active],
        "violations": [],
    }
    if len(active) > 1:
        receipt["violations"].append(f"MULTIPLE_ACTIVE_CLAIMS:{len(active)}")
        receipt["pass"] = False
        return False, receipt
    if not active:
        receipt.update(status="NO_ACTIVE_CLAIM", lease_required=False, pass_=True)
        receipt["pass"] = True
        receipt.pop("pass_", None)
        return True, receipt

    claim = active[0]
    fencing = claim.get("fencing_token")
    if isinstance(fencing, bool) or not isinstance(fencing, int):
        receipt["violations"].append("ACTIVE_CLAIM_INVALID_FENCING_TOKEN")
        receipt["pass"] = False
        return False, receipt
    receipt["claim"] = {
        "claim_id": claim.get("claim_id"),
        "agent_id": claim.get("agent_id"),
        "session_id": claim.get("session_id"),
        "base_sha": claim.get("base_sha"),
        "fencing_token": fencing,
        "authority_epoch": (claim.get("preconditions") or {}).get("authority_epoch"),
    }
    if fencing < LEASE_ENFORCEMENT_TOKEN_FLOOR:
        receipt.update(status="LEGACY_CLAIM_BELOW_LEASE_FLOOR", lease_required=False)
        receipt["pass"] = True
        return True, receipt

    if not token:
        receipt["violations"].append("LIVE_LEASE_READBACK_REQUIRES_GITHUB_TOKEN")
        receipt["pass"] = False
        return False, receipt

    store = GitHubContentsLeaseStore(repo, token)
    stored = store.read()
    lease = stored.projection.active_lease
    receipt.update(
        status="LIVE_LEASE_REQUIRED",
        lease_required=True,
        lease_blob_sha=stored.blob_sha,
        lease_generation=stored.projection.generation,
        lease_fencing_high_watermark=stored.projection.fencing_high_watermark,
        lease=lease.as_dict() if lease else None,
    )
    if lease is None:
        receipt["violations"].append("ACTIVE_CLAIM_HAS_NO_GLOBAL_LEASE")
    else:
        if lease.state is not LeaseState.ACTIVE:
            receipt["violations"].append(f"GLOBAL_LEASE_NOT_ACTIVE:{lease.state.value}")
        if now.astimezone(timezone.utc) >= parse_utc(lease.expires_at):
            receipt["violations"].append("GLOBAL_LEASE_EXPIRED")
        checks = {
            "LEASE_AGENT_MISMATCH": (lease.owner_agent_id, claim.get("agent_id")),
            "LEASE_SESSION_MISMATCH": (lease.session_id, claim.get("session_id")),
            "LEASE_FENCING_MISMATCH": (lease.fencing_token, fencing),
            "LEASE_PARENT_MISMATCH": (lease.parent_main_sha, claim.get("base_sha")),
            "LEASE_AUTHORITY_EPOCH_MISMATCH": (
                lease.authority_epoch,
                (claim.get("preconditions") or {}).get("authority_epoch"),
            ),
        }
        for code, (observed, expected) in checks.items():
            if observed != expected:
                receipt["violations"].append(f"{code}:{observed}!={expected}")
        if stored.projection.fencing_high_watermark < fencing:
            receipt["violations"].append("LEASE_WATERMARK_BEHIND_ACTIVE_CLAIM")

    ok = not receipt["violations"]
    receipt["pass"] = ok
    return ok, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Require token19+ claims to match the globally serialized live execution lease.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "rotprods/swiss-OS"))
    parser.add_argument("--now", help="UTC Z timestamp; defaults to wall clock")
    parser.add_argument("--receipt")
    args = parser.parse_args()
    now = parse_utc(args.now) if args.now else datetime.now(timezone.utc)
    try:
        ok, receipt = evaluate(now, repo=args.repo, token=os.environ.get("GITHUB_TOKEN", ""))
    except (LeaseStoreError, ValueError, OSError, json.JSONDecodeError) as exc:
        ok = False
        receipt = {
            "schema_version": "EXECUTION-LEASE-LIVE-GUARD-1.0",
            "observed_at": now.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "pass": False,
            "violations": [f"LIVE_LEASE_GUARD_ERROR:{exc}"],
        }
    rendered = json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.receipt:
        target = Path(args.receipt)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
