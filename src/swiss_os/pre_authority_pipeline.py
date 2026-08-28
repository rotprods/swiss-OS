from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

from .candidate_export import export_candidate_ingest_records
from .directory_coverage import build_directory_coverage_plan
from .member_directory_manifest import compile_member_directory_manifest
from .source_scope import ScopeExplanation, build_candidate_snapshot, reconcile_source_scope


def _stable_sha(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_pre_authority_bundle(api_manifest: Mapping[str, Any], directory_observations: Iterable[Mapping[str, Any]], *, directory_snapshot_id: str, directory_observed_at: str, locale: str, epoch: str, expected_pages: int, declared_raw_records: int, conflict_pages: Iterable[int] = (), explanations: tuple[ScopeExplanation, ...] = ()) -> dict[str, Any]:
    rows = [dict(item) for item in directory_observations]
    coverage = build_directory_coverage_plan(rows, locale=locale, epoch=epoch, expected_pages=expected_pages, conflict_pages=conflict_pages)
    directory_manifest = compile_member_directory_manifest(rows, snapshot_id=directory_snapshot_id, observed_at=directory_observed_at, expected_pages=expected_pages, declared_raw_records=declared_raw_records)
    blockers: list[str] = []
    if not bool(api_manifest.get("capture_valid", False)):
        blockers.append("API_CAPTURE_INVALID")
    if not bool(directory_manifest.get("coverage_complete", False)):
        blockers.append("MEMBER_DIRECTORY_INCOMPLETE")
    if not bool(coverage.get("complete", False)):
        blockers.append("DIRECTORY_COVERAGE_WORK_REMAINS")
    candidate: dict[str, Any] | None = None
    reconciliation: dict[str, Any] | None = None
    ingest_records: list[dict[str, str]] = []
    if not blockers:
        result = reconcile_source_scope(api_manifest, directory_manifest, explanations)
        reconciliation = result.as_dict()
        candidate = build_candidate_snapshot(api_manifest, directory_manifest, result, explanations)
        if not candidate["crm_freeze_eligible"]:
            blockers.append("SOURCE_SCOPE_UNRESOLVED")
        else:
            ingest_records = export_candidate_ingest_records(candidate, api_manifest)
    state = "FROZEN_CANDIDATE_READY" if not blockers and candidate is not None else "BLOCKED_PRE_AUTHORITY"
    bundle: dict[str, Any] = {
        "schema_version": "swiss-os-pre-authority-bundle-v1",
        "state": state,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "api_snapshot_id": str(api_manifest.get("snapshot_id", "") or ""),
        "directory_snapshot_id": directory_snapshot_id,
        "coverage": coverage,
        "directory_manifest": directory_manifest,
        "reconciliation": reconciliation,
        "candidate_snapshot": candidate,
        "ingest_records": ingest_records,
        "ingest_records_count": len(ingest_records),
        "blockers": sorted(set(blockers)),
    }
    bundle["bundle_sha256"] = _stable_sha(bundle)
    return bundle


def write_bundle_artifacts(bundle: Mapping[str, Any], out_dir: str | Path) -> dict[str, str]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, object] = {
        "pre_authority_bundle.json": dict(bundle),
        "directory_manifest.json": bundle.get("directory_manifest"),
        "coverage_plan.json": bundle.get("coverage"),
        "candidate_snapshot.json": bundle.get("candidate_snapshot"),
        "ingest_records.json": bundle.get("ingest_records", []),
    }
    written: dict[str, str] = {}
    for name, payload in artifacts.items():
        path = target / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written[name] = str(path)
    return written


def _read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.pre_authority_pipeline")
    parser.add_argument("api_manifest")
    parser.add_argument("directory_observations")
    parser.add_argument("--directory-snapshot-id", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--locale", required=True)
    parser.add_argument("--epoch", required=True)
    parser.add_argument("--expected-pages", type=int, required=True)
    parser.add_argument("--declared-raw-records", type=int, required=True)
    parser.add_argument("--conflict-pages")
    parser.add_argument("--explanations")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    api = _read_json(args.api_manifest)
    observations = _read_json(args.directory_observations)
    if not isinstance(api, dict):
        raise ValueError("api_manifest must be a JSON object")
    if not isinstance(observations, list) or not all(isinstance(item, dict) for item in observations):
        raise ValueError("directory_observations must be a JSON array of objects")
    conflicts: list[int] = []
    if args.conflict_pages:
        raw = _read_json(args.conflict_pages)
        if not isinstance(raw, list):
            raise ValueError("conflict_pages must be a JSON array")
        conflicts = [int(item) for item in raw]
    explanations: tuple[ScopeExplanation, ...] = ()
    if args.explanations:
        raw = _read_json(args.explanations)
        if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
            raise ValueError("explanations must be a JSON array of objects")
        explanations = tuple(ScopeExplanation.from_mapping(item) for item in raw)
    bundle = build_pre_authority_bundle(api, observations, directory_snapshot_id=args.directory_snapshot_id, directory_observed_at=args.observed_at, locale=args.locale, epoch=args.epoch, expected_pages=args.expected_pages, declared_raw_records=args.declared_raw_records, conflict_pages=conflicts, explanations=explanations)
    written = write_bundle_artifacts(bundle, args.out_dir)
    summary = {
        "state": bundle["state"],
        "bundle_sha256": bundle["bundle_sha256"],
        "coverage_pct": bundle["coverage"]["coverage_pct"],
        "coverage_tasks": len(bundle["coverage"]["tasks"]),
        "crm_freeze_eligible": bool((bundle.get("candidate_snapshot") or {}).get("crm_freeze_eligible", False)),
        "ingest_records_count": bundle["ingest_records_count"],
        "blockers": bundle["blockers"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "artifacts": written,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if bundle["state"] == "FROZEN_CANDIDATE_READY" else 2


if __name__ == "__main__":
    sys.exit(main())
