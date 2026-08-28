from __future__ import annotations

"""Run HSLCA checkpoint capture with the canonical MDC-1.1 card parser.

The repository contains two intentionally different layers:

- HSLCA owns resumable page checkpoints and coherent capture envelopes.
- MDC owns the live HotellerieSuisse card identity semantics.

HSLCA predates MDC-1.1 and its embedded legacy card parser can misread live cards
whose anchor renders locality first and property name last. This adapter keeps the
HSLCA checkpoint/PCF lineage intact while delegating record identity extraction to
the canonical MDC parser. It is pre-authority plumbing only.
"""

import argparse
import json
import sys
from typing import Any

from . import hotelleriesuisse_capture as hslca
from .hotelleriesuisse_capture_runtime import AdaptiveHtmlFetcher, HSLCAAccessError
from .member_directory_capture import parse_directory_page


def extract_records_with_mdc(
    html: str,
    *,
    page_url: str,
    page_id: str,
    page_position: int,
) -> list[dict[str, Any]]:
    """Translate canonical MDC-1.1 cards into the HSLCA record envelope."""

    parsed = parse_directory_page(html.encode("utf-8"), page_url)
    if parsed.rejects:
        reasons = sorted(
            {
                str(item.get("reason_code", "UNKNOWN"))
                for item in parsed.rejects
                if isinstance(item, dict)
            }
        )
        raise hslca.DirectoryCaptureError(
            f"MDC rejected {len(parsed.rejects)} card(s) at page {page_position}: "
            + ",".join(reasons)
        )
    if not parsed.cards:
        raise hslca.DirectoryCaptureError(
            f"MDC found no directory records at page {page_position}: {page_url}"
        )

    records: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for card in parsed.cards:
        if card.detail_url in seen_urls:
            raise hslca.DirectoryCaptureError(
                f"duplicate MDC detail URL at page {page_position}: {card.detail_url}"
            )
        seen_urls.add(card.detail_url)
        records.append(
            {
                "name": card.name,
                "city": card.city,
                "hs_id": "",
                "detail_url": card.detail_url,
                "source_url": page_url,
                "evidence_ref": f"{page_id}#record-{len(records) + 1:03d}",
            }
        )
    return records


def run_capture(
    *,
    capture_id: str,
    root_url: str,
    locale: str,
    output_dir: str,
    delay_seconds: float = 6.0,
    timeout_seconds: float = 45.0,
    attempts: int = 6,
    base_backoff_seconds: float = 15.0,
    max_backoff_seconds: float = 120.0,
) -> tuple[dict[str, object], dict[str, object]]:
    """Execute HSLCA with canonical MDC identity semantics for this process."""

    config = hslca.CaptureConfig(
        capture_id=capture_id,
        locale=locale,
        root_url=root_url,
        delay_seconds=delay_seconds,
        timeout_seconds=timeout_seconds,
        retries=1,
        resume=True,
    )
    fetcher = AdaptiveHtmlFetcher(
        timeout_seconds=timeout_seconds,
        attempts=attempts,
        base_backoff_seconds=base_backoff_seconds,
        max_backoff_seconds=max_backoff_seconds,
    )

    original = hslca.extract_directory_records
    hslca.extract_directory_records = extract_records_with_mdc
    try:
        return hslca.capture_directory(config, output_dir=output_dir, fetcher=fetcher)
    finally:
        hslca.extract_directory_records = original


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.hslca_mdc_runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--capture-id", required=True)
    capture.add_argument("--root-url", required=True)
    capture.add_argument("--locale", default="de")
    capture.add_argument("--out-dir", required=True)
    capture.add_argument("--delay", type=float, default=6.0)
    capture.add_argument("--timeout", type=float, default=45.0)
    capture.add_argument("--attempts", type=int, default=6)
    capture.add_argument("--base-backoff", type=float, default=15.0)
    capture.add_argument("--max-backoff", type=float, default=120.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        capture, manifest = run_capture(
            capture_id=args.capture_id,
            root_url=args.root_url,
            locale=args.locale,
            output_dir=args.out_dir,
            delay_seconds=args.delay,
            timeout_seconds=args.timeout,
            attempts=args.attempts,
            base_backoff_seconds=args.base_backoff,
            max_backoff_seconds=args.max_backoff,
        )
        summary = {
            "capture_id": capture.get("capture_id"),
            "capture_mode": capture.get("capture_mode"),
            "coverage_claim": capture.get("coverage_claim"),
            "capture_violations": capture.get("capture_violations"),
            "records_count": manifest.get("records_count"),
            "coverage_complete": manifest.get("coverage_complete"),
            "manifest_violations": manifest.get("violations"),
            "identity_parser": "MDC-1.1",
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if manifest.get("coverage_complete") is True else 2
    except (HSLCAAccessError, hslca.DirectoryCaptureError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": str(exc),
                    "identity_parser": "MDC-1.1",
                    "authority_advanced": False,
                    "h_id_allocations": 0,
                    "outbound_opened": False,
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
