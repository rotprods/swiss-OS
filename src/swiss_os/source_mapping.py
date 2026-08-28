from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

from .ingest_packet import (
    IngestDecision,
    MATCHED_EXISTING,
    RECONCILE,
    REVIEW_UNKNOWN,
    VERIFY_NEW,
)


class SourceMappingError(ValueError):
    """Raised when a complete source-record mapping candidate cannot be built."""


ALLOWED_MAPPING_STATES = frozenset(
    {
        "ACTIVE_CANONICAL",
        "ALIAS_TO_CANONICAL",
        "EXCLUDED_WITH_REASON",
        "RECONCILE_REQUIRED",
    }
)


def _sha256(payload: object) -> str:
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


def _extract_raw_decisions(payload: object) -> list[Mapping[str, object]]:
    if isinstance(payload, list):
        raw = payload
    elif isinstance(payload, Mapping):
        raw = payload.get("decisions")
        if raw is None and isinstance(payload.get("result"), Mapping):
            raw = payload["result"].get("decisions")
        if raw is None and isinstance(payload.get("payload"), Mapping):
            raw = payload["payload"].get("decisions")
    else:
        raw = None
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        raise SourceMappingError("CMI payload must contain a decisions array of objects")
    return list(raw)


def _verification_index(
    verified: object, requeue: object
) -> dict[str, Mapping[str, object]]:
    combined: list[Mapping[str, object]] = []
    for label, payload in (("verified", verified), ("requeue", requeue)):
        if not isinstance(payload, list) or not all(
            isinstance(item, Mapping) for item in payload
        ):
            raise SourceMappingError(f"{label} verification file must be an array of objects")
        combined.extend(payload)
    index: dict[str, Mapping[str, object]] = {}
    for item in combined:
        key = str(item.get("source_record_key", "")).strip()
        if not key:
            raise SourceMappingError("verification result has empty source_record_key")
        if key in index:
            raise SourceMappingError(f"duplicate verification source_record_key: {key}")
        index[key] = item
    return index


def _reconcile_reason(decision: IngestDecision, verification: Mapping[str, object] | None) -> str:
    if verification is None:
        return "MISSING_EXACT_CURRENT_VERIFICATION"
    state = str(verification.get("verification_state", "UNKNOWN")).strip()
    if state != "CURRENT_DETAIL_VERIFIED":
        return f"EXACT_CURRENT_{state or 'UNKNOWN'}"
    if decision.work_state == RECONCILE:
        return "CURRENT_VERIFIED_CANONICAL_CONFLICT"
    if decision.work_state == VERIFY_NEW:
        return "CURRENT_VERIFIED_NEW_ENTITY_AWAITING_CANONICAL_REVIEW"
    if decision.work_state == REVIEW_UNKNOWN:
        return "CURRENT_VERIFIED_UNKNOWN_CMI_DECISION"
    return "CURRENT_VERIFIED_REVIEW_REQUIRED"


