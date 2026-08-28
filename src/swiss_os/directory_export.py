from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping

from .member_directory import validate_member_directory_manifest


class DirectoryExportError(ValueError):
    """Raised when an MDM manifest is not eligible for CMI canary export."""


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def _sha256_payload(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _strict_bool(manifest: Mapping[str, object], field: str) -> bool:
    value = manifest.get(field)
    if type(value) is not bool:
        raise DirectoryExportError(f"{field} must be a JSON boolean")
    return value


def _strict_int(manifest: Mapping[str, object], field: str) -> int:
    value = manifest.get(field)
    if type(value) is not int:
        raise DirectoryExportError(f"{field} must be a JSON integer")
    return value


def export_directory_to_cmi(
    manifest: Mapping[str, object],
) -> tuple[list[dict[str, str]], dict[str, object]]:
    # Security-critical gate fields are type-strict. Do not allow JSON strings or
    # booleans to be coerced through bool()/int() before transfer validation.
    coverage_complete = _strict_bool(manifest, "coverage_complete")
    authority_advanced = _strict_bool(manifest, "authority_advanced")
    outbound_opened = _strict_bool(manifest, "outbound_opened")
    h_id_allocations = _strict_int(manifest, "h_id_allocations")
    send_allowed = _strict_int(manifest, "send_allowed")
    records_count = _strict_int(manifest, "records_count")

    transfer_violations = validate_member_directory_manifest(manifest)
    if transfer_violations:
        raise DirectoryExportError(
            "member-directory manifest failed transfer validation: "
            + ", ".join(transfer_violations)
        )
    if manifest.get("schema_version") != "MEMBER-DIRECTORY-1.0":
        raise DirectoryExportError("unsupported member-directory schema")
    if not coverage_complete:
        raise DirectoryExportError("coverage_complete=true is required")
    declared_violations = manifest.get("violations", [])
    if declared_violations:
        raise DirectoryExportError("complete manifest cannot contain semantic violations")
    if manifest.get("source_provider") != "HOTELLERIESUISSE_MEMBER_DIRECTORY":
        raise DirectoryExportError(
            "source_provider must be HOTELLERIESUISSE_MEMBER_DIRECTORY"
        )
    if authority_advanced:
        raise DirectoryExportError("input manifest must remain pre-authority")
    if h_id_allocations != 0:
        raise DirectoryExportError("input manifest cannot allocate H-IDs")
    if outbound_opened:
        raise DirectoryExportError("input manifest cannot open outbound")
    if send_allowed != 0:
        raise DirectoryExportError("input manifest must keep send_allowed=0")

    raw_records = manifest.get("records")
    if not isinstance(raw_records, list):
        raise DirectoryExportError("manifest records must be an array")
    if records_count != len(raw_records):
        raise DirectoryExportError("manifest records_count does not match records")

    exported: list[dict[str, str]] = []
    provider_keys: set[str] = set()
    detail_urls: set[str] = set()
    for index, raw in enumerate(raw_records):
        if not isinstance(raw, Mapping):
            raise DirectoryExportError(f"record {index} must be an object")
        record_id = str(raw.get("record_id", "")).strip()
        name = str(raw.get("name", "")).strip()
        city = str(raw.get("city", "")).strip()
        detail_url = str(raw.get("detail_url", "")).strip()
        if not all((record_id, name, city, detail_url)):
            raise DirectoryExportError(
                f"record {index} requires record_id/name/city/detail_url"
            )
        if record_id in provider_keys:
            raise DirectoryExportError(f"duplicate provider record key: {record_id}")
        if detail_url in detail_urls:
            raise DirectoryExportError(f"duplicate detail URL: {detail_url}")
        provider_keys.add(record_id)
        detail_urls.add(detail_url)
        exported.append(
            {
                "source_url": detail_url,
                "raw_name": name,
                "raw_city": city,
                "detail_url": detail_url,
                "provider_record_key": record_id,
            }
        )

    exported.sort(key=lambda row: row["provider_record_key"])
    records_sha256 = _sha256_payload(exported)
    attestation: dict[str, object] = {
        "schema_version": "DIRECTORY-TO-CMI-1.0",
        "snapshot_id": manifest.get("snapshot_id"),
        "source_manifest_sha256": manifest.get("manifest_sha256"),
        "source_records_sha256": manifest.get("records_sha256"),
        "exported_records": len(exported),
        "exported_records_sha256": records_sha256,
        "provider_record_keys_unique": True,
        "detail_urls_unique": True,
        "coverage_complete_input": True,
        "ssr_pending": True,
        "candidate_snapshot_state": "DIRECTORY_COMPLETE_SSR_PENDING",
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "allowed_next_use": "CMI_NON_AUTHORITATIVE_ANTI_JOIN_AND_SCHEDULING",
        "forbidden_next_use": [
            "AUTHORITATIVE_CANONICAL_PROMOTION",
            "CRM_UNIVERSE_COMPLETE",
            "OUTBOUND_OPEN",
        ],
    }
    attestation["attestation_sha256"] = _sha256_payload(attestation)
    return exported, attestation


def export_files(
    manifest_path: str | Path,
    records_out: str | Path,
    attestation_out: str | Path,
) -> dict[str, object]:
    payload = _read_json(manifest_path)
    if not isinstance(payload, Mapping):
        raise DirectoryExportError("manifest must be a JSON object")
    records, attestation = export_directory_to_cmi(payload)
    _write_json(records_out, records)
    _write_json(attestation_out, attestation)
    return attestation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.directory_export")
    parser.add_argument("manifest")
    parser.add_argument("--records-out", required=True)
    parser.add_argument("--attestation-out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        attestation = export_files(
            args.manifest, args.records_out, args.attestation_out
        )
        print(json.dumps(attestation, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (DirectoryExportError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
