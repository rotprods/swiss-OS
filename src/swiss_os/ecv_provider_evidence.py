from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping


NORMALIZER_VERSION = "ECV-PROVIDER-EVIDENCE-1.0"
PROVIDER_CHANGE_REVIEW = "PROVIDER_RECORD_CHANGE_REVIEW"
URL_NOT_FOUND = "CURRENT_DETAIL_URL_NOT_FOUND"
IDENTITY_DRIFT_STATES = {
    "CURRENT_DETAIL_NAME_ONLY",
    "CURRENT_DETAIL_CITY_ONLY",
    "CURRENT_DETAIL_MISMATCH",
}
TERMINAL_EVIDENCE_STATES = {
    "CURRENT_DETAIL_VERIFIED",
    URL_NOT_FOUND,
    *IDENTITY_DRIFT_STATES,
}


class ProviderEvidenceError(ValueError):
    """Raised when an ECV packet cannot be normalized safely."""


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _is_repeat_http_404(error: object) -> bool:
    text = str(error or "")
    if "fetch failed:" not in text:
        return False
    attempts = [
        part.strip()
        for part in text.split("fetch failed:", 1)[1].split(";")
        if part.strip()
    ]
    if not attempts:
        return False
    return all("HTTPError: HTTP Error 404: Not Found" in part for part in attempts)


def normalize_packet(payload: Mapping[str, object]) -> dict[str, object]:
    """Convert deterministic provider-record changes into terminal pre-authority evidence.

    This normalizer is deliberately narrow. It never turns a missing detail URL or an
    identity mismatch into hotel absence, novelty, exclusion, aliasing, a terminal
    canonical mapping, or an H-ID allocation. It only prevents deterministic provider
    record changes from being treated as transient network failures forever.
    """

    if payload.get("schema_version") != "EXACT-CURRENT-VERIFY-1.0":
        raise ProviderEvidenceError("unsupported ECV schema_version")
    if bool(payload.get("authority_advanced")):
        raise ProviderEvidenceError("authority_advanced must remain false")
    if int(payload.get("h_id_allocations", 0)) != 0:
        raise ProviderEvidenceError("h_id_allocations must remain zero")
    if payload.get("outbound") != "CLOSED":
        raise ProviderEvidenceError("OUTBOUND must remain CLOSED")
    if int(payload.get("send_allowed", 0)) != 0:
        raise ProviderEvidenceError("send_allowed must remain zero")

    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise ProviderEvidenceError("results must be an array")

    results: list[dict[str, object]] = []
    for raw in raw_results:
        if not isinstance(raw, Mapping):
            raise ProviderEvidenceError("every result must be an object")
        result = dict(raw)
        state = str(result.get("verification_state", ""))
        if state == "FETCH_FAILED" and _is_repeat_http_404(result.get("error")):
            result["verification_state"] = URL_NOT_FOUND
            result["followup"] = PROVIDER_CHANGE_REVIEW
            result["evidence_semantics"] = (
                "DETAIL_URL_RETURNED_HTTP_404_ON_ALL_FETCH_ATTEMPTS"
            )
        elif state in IDENTITY_DRIFT_STATES:
            result["followup"] = PROVIDER_CHANGE_REVIEW
            result["evidence_semantics"] = "CURRENT_DETAIL_IDENTITY_DRIFT"
        results.append(result)

    counts: dict[str, int] = {}
    for result in results:
        state = str(result.get("verification_state", ""))
        counts[state] = counts.get(state, 0) + 1

    terminal_evidence_count = sum(
        count for state, count in counts.items() if state in TERMINAL_EVIDENCE_STATES
    )
    normalized = dict(payload)
    normalized["results"] = results
    normalized["results_count"] = len(results)
    normalized["counts_by_state"] = counts
    normalized["all_verified"] = counts.get("CURRENT_DETAIL_VERIFIED", 0) == len(results)
    normalized["all_terminal"] = terminal_evidence_count == len(results)
    normalized["terminal_evidence_count"] = terminal_evidence_count
    normalized["provider_record_change_count"] = sum(
        counts.get(state, 0)
        for state in {URL_NOT_FOUND, *IDENTITY_DRIFT_STATES}
    )
    normalized["evidence_normalizer"] = NORMALIZER_VERSION
    normalized["packet_sha256"] = ""
    normalized["packet_sha256"] = _sha256_json(
        {key: value for key, value in normalized.items() if key != "packet_sha256"}
    )
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.ecv_provider_evidence")
    parser.add_argument("path")
    parser.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw = _read_json(args.path)
        if not isinstance(raw, Mapping):
            raise ProviderEvidenceError("ECV packet must be a JSON object")
        normalized = normalize_packet(raw)
        _write_json(args.out, normalized)
        print(
            json.dumps(
                {
                    "valid": True,
                    "normalizer": NORMALIZER_VERSION,
                    "counts_by_state": normalized["counts_by_state"],
                    "all_verified": normalized["all_verified"],
                    "all_terminal": normalized["all_terminal"],
                    "terminal_evidence_count": normalized["terminal_evidence_count"],
                    "provider_record_change_count": normalized[
                        "provider_record_change_count"
                    ],
                    "packet_sha256": normalized["packet_sha256"],
                    "out": args.out,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except (ProviderEvidenceError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
