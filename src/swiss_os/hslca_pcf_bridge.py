from __future__ import annotations

"""Bind HSLCA page checkpoints to truthful per-page capture timestamps for PCF-1.0.

HSLCA-1.0 writes one atomic JSON checkpoint immediately after each successful
page parse. PCF-1.0 intentionally requires `captured_at` on every page so a
checkpoint from an older activation cannot silently satisfy a new current-run
completion claim. The original HSLCA schema predates that field.

This bridge derives `captured_at` from the filesystem mtime of the exact
checkpoint file only after proving that the checkpoint JSON is semantically
identical to the page embedded in the final HSLCA capture. The timestamp must
fall inside the capture's own started/completed interval. A copied, stale,
missing or tampered checkpoint therefore fails closed.

The bridge is pre-authority evidence plumbing only. It never allocates H-IDs,
advances authority, or opens outbound.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

from .directory_manifest import write_json_atomic


SCHEMA_VERSION = "HSLCA-PCF-CHECKPOINT-BRIDGE-1.0"


class HSLCAProofBridgeError(ValueError):
    """Raised when checkpoint timestamp provenance cannot be proven."""


def _timestamp(value: object, *, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise HSLCAProofBridgeError(f"{field} must be a non-empty ISO-8601 string")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise HSLCAProofBridgeError(f"{field} must be valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise HSLCAProofBridgeError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HSLCAProofBridgeError(f"{field} must be a positive integer")
    return value


def _strict_false(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if not isinstance(value, bool) or value is not False:
        raise HSLCAProofBridgeError(f"{key} must be exactly false")


def _strict_zero(payload: Mapping[str, object], key: str) -> None:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise HSLCAProofBridgeError(f"{key} must be integer 0")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def enrich_capture_with_checkpoint_times(
    capture_payload: object,
    *,
    pages_dir: str | Path,
) -> dict[str, Any]:
    if not isinstance(capture_payload, Mapping):
        raise HSLCAProofBridgeError("capture payload must be a JSON object")
    if capture_payload.get("schema_version") != "MEMBER_DIRECTORY_CAPTURE_V1":
        raise HSLCAProofBridgeError("unsupported capture schema")

    _strict_false(capture_payload, "authority_advanced")
    _strict_zero(capture_payload, "h_id_allocations")
    _strict_false(capture_payload, "outbound_opened")
    _strict_zero(capture_payload, "send_allowed")

    capture_id = capture_payload.get("capture_id")
    locale = capture_payload.get("locale")
    if not isinstance(capture_id, str) or not capture_id.strip():
        raise HSLCAProofBridgeError("capture_id must be a non-empty string")
    if not isinstance(locale, str) or not locale.strip():
        raise HSLCAProofBridgeError("locale must be a non-empty string")

    started_at = _timestamp(capture_payload.get("started_at"), field="started_at")
    completed_at = _timestamp(capture_payload.get("completed_at"), field="completed_at")
    if completed_at < started_at:
        raise HSLCAProofBridgeError("completed_at precedes started_at")

    expected_pages = _positive_int(
        capture_payload.get("expected_pages"), field="expected_pages"
    )
    raw_pages = capture_payload.get("pages")
    if not isinstance(raw_pages, list) or not all(
        isinstance(page, Mapping) for page in raw_pages
    ):
        raise HSLCAProofBridgeError("pages must be an array of objects")
    if len(raw_pages) != expected_pages:
        raise HSLCAProofBridgeError("capture page cardinality mismatch")

    directory = Path(pages_dir)
    if not directory.is_dir():
        raise HSLCAProofBridgeError("pages_dir is not a directory")

    enriched_pages: list[dict[str, Any]] = []
    seen_positions: set[int] = set()
    for raw_page in raw_pages:
        assert isinstance(raw_page, Mapping)
        position = _positive_int(raw_page.get("page_position"), field="page_position")
        if position in seen_positions:
            raise HSLCAProofBridgeError(f"duplicate page_position: {position}")
        seen_positions.add(position)
        if raw_page.get("capture_id") != capture_id:
            raise HSLCAProofBridgeError(f"page {position} capture_id mismatch")
        if raw_page.get("locale") != locale:
            raise HSLCAProofBridgeError(f"page {position} locale mismatch")

        checkpoint_path = directory / f"page-{position:04d}.json"
        if not checkpoint_path.is_file():
            raise HSLCAProofBridgeError(
                f"page {position} checkpoint is missing: {checkpoint_path.name}"
            )
        checkpoint = _read_json(checkpoint_path)
        if not isinstance(checkpoint, Mapping):
            raise HSLCAProofBridgeError(f"page {position} checkpoint is not an object")
        if dict(checkpoint) != dict(raw_page):
            raise HSLCAProofBridgeError(
                f"page {position} checkpoint does not equal capture page payload"
            )

        stat = checkpoint_path.stat()
        captured_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        # Filesystems may expose sub-second rounding. Allow one second of timestamp
        # granularity tolerance at the capture boundaries, but never cross an
        # activation by minutes/hours/days.
        tolerance_seconds = 1.0
        if captured_at.timestamp() < started_at.timestamp() - tolerance_seconds:
            raise HSLCAProofBridgeError(
                f"page {position} checkpoint predates current capture window"
            )
        if captured_at.timestamp() > completed_at.timestamp() + tolerance_seconds:
            raise HSLCAProofBridgeError(
                f"page {position} checkpoint postdates current capture window"
            )

        enriched = dict(raw_page)
        enriched["captured_at"] = captured_at.isoformat().replace("+00:00", "Z")
        enriched["captured_at_basis"] = "ATOMIC_CHECKPOINT_FILE_MTIME"
        enriched_pages.append(enriched)

    expected_positions = set(range(1, expected_pages + 1))
    if seen_positions != expected_positions:
        missing = sorted(expected_positions - seen_positions)
        extra = sorted(seen_positions - expected_positions)
        raise HSLCAProofBridgeError(
            f"capture page set mismatch missing={missing} extra={extra}"
        )

    out = json.loads(json.dumps(capture_payload))
    out["pages"] = sorted(enriched_pages, key=lambda page: page["page_position"])
    out["checkpoint_timestamp_provenance"] = {
        "schema_version": SCHEMA_VERSION,
        "basis": "ATOMIC_CHECKPOINT_FILE_MTIME",
        "pages_verified": expected_pages,
        "capture_window_start": started_at.isoformat().replace("+00:00", "Z"),
        "capture_window_end": completed_at.isoformat().replace("+00:00", "Z"),
    }
    out["authority_advanced"] = False
    out["h_id_allocations"] = 0
    out["outbound_opened"] = False
    out["send_allowed"] = 0
    return out


def bridge_file(
    capture_path: str | Path,
    *,
    pages_dir: str | Path,
    out_path: str | Path,
) -> dict[str, Any]:
    capture_file = Path(capture_path)
    payload = _read_json(capture_file)
    enriched = enrich_capture_with_checkpoint_times(payload, pages_dir=pages_dir)
    write_json_atomic(out_path, enriched)
    return {
        "valid": True,
        "capture_id": enriched["capture_id"],
        "pages_verified": enriched["checkpoint_timestamp_provenance"]["pages_verified"],
        "timestamp_basis": "ATOMIC_CHECKPOINT_FILE_MTIME",
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "out": str(out_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.hslca_pcf_bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    bridge = sub.add_parser("bridge")
    bridge.add_argument("capture")
    bridge.add_argument("--pages-dir", required=True)
    bridge.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "bridge":
            result = bridge_file(
                args.capture, pages_dir=args.pages_dir, out_path=args.out
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
    except (HSLCAProofBridgeError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": str(exc),
                    "authority_advanced": False,
                    "h_id_allocations": 0,
                    "outbound": "CLOSED",
                    "send_allowed": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
