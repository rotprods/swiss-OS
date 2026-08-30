#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "CRM-LOWER49-PREAUTH-WORKSET-1.0"
PROJECT = "SWITZERLAND_JOB_OS"
SNAPSHOT = "HS-MEMBER-DE-33206402141"
AUTHORITY_EPOCH = "HS_ENTITY_EPOCH_2026-08-25_E4"
AUTHORITY_SHA256 = "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
CLAIM_ID = "CLAIM-CRM-SRR-SPECIAL-006"
FENCING_TOKEN = 6
QUEUE = "docs/state/SRET_PROVIDER_IDENTITY_LOWER49_33206402141.json"
PRECHECK = "docs/recovery/PIE050_LOWER49_COMPLETION_PRECHECK_2026-08-30.json"
PACKETS = [
    f"docs/state/PIE050_LOWER49_REVIEW_PACKET_{index:02d}_2026-08-30.json"
    for index in range(1, 6)
]
EXPECTED_SPECIAL_KEYS = {
    "MD-33d867e983644585e4b2",  # Neu-Schönstatt, handled separately
    "MD-7976c173678dc89c9cf0",  # Delta Resort Apartments, handled by EGR-1.0
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load(root: Path, rel: str) -> Mapping[str, Any]:
    value = json.loads((root / rel).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{rel}: expected JSON object")
    return value


def compile_workset(root: Path, *, parent_main_sha: str) -> dict[str, Any]:
    queue = load(root, QUEUE)
    precheck = load(root, PRECHECK)
    if queue.get("items_count") != 49:
        raise ValueError("lower49 queue must contain exactly 49 records")
    if queue.get("authority_advanced") is not False or queue.get("h_id_allocations") != 0:
        raise ValueError("queue is not fail-closed")
    if queue.get("canonical_id_reservation_allowed") is not False:
        raise ValueError("queue permits canonical ID reservation")
    queue_keys = set(queue.get("source_record_keys", []))
    if len(queue_keys) != 49:
        raise ValueError("lower49 queue keys must be unique and complete")
    if precheck.get("expected", {}).get("ordinary_reviewed") != 47:
        raise ValueError("completion precheck ordinary reviewed count mismatch")

    records: list[dict[str, Any]] = []
    packet_refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rel in PACKETS:
        packet = load(root, rel)
        packet_sha = packet.get("packet_sha256")
        reviews = packet.get("reviews")
        if not isinstance(packet_sha, str) or len(packet_sha) != 64:
            raise ValueError(f"{rel}: invalid packet_sha256")
        if not isinstance(reviews, list) or not reviews:
            raise ValueError(f"{rel}: no reviews")
        effect = packet.get("effect", {})
        locks = {
            "authority_advanced": False,
            "canonical_id_reservations": 0,
            "h_id_allocations": 0,
            "terminal_source_mappings_added": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
        for key, expected in locks.items():
            if effect.get(key) != expected:
                raise ValueError(f"{rel}: fail-closed invariant mismatch for {key}")
        packet_refs.append(
            {
                "path": rel,
                "packet_sha256": packet_sha,
                "source_fencing_token": packet.get("fencing_token"),
                "source_claim_id": packet.get("claim_id"),
                "reviewed_count": len(reviews),
            }
        )
        for review in reviews:
            if not isinstance(review, dict):
                raise ValueError(f"{rel}: invalid review row")
            source_key = review.get("source_record_key")
            if not isinstance(source_key, str) or source_key not in queue_keys:
                raise ValueError(f"{rel}: review source key not in lower49 queue")
            if source_key in seen:
                raise ValueError(f"duplicate ordinary review key: {source_key}")
            if review.get("review_outcome") != "CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED":
                raise ValueError(f"{source_key}: review is not distinctness-supported")
            if review.get("new_identity_status") != "UNALLOCATED_PREAUTH_CANDIDATE":
                raise ValueError(f"{source_key}: review is not unallocated preauthority")
            if review.get("terminal_source_mapping") != "NONE" or review.get("authority_effect") != "NONE":
                raise ValueError(f"{source_key}: review has terminal/authority effect")
            candidates = review.get("similarity_candidates")
            if not isinstance(candidates, list) or not candidates or not all(isinstance(i, str) for i in candidates):
                raise ValueError(f"{source_key}: suggested comparator set missing")
            seen.add(source_key)
            records.append(
                {
                    "source_record_key": source_key,
                    "suggested_hotel_ids": list(candidates),
                    "review_packet": rel,
                    "review_packet_sha256": packet_sha,
                    "review_outcome": "CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED",
                    "new_identity_status": "UNALLOCATED_PREAUTH_CANDIDATE",
                    "terminal_source_mapping": "NONE",
                    "authority_effect": "NONE",
                }
            )

    ordinary_keys = set(seen)
    special_keys = queue_keys - ordinary_keys
    if len(ordinary_keys) != 47:
        raise ValueError(f"ordinary lower49 review count must be 47, got {len(ordinary_keys)}")
    if special_keys != EXPECTED_SPECIAL_KEYS:
        raise ValueError(f"unexpected special-key set: {sorted(special_keys)}")
    if ordinary_keys | special_keys != queue_keys or ordinary_keys & special_keys:
        raise ValueError("lower49 set conservation failed")

    records.sort(key=lambda row: row["source_record_key"])
    batches: list[dict[str, Any]] = []
    batch_sizes = (10, 10, 10, 10, 7)
    cursor = 0
    for index, size in enumerate(batch_sizes, start=1):
        slice_ = records[cursor : cursor + size]
        if len(slice_) != size:
            raise ValueError("stable lower49 batch partition underflow")
        batches.append(
            {
                "batch_id": f"L49-B{index:02d}",
                "items": size,
                "source_record_keys": [row["source_record_key"] for row in slice_],
            }
        )
        cursor += size
    if cursor != 47:
        raise ValueError("stable lower49 batch partition overflow")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "project": PROJECT,
        "source_snapshot_id": SNAPSHOT,
        "compiled_from_main_sha": parent_main_sha,
        "authority": {
            "epoch": AUTHORITY_EPOCH,
            "materialized_sha256": AUTHORITY_SHA256,
            "advanced": False,
        },
        "materialization_claim": {
            "claim_id": CLAIM_ID,
            "fencing_token": FENCING_TOKEN,
            "authority_ceiling": "PREAUTH_SRR_DECISION_ONLY_NO_CANONICAL_MUTATION",
        },
        "source_queue": {
            "path": QUEUE,
            "records": 49,
            "source_record_keys_sha256": queue.get("source_record_keys_sha256"),
            "manifest_sha256": queue.get("manifest_sha256"),
        },
        "completion_precheck": PRECHECK,
        "evidence_packets": packet_refs,
        "evidence_reuse_semantics": "TOKEN5_REVIEW_EVIDENCE_ONLY_TOKEN6_RECOMPILES_NO_AUTHORITY_TRANSFER",
        "ordinary_reviewed_records": 47,
        "ordinary_source_record_keys_sha256": sha256_json([row["source_record_key"] for row in records]),
        "excluded_special_source_record_keys": sorted(special_keys),
        "records": records,
        "batches": batches,
        "batch_policy": "stable source_record_key order; 10/10/10/10/7",
        "mapping_effect": {
            "terminal_mapping_delta": 0,
            "terminal_source_mappings": 658,
            "reconcile_required": 1403,
        },
        "safety": {
            "authority_advanced": False,
            "h_id_allocations": 0,
            "canonical_id_reservations": 0,
            "h_0691": "UNALLOCATED",
            "crm_universe_complete": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
        "next": {
            "route": "EXECUTE_LOWER49_PREAUTH_L49_B01_WITHOUT_AUTOBIND",
            "batch_id": "L49-B01",
            "items": 10,
        },
    }
    payload["records_sha256"] = sha256_json(records)
    payload["workset_sha256"] = sha256_json({key: value for key, value in payload.items() if key != "workset_sha256"})
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--parent-main-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    payload = compile_workset(root, parent_main_sha=args.parent_main_sha)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "workset_sha256": payload["workset_sha256"], "records": 47}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
