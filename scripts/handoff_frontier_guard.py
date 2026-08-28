#!/usr/bin/env python3
"""Fail CI when NEXT/STATE lag the latest persisted ECV result.

The guard is intentionally authority-neutral. It reads only durable Git state and
never allocates H-IDs, mutates operational authority, or opens outbound.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
RESULT_GLOB = "ECV_BATCH_*_RESULT.json"


@dataclass(frozen=True)
class EcvFrontier:
    cumulative_verified: int
    remaining_never_verified: int
    pending_requeue: int
    batch_id: str
    result_file: str
    packet_sha256: str


class FrontierError(ValueError):
    pass


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FrontierError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FrontierError(f"expected object in {path}")
    return value


def _require_nonnegative_int(payload: dict, key: str, path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FrontierError(f"{path}: {key} must be a non-negative integer")
    return value


def _validate_safety(payload: dict, path: Path) -> None:
    if payload.get("authority_advanced") is not False:
        raise FrontierError(f"{path}: authority_advanced must remain false")
    if payload.get("h_id_allocations") != 0:
        raise FrontierError(f"{path}: h_id_allocations must remain 0")
    if payload.get("outbound") != "CLOSED":
        raise FrontierError(f"{path}: outbound must remain CLOSED")
    if payload.get("send_allowed") != 0:
        raise FrontierError(f"{path}: send_allowed must remain 0")


def latest_ecv_frontier(root: Path = ROOT) -> EcvFrontier:
    state_dir = root / "docs" / "state"
    paths = sorted(state_dir.glob(RESULT_GLOB))
    if not paths:
        raise FrontierError("no persisted ECV result summaries found")

    frontiers: list[EcvFrontier] = []
    seen_cumulative: dict[int, tuple[int, int]] = {}
    frontier_keys = (
        "cumulative_current_detail_verified",
        "remaining_never_verified",
        "pending_requeue",
    )

    for path in paths:
        payload = _load_json(path)
        if payload.get("schema_version") != "ECV-RESULT-SUMMARY-1.0":
            continue

        # All persisted summaries, including early legacy summaries, are still
        # safety-bearing evidence and must remain fail-closed.
        _validate_safety(payload, path)

        batch_id = payload.get("batch_id")
        packet = payload.get("ecv_packet_sha256")
        if not isinstance(batch_id, str) or not batch_id:
            raise FrontierError(f"{path}: batch_id missing")
        if not isinstance(packet, str) or not re.fullmatch(r"[0-9a-f]{64}", packet):
            raise FrontierError(f"{path}: ecv_packet_sha256 must be lowercase sha256")

        present = [key in payload for key in frontier_keys]
        if not any(present):
            # ECV-RESULT-SUMMARY-1.0 predates cumulative frontier fields for the
            # earliest batches. They are valid durable evidence but cannot by
            # themselves define the current handoff frontier.
            continue
        if not all(present):
            missing = [key for key, is_present in zip(frontier_keys, present) if not is_present]
            raise FrontierError(f"{path}: partial cumulative frontier; missing {', '.join(missing)}")

        cumulative = _require_nonnegative_int(payload, "cumulative_current_detail_verified", path)
        remaining = _require_nonnegative_int(payload, "remaining_never_verified", path)
        pending = _require_nonnegative_int(payload, "pending_requeue", path)

        prior = seen_cumulative.setdefault(cumulative, (remaining, pending))
        if prior != (remaining, pending):
            raise FrontierError(
                f"{path}: conflicting ECV frontier for cumulative={cumulative}: "
                f"{prior} vs {(remaining, pending)}"
            )
        frontiers.append(EcvFrontier(cumulative, remaining, pending, batch_id, path.name, packet))

    if not frontiers:
        raise FrontierError("no ECV result summary contains cumulative frontier fields")

    return max(frontiers, key=lambda item: (item.cumulative_verified, -item.remaining_never_verified, item.batch_id))


def validate_handoff(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        frontier = latest_ecv_frontier(root)
    except FrontierError as exc:
        return [str(exc)]

    next_path = root / "docs" / "state" / "NEXT.json"
    state_path = root / "STATE.md"
    try:
        next_payload = _load_json(next_path)
    except FrontierError as exc:
        return [str(exc)]

    ecv = next_payload.get("ecv_frontier")
    if not isinstance(ecv, dict):
        errors.append("NEXT.json: ecv_frontier must be an object")
    else:
        expected = {
            "current_detail_verified": frontier.cumulative_verified,
            "remaining_unverified": frontier.remaining_never_verified,
            "pending_requeue": frontier.pending_requeue,
        }
        for key, value in expected.items():
            if ecv.get(key) != value:
                errors.append(f"NEXT.json: ecv_frontier.{key}={ecv.get(key)!r}, expected {value}")
        latest_batch = ecv.get("latest_subbatch_id")
        if latest_batch != frontier.batch_id:
            errors.append(
                f"NEXT.json: ecv_frontier.latest_subbatch_id={latest_batch!r}, expected {frontier.batch_id!r}"
            )
        latest_packet = ecv.get("latest_subbatch_packet_sha256")
        if latest_packet != frontier.packet_sha256:
            errors.append("NEXT.json: ecv_frontier.latest_subbatch_packet_sha256 does not match latest durable result")

    if next_payload.get("authority_advance_allowed") is not False:
        errors.append("NEXT.json: authority_advance_allowed must remain false in pre-authority ECV")
    if next_payload.get("canonical_id_allocation_allowed") is not False:
        errors.append("NEXT.json: canonical_id_allocation_allowed must remain false")
    if next_payload.get("outbound_allowed") is not False:
        errors.append("NEXT.json: outbound_allowed must remain false")

    try:
        state_text = state_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read STATE.md: {exc}")
        return errors

    state_verified = re.search(r"^ECV verified frontier\s+(\d+)\s*/\s*(\d+)\s*$", state_text, re.M)
    if not state_verified:
        errors.append("STATE.md: missing machine-readable 'ECV verified frontier N / TOTAL' line")
    else:
        verified, total = map(int, state_verified.groups())
        if verified != frontier.cumulative_verified:
            errors.append(f"STATE.md: ECV verified frontier={verified}, expected {frontier.cumulative_verified}")
        if total != frontier.cumulative_verified + frontier.remaining_never_verified:
            errors.append("STATE.md: ECV candidate denominator must equal verified + remaining-never-verified")

    state_remaining = re.search(r"^ECV remaining never verified\s+(\d+)\s*$", state_text, re.M)
    if not state_remaining:
        errors.append("STATE.md: missing machine-readable 'ECV remaining never verified N' line")
    elif int(state_remaining.group(1)) != frontier.remaining_never_verified:
        errors.append(
            f"STATE.md: ECV remaining never verified={state_remaining.group(1)}, expected {frontier.remaining_never_verified}"
        )

    for marker in ("OUTBOUND                        CLOSED", "send_allowed                      0"):
        if marker not in state_text:
            errors.append(f"STATE.md: missing safety marker {marker!r}")

    return errors


def main(argv: Iterable[str] | None = None) -> int:
    del argv
    errors = validate_handoff(ROOT)
    if errors:
        print("handoff_frontier_guard: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    frontier = latest_ecv_frontier(ROOT)
    print(
        "handoff_frontier_guard: PASS "
        f"verified={frontier.cumulative_verified} remaining={frontier.remaining_never_verified} "
        f"pending_requeue={frontier.pending_requeue} batch={frontier.batch_id}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
