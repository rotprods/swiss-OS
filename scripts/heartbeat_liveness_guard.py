#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_DIR = ROOT / "docs/state/v2/claims"
HEARTBEATS_DIR = ROOT / "docs/state/agent-runtime/heartbeats"
DEFAULT_TTL_SECONDS = 1800


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def load_objects(directory: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"{path}: expected JSON object")
        values.append(value)
    return values


def evaluate(
    claims: Iterable[dict[str, Any]],
    heartbeats: Iterable[dict[str, Any]],
    now: datetime,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> tuple[bool, dict[str, Any]]:
    now = now.astimezone(timezone.utc)
    hb_by_session: dict[str, list[dict[str, Any]]] = {}
    for heartbeat in heartbeats:
        session_id = heartbeat.get("session_id")
        observed_at = heartbeat.get("observed_at")
        if not isinstance(session_id, str) or not isinstance(observed_at, str):
            continue
        hb_by_session.setdefault(session_id, []).append(heartbeat)

    violations: list[str] = []
    sessions: list[dict[str, Any]] = []
    for claim in claims:
        if claim.get("state") not in {"ACTIVE", "BLOCKED"}:
            continue
        claim_id = str(claim.get("claim_id", ""))
        session_id = str(claim.get("session_id", ""))
        if not claim_id or not session_id:
            violations.append(f"ACTIVE_CLAIM_MISSING_SESSION:{claim_id or '<missing>'}")
            continue
        candidates = hb_by_session.get(session_id, [])
        if not candidates:
            violations.append(f"MISSING_HEARTBEAT:{claim_id}:{session_id}")
            sessions.append({"claim_id": claim_id, "session_id": session_id, "status": "MISSING"})
            continue
        latest = max(candidates, key=lambda hb: parse_time(str(hb["observed_at"])))
        observed = parse_time(str(latest["observed_at"]))
        age_seconds = max(0, int((now - observed).total_seconds()))
        heartbeat_state = str(latest.get("state", ""))
        expected_states = {"ACTIVE", "BLOCKED"}
        if heartbeat_state not in expected_states:
            violations.append(f"ACTIVE_CLAIM_TERMINAL_HEARTBEAT:{claim_id}:{heartbeat_state}")
        if age_seconds > ttl_seconds:
            violations.append(f"STALE_HEARTBEAT:{claim_id}:{session_id}:AGE={age_seconds}:TTL={ttl_seconds}")
        sessions.append({
            "claim_id": claim_id,
            "session_id": session_id,
            "heartbeat_id": latest.get("heartbeat_id"),
            "heartbeat_state": heartbeat_state,
            "observed_at": latest.get("observed_at"),
            "age_seconds": age_seconds,
            "ttl_seconds": ttl_seconds,
            "status": "STALE" if age_seconds > ttl_seconds else "LIVE",
        })

    receipt = {
        "schema_version": "GRAPH-V2-HEARTBEAT-LIVENESS-1.0",
        "evaluated_at": now.isoformat().replace("+00:00", "Z"),
        "ttl_seconds": ttl_seconds,
        "active_session_count": len(sessions),
        "sessions": sessions,
        "violations": violations,
    }
    return not violations, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims-dir", default=str(CLAIMS_DIR))
    parser.add_argument("--heartbeats-dir", default=str(HEARTBEATS_DIR))
    parser.add_argument("--now", help="Injectable RFC3339 UTC time; defaults to wall clock")
    parser.add_argument("--ttl-seconds", type=int, default=DEFAULT_TTL_SECONDS)
    parser.add_argument("--receipt")
    args = parser.parse_args()

    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    ok, receipt = evaluate(
        load_objects(Path(args.claims_dir)),
        load_objects(Path(args.heartbeats_dir)),
        now,
        args.ttl_seconds,
    )
    text = json.dumps(receipt, sort_keys=True)
    print(text)
    if args.receipt:
        Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.receipt).write_text(text + "\n", encoding="utf-8")
    if not ok:
        for violation in receipt["violations"]:
            print(violation, file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
