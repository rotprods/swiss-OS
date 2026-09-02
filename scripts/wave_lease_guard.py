#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from swiss_os.execution_lease import (
    DEFAULT_LEASE_STATE_PATH,
    LeaseState,
    load_lease_projection,
    parse_utc,
)


RECEIPT_SCHEMA_VERSION = "WAVE-EXECUTION-LEASE-GUARD-1.0"


def evaluate(path: str | Path, now: datetime) -> tuple[bool, dict[str, object]]:
    violations: list[str] = []
    lease = None
    try:
        lease = load_lease_projection(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        violations.append(f"INVALID_LEASE_PROJECTION:{exc}")

    status = "NO_ACTIVE_LEASE"
    lease_id: str | None = None
    expires_at: str | None = None
    if lease is not None:
        lease_id = lease.lease_id
        expires_at = lease.expires_at
        if lease.state is not LeaseState.ACTIVE:
            violations.append(f"NON_ACTIVE_LEASE_IN_ACTIVE_PROJECTION:{lease.state.value}")
        elif now.astimezone(timezone.utc) >= parse_utc(lease.expires_at):
            status = "EXPIRED_ACTIVE_LEASE"
            violations.append(f"EXPIRED_ACTIVE_LEASE_REQUIRES_RECOVERY:{lease.lease_id}")
        else:
            status = "LIVE_WRITER_LEASE"

    receipt: dict[str, object] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "observed_at": now.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "lease_state_path": str(path),
        "status": status,
        "active_lease_id": lease_id,
        "expires_at": expires_at,
        "writer_overlap_allowed": False,
        "read_only_fallback_required_for_foreign_activation": status == "LIVE_WRITER_LEASE",
        "violations": violations,
        "pass": not violations,
    }
    return not violations, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the durable wave execution lease projection.")
    parser.add_argument("--lease-state", default=str(DEFAULT_LEASE_STATE_PATH))
    parser.add_argument("--now", help="UTC Z timestamp; defaults to current wall clock")
    parser.add_argument("--receipt")
    args = parser.parse_args()

    now = parse_utc(args.now) if args.now else datetime.now(timezone.utc)
    ok, receipt = evaluate(args.lease_state, now)
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        target = Path(args.receipt)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