def build_source_mapping_candidate(
    cmi_payload: object,
    verified_results: object,
    requeue_results: object,
    *,
    snapshot_id: str,
    source_manifest_sha256: str,
    source_scope_state: str = "DIRECTORY_COMPLETE_SSR_PENDING",
) -> dict[str, object]:
    if not snapshot_id.strip():
        raise SourceMappingError("snapshot_id must be non-empty")
    if len(source_manifest_sha256) != 64:
        raise SourceMappingError("source_manifest_sha256 must be a 64-character digest")

    raw_decisions = _extract_raw_decisions(cmi_payload)
    decisions = tuple(
        IngestDecision.from_mapping(item, index)
        for index, item in enumerate(raw_decisions, start=1)
    )
    decision_keys = [decision.source_record_key for decision in decisions]
    if len(decision_keys) != len(set(decision_keys)):
        raise SourceMappingError("CMI decisions contain duplicate source_record_key values")

    verification = _verification_index(verified_results, requeue_results)
    active_keys = {
        decision.source_record_key
        for decision in decisions
        if decision.work_state != MATCHED_EXISTING
    }
    extra_verification = sorted(set(verification) - active_keys)
    if extra_verification:
        raise SourceMappingError(
            "verification results include non-active source keys: "
            + ", ".join(extra_verification[:10])
        )

    mappings: list[dict[str, object]] = []
    for decision in sorted(decisions, key=lambda item: item.source_record_key):
        if decision.work_state == MATCHED_EXISTING:
            if not decision.matched_hotel_id:
                raise SourceMappingError(
                    f"terminal match lacks canonical hotel ID: {decision.source_record_key}"
                )
            mapping_state = "ACTIVE_CANONICAL"
            canonical_hotel_id = decision.matched_hotel_id
            reason_code = "CMI_EXISTING_CANONICAL_MATCH"
            current_evidence_verified = True
            verification_state = "NOT_REQUIRED_FOR_EXISTING_MATCH"
            evidence_ref = "CMI_ANTI_JOIN"
        else:
            result = verification.get(decision.source_record_key)
            mapping_state = "RECONCILE_REQUIRED"
            canonical_hotel_id = ""
            reason_code = _reconcile_reason(decision, result)
            verification_state = (
                str(result.get("verification_state", "MISSING")) if result else "MISSING"
            )
            current_evidence_verified = verification_state == "CURRENT_DETAIL_VERIFIED"
            response_sha = str(result.get("response_sha256", "")) if result else ""
            evidence_ref = (
                f"EXACT_CURRENT_SHA256:{response_sha}"
                if response_sha
                else "EXACT_CURRENT_EVIDENCE_PENDING"
            )
        mappings.append(
            {
                "source_record_key": decision.source_record_key,
                "name": decision.name,
                "city": decision.city,
                "detail_url": decision.detail_url,
                "cmi_decision": decision.decision,
                "cmi_work_state": decision.work_state,
                "mapping_state": mapping_state,
                "canonical_hotel_id": canonical_hotel_id,
                "reason_code": reason_code,
                "current_evidence_verified": current_evidence_verified,
                "verification_state": verification_state,
                "evidence_ref": evidence_ref,
            }
        )

    counts = {
        state: sum(1 for item in mappings if item["mapping_state"] == state)
        for state in sorted(ALLOWED_MAPPING_STATES)
    }
    unmapped_records = len(decisions) - len(mappings)
    terminal_mappings = (
        counts["ACTIVE_CANONICAL"]
        + counts["ALIAS_TO_CANONICAL"]
        + counts["EXCLUDED_WITH_REASON"]
    )
    candidate: dict[str, object] = {
        "schema_version": "CRM-SOURCE-MAPPING-CANDIDATE-1.0",
        "snapshot_id": snapshot_id,
        "source_manifest_sha256": source_manifest_sha256,
        "source_scope_state": source_scope_state,
        "source_records": len(decisions),
        "mappings_count": len(mappings),
        "unmapped_records": unmapped_records,
        "counts_by_mapping_state": counts,
        "terminal_mappings": terminal_mappings,
        "reconcile_required": counts["RECONCILE_REQUIRED"],
        "terminal_mapping_coverage_pct": (
            0.0 if not decisions else terminal_mappings / len(decisions)
        ),
        "mappings": mappings,
        "mapping_sha256": _sha256(mappings),
        "crm_universe_complete": False,
        "crm_completion_blockers": [
            "SOURCE_SCOPE_SSR_PENDING",
            "RECONCILE_REQUIRED_NOT_ZERO"
            if counts["RECONCILE_REQUIRED"]
            else "AUTHORITY_CROSS_PLANE_RECONCILIATION_PENDING",
        ],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "candidate_sha256": "",
    }
    candidate["candidate_sha256"] = _sha256(
        {key: value for key, value in candidate.items() if key != "candidate_sha256"}
    )
    return candidate


