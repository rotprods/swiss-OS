#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


class BundleVerificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def locate_root(extracted: Path) -> Path:
    candidates = [
        path.parent
        for path in extracted.rglob("manifest.json")
        if path.parent.name == "graph-v2" or "graph-v2" in path.parent.as_posix()
    ]
    unique = sorted(set(candidates))
    if len(unique) != 1:
        raise BundleVerificationError(
            f"expected exactly one graph-v2 manifest root, found {len(unique)}"
        )
    return unique[0]


def verify_bundle(bundle: Path, expected_sha: str) -> dict[str, object]:
    if not bundle.is_file():
        raise BundleVerificationError(f"bundle not found: {bundle}")
    if not expected_sha or len(expected_sha) != 40:
        raise BundleVerificationError("expected SHA must contain 40 characters")

    with tempfile.TemporaryDirectory(prefix="graph-v2-recovery-") as temp:
        extracted = Path(temp)
        try:
            with zipfile.ZipFile(bundle) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise BundleVerificationError(
                        f"ZIP CRC failure at {bad_member}"
                    )
                for info in archive.infolist():
                    destination = (extracted / info.filename).resolve()
                    if not destination.is_relative_to(extracted.resolve()):
                        raise BundleVerificationError(
                            f"ZIP path traversal: {info.filename}"
                        )
                archive.extractall(extracted)
        except zipfile.BadZipFile as exc:
            raise BundleVerificationError("invalid ZIP bundle") from exc

        root = locate_root(extracted)
        manifest = read_json(root / "manifest.json")
        if not isinstance(manifest, dict):
            raise BundleVerificationError("manifest must be a JSON object")
        if manifest.get("main_sha") != expected_sha:
            raise BundleVerificationError("bundle main SHA mismatch")
        if manifest.get("release_candidate") is not True:
            raise BundleVerificationError("bundle is not a release candidate")
        if manifest.get("operational_authority_mutated") is not False:
            raise BundleVerificationError("bundle claims authority mutation")
        if manifest.get("h_id_allocations") != 0:
            raise BundleVerificationError("bundle allocated H-IDs")
        if manifest.get("outbound_opened") is not False:
            raise BundleVerificationError("bundle opened outbound")
        if manifest.get("send_allowed") != 0:
            raise BundleVerificationError("bundle changed send_allowed")

        file_entries = manifest.get("files")
        if not isinstance(file_entries, dict) or not file_entries:
            raise BundleVerificationError("manifest file set is missing")
        for relative, metadata in file_entries.items():
            if not isinstance(relative, str) or not isinstance(metadata, dict):
                raise BundleVerificationError("invalid manifest file entry")
            path = (root / relative).resolve()
            if not path.is_relative_to(root.resolve()):
                raise BundleVerificationError(
                    f"manifest path traversal: {relative}"
                )
            if not path.is_file():
                raise BundleVerificationError(
                    f"manifest file is missing: {relative}"
                )
            if sha256_file(path) != metadata.get("sha256"):
                raise BundleVerificationError(
                    f"manifest hash mismatch: {relative}"
                )
            if path.stat().st_size != metadata.get("bytes"):
                raise BundleVerificationError(
                    f"manifest size mismatch: {relative}"
                )

        graph = read_json(root / "system_graph.json")
        assurance = read_json(root / "assurance_report.json")
        cos = read_json(root / "cos_registry.json")
        context = read_json(root / "contextpack.json")
        program = read_json(root / "implementation_program.json")
        death = read_json(root / "death_drill.json")
        if not all(
            isinstance(item, dict)
            for item in (graph, assurance, cos, context, program, death)
        ):
            raise BundleVerificationError("core bundle objects must be mappings")

        if assurance.get("release_candidate") is not True:
            raise BundleVerificationError("assurance release gate failed")
        for key in (
            "p0_open",
            "p1_open",
        ):
            if assurance.get(key) != 0:
                raise BundleVerificationError(f"assurance {key} is non-zero")
        for key in (
            "graph_errors",
            "critical_owner_gaps",
            "critical_test_gaps",
            "invariant_failures",
        ):
            if assurance.get(key) != []:
                raise BundleVerificationError(
                    f"assurance {key} is not empty"
                )

        dimensions = cos.get("dimensions")
        if not isinstance(dimensions, list) or len(dimensions) != 20:
            raise BundleVerificationError("COS registry is not L0..L19 complete")
        dimension_ids = {item.get("dimension_id") for item in dimensions}
        if dimension_ids != {f"L{index}" for index in range(20)}:
            raise BundleVerificationError("COS dimension IDs are incomplete")
        projections = sorted((root / "projections").glob("L*.json"))
        if len(projections) != 20:
            raise BundleVerificationError("projection artifact count is not 20")

        if context.get("main_sha") != expected_sha:
            raise BundleVerificationError("ContextPack SHA mismatch")
        payload = context.get("payload")
        if not isinstance(payload, dict):
            raise BundleVerificationError("ContextPack payload is missing")
        if payload.get("operational_authority_mutated") is not False:
            raise BundleVerificationError("ContextPack claims authority mutation")
        if payload.get("outbound") != "CLOSED" or payload.get("send_allowed") != 0:
            raise BundleVerificationError("ContextPack outbound lock failed")

        tasks = program.get("tasks")
        checkpoints = program.get("checkpoints")
        if not isinstance(tasks, list) or len(tasks) != 18:
            raise BundleVerificationError("implementation task set is not 18")
        if not isinstance(checkpoints, list) or len(checkpoints) != 15:
            raise BundleVerificationError("checkpoint set is not 15")
        if death.get("authority_mutated") is not False:
            raise BundleVerificationError("death drill claims authority mutation")

        ledger_path = root / "event_ledger.jsonl"
        events = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(events) != 5:
            raise BundleVerificationError("foundation ledger event count is not 5")
        previous_hash: str | None = None
        seen: set[str] = set()
        for sequence, event in enumerate(events):
            if event.get("sequence") != sequence:
                raise BundleVerificationError("event sequence mismatch")
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or event_id in seen:
                raise BundleVerificationError("event ID invalid or duplicated")
            if event.get("previous_event_hash") != previous_hash:
                raise BundleVerificationError("event predecessor hash mismatch")
            causation = event.get("causation_id")
            if causation is not None and causation not in seen:
                raise BundleVerificationError("causation does not reference an earlier event")
            unsigned = {key: value for key, value in event.items() if key != "event_hash"}
            computed = hashlib.sha256(
                canonical_json(unsigned).encode("utf-8")
            ).hexdigest()
            if computed != event.get("event_hash"):
                raise BundleVerificationError("event hash mismatch")
            seen.add(event_id)
            previous_hash = computed
        watermark = f"{events[-1]['sequence']}:{events[-1]['event_id']}:{events[-1]['event_hash']}"
        if manifest.get("event_watermark") != watermark:
            raise BundleVerificationError("event watermark mismatch")

        attestations = list(extracted.rglob("v2_test_attestation.json"))
        if len(attestations) != 1:
            raise BundleVerificationError("expected one test attestation")
        attestation = read_json(attestations[0])
        if not isinstance(attestation, dict):
            raise BundleVerificationError("test attestation must be a mapping")
        if attestation.get("commit_sha") != expected_sha:
            raise BundleVerificationError("test attestation SHA mismatch")
        results = attestation.get("results")
        if not isinstance(results, list) or len(results) != 11:
            raise BundleVerificationError("test attestation set is incomplete")
        if not all(
            isinstance(item, dict)
            and item.get("state") == "PASS"
            and item.get("evidence_ref")
            for item in results
        ):
            raise BundleVerificationError("test attestation contains non-PASS evidence")

        return {
            "schema_version": "GRAPH_V2_ZERO_CONTEXT_RECOVERY_1",
            "state": "PASS",
            "main_sha": expected_sha,
            "bundle_sha256": sha256_file(bundle),
            "bundle_bytes": bundle.stat().st_size,
            "graph_digest": manifest.get("graph_digest"),
            "contextpack_digest": manifest.get("contextpack_digest"),
            "event_watermark": watermark,
            "nodes": len(graph.get("nodes", [])),
            "edges": len(graph.get("edges", [])),
            "hyperedges": len(graph.get("hyperedges", [])),
            "cos_projections": len(projections),
            "tasks": len(tasks),
            "checkpoints": len(checkpoints),
            "test_attestations": len(results),
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = verify_bundle(args.bundle, args.expected_sha)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
