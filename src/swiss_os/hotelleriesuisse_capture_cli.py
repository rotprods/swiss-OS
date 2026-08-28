"""CLI for resumable public HotellerieSuisse directory capture."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys

from .hotelleriesuisse_capture import (
    CaptureConfig,
    DirectoryCaptureError,
    capture_directory,
)


DEFAULT_ROOTS = {
    "de": (
        "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/"
        "mitglieder/mitgliederverzeichnis"
    ),
    "fr": (
        "https://www.hotelleriesuisse.ch/fr/association-et-siege-admin/"
        "membres/liste-des-membres"
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m swiss_os.hotelleriesuisse_capture_cli"
    )
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--capture-id")
    parser.add_argument("--locale", choices=sorted(DEFAULT_ROOTS), default="de")
    parser.add_argument("--root-url")
    parser.add_argument("--expected-pages", type=int)
    parser.add_argument("--reported-records", type=int)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--no-resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    capture_id = args.capture_id or (
        "HS-"
        + args.locale.upper()
        + "-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    config = CaptureConfig(
        capture_id=capture_id,
        locale=args.locale,
        root_url=args.root_url or DEFAULT_ROOTS[args.locale],
        expected_pages=args.expected_pages,
        reported_records=args.reported_records,
        delay_seconds=args.delay,
        timeout_seconds=args.timeout,
        retries=args.retries,
        resume=not args.no_resume,
    )
    try:
        capture, manifest = capture_directory(config, output_dir=args.out_dir)
    except (DirectoryCaptureError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "capture_valid": False,
                    "coverage_complete": False,
                    "authority_advanced": False,
                    "h_id_allocations": 0,
                    "outbound_opened": False,
                    "send_allowed": 0,
                    "error": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    result = {
        "capture_id": capture["capture_id"],
        "capture_mode": capture["capture_mode"],
        "capture_violations": capture["capture_violations"],
        "expected_pages": capture["expected_pages"],
        "reported_records": capture["reported_records"],
        "observed_pages": manifest["observed_pages"],
        "records_count": manifest["records_count"],
        "capture_valid": manifest["capture_valid"],
        "coverage_complete": manifest["coverage_complete"],
        "records_sha256": manifest["records_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
        "out_dir": args.out_dir,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if manifest["coverage_complete"] else 2


if __name__ == "__main__":
    sys.exit(main())