def validate_source_mapping_candidate(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != "CRM-SOURCE-MAPPING-CANDIDATE-1.0":
        violations.append("INVALID_SCHEMA_VERSION")
    if bool(payload.get("crm_universe_complete")):
        violations.append("CRM_COMPLETE_FORBIDDEN_FOR_CANDIDATE")
    if bool(payload.get("authority_advanced")):
        violations.append("AUTHORITY_ADVANCED_FORBIDDEN")
    if int(payload.get("h_id_allocations", 0)) != 0:
        violations.append("H_ID_ALLOCATIONS_FORBIDDEN")
    if payload.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")
    if int(payload.get("send_allowed", 0)) != 0:
        violations.append("SEND_ALLOWED_NOT_ZERO")
    mappings = payload.get("mappings")
    if not isinstance(mappings, list):
        violations.append("MAPPINGS_NOT_ARRAY")
        mappings = []
    if int(payload.get("mappings_count", -1)) != len(mappings):
        violations.append("MAPPING_COUNT_MISMATCH")
    if int(payload.get("source_records", -1)) - len(mappings) != int(
        payload.get("unmapped_records", -1)
    ):
        violations.append("UNMAPPED_COUNT_MISMATCH")
    keys: set[str] = set()
    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            violations.append("MAPPING_NOT_OBJECT")
            continue
        key = str(mapping.get("source_record_key", "")).strip()
        state = str(mapping.get("mapping_state", "")).strip()
        if not key:
            violations.append("EMPTY_SOURCE_RECORD_KEY")
        elif key in keys:
            violations.append("DUPLICATE_SOURCE_RECORD_KEY")
        keys.add(key)
        if state not in ALLOWED_MAPPING_STATES:
            violations.append("INVALID_MAPPING_STATE")
        if state in {"ACTIVE_CANONICAL", "ALIAS_TO_CANONICAL"} and not str(
            mapping.get("canonical_hotel_id", "")
        ).strip():
            violations.append("CANONICAL_MAPPING_WITHOUT_TARGET")
        if state == "RECONCILE_REQUIRED" and str(
            mapping.get("canonical_hotel_id", "")
        ).strip():
            violations.append("RECONCILE_MAPPING_HAS_CANONICAL_TARGET")
    if payload.get("mapping_sha256") != _sha256(mappings):
        violations.append("MAPPING_SHA_MISMATCH")
    expected = _sha256(
        {key: value for key, value in payload.items() if key != "candidate_sha256"}
    )
    if payload.get("candidate_sha256") != expected:
        violations.append("CANDIDATE_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.source_mapping")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("cmi_payload")
    build.add_argument("verified_results")
    build.add_argument("requeue_results")
    build.add_argument("--snapshot-id", required=True)
    build.add_argument("--source-manifest-sha256", required=True)
    build.add_argument("--source-scope-state", default="DIRECTORY_COMPLETE_SSR_PENDING")
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            candidate = build_source_mapping_candidate(
                _read_json(args.cmi_payload),
                _read_json(args.verified_results),
                _read_json(args.requeue_results),
                snapshot_id=args.snapshot_id,
                source_manifest_sha256=args.source_manifest_sha256,
                source_scope_state=args.source_scope_state,
            )
            _write_json(args.out, candidate)
            print(json.dumps({
                "valid": True,
                "snapshot_id": candidate["snapshot_id"],
                "source_records": candidate["source_records"],
                "mappings_count": candidate["mappings_count"],
                "unmapped_records": candidate["unmapped_records"],
                "counts_by_mapping_state": candidate["counts_by_mapping_state"],
                "terminal_mapping_coverage_pct": candidate["terminal_mapping_coverage_pct"],
                "crm_universe_complete": False,
                "candidate_sha256": candidate["candidate_sha256"],
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound": "CLOSED",
                "send_allowed": 0,
                "out": args.out,
            }, indent=2, sort_keys=True))
            return 0
        raw = _read_json(args.path)
        if not isinstance(raw, Mapping):
            raise SourceMappingError("candidate must be a JSON object")
        violations = validate_source_mapping_candidate(raw)
        print(json.dumps({
            "valid": not violations,
            "violations": list(violations),
            "candidate_sha256": raw.get("candidate_sha256"),
        }, indent=2, sort_keys=True))
        return 0 if not violations else 2
    except (SourceMappingError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
