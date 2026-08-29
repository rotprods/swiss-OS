from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from .cwp_lineage_guard import (
    CwpLineageError,
    _load_multipart_candidate_export,
    _sha256_json,
    validate_candidate_export,
)


def materialize_candidate_export(
    root: Path,
    manifest_path: Path,
    out_dir: Path,
) -> Mapping[str, Any]:
    """Materialize and validate the committed multipart candidate export.

    This is a read-only recovery bridge for CP-R01. It never allocates H-IDs,
    advances authority, or opens outbound. The materialized payload is intended
    for ephemeral workflow/local use and is not written back to repository state.
    """

    root = root.resolve()
    manifest_path = manifest_path.resolve()
    out_dir = out_dir.resolve()
    payload, gzip_sha, manifest = _load_multipart_candidate_export(root, manifest_path)

    errors = validate_candidate_export(payload)
    if errors:
        raise CwpLineageError("CANDIDATE_EXPORT_VALIDATION_FAILED:" + ",".join(errors))

    records = payload.get("records")
    if not isinstance(records, list):
        raise CwpLineageError("CANDIDATE_RECORDS_NOT_ARRAY")
    records_sha = _sha256_json(records)
    if records_sha != manifest.get("records_sha256"):
        raise CwpLineageError("CANDIDATE_EXPORT_RECORDS_SHA_MISMATCH")

    out_dir.mkdir(parents=True, exist_ok=True)
    payload_path = out_dir / "CRM_CANDIDATE_EXPORT.json"
    report_path = out_dir / "CANDIDATE_EXPORT_MATERIALIZE_REPORT.json"

    payload_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    report: dict[str, Any] = {
        "schema_version": "CRM-CANDIDATE-EXPORT-MATERIALIZE-1.0",
        "manifest_path": str(manifest_path.relative_to(root)),
        "snapshot_id": manifest.get("snapshot_id"),
        "records_count": len(records),
        "records_sha256": records_sha,
        "gzip_sha256": gzip_sha,
        "source_records": payload.get("source_records"),
        "exact_name_city_matches": payload.get("exact_name_city_matches"),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "materialized_payload": payload_path.name,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize the durable CRM candidate export")
    parser.add_argument(
        "--manifest",
        default="docs/state/CRM_CANDIDATE_EXPORT_33206402141.manifest.json",
        help="Repository-relative multipart manifest path",
    )
    parser.add_argument("--out-dir", default=".artifacts", help="Ephemeral output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    manifest_path = (root / args.manifest).resolve()
    out_dir = (root / args.out_dir).resolve()
    try:
        report = materialize_candidate_export(root, manifest_path, out_dir)
    except CwpLineageError as exc:
        print("candidate_export_materialize: FAIL")
        print(f"- {exc}")
        return 1
    print("candidate_export_materialize: PASS")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
