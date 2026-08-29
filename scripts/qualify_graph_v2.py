#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from swiss_os.v2_runtime_drills import run_all_runtime_drills  # noqa: E402
from swiss_os.v2_shadow_bridge import execute_read_only_next_shadow  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between 0 and 1")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def stats(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "min_ms": round(min(values), 3),
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": round(percentile(values, 0.95), 3),
        "max_ms": round(max(values), 3),
        "mean_ms": round(statistics.fmean(values), 3),
    }


def timed(callback: Callable[[], Any]) -> tuple[float, Any]:
    started = time.perf_counter()
    value = callback()
    duration_ms = (time.perf_counter() - started) * 1000
    return duration_ms, value


def build_bundle(
    *,
    commit_sha: str,
    branch: str,
    generated_at: str,
    attestation: Path,
    out_root: Path,
) -> tuple[Path, dict[str, Any], float]:
    build = out_root / "graph-v2"
    if build.exists():
        shutil.rmtree(build)
    command = [
        sys.executable,
        str(ROOT / "scripts/compile_graph_v2.py"),
        "--out",
        str(build),
        "--main-sha",
        commit_sha,
        "--branch",
        branch,
        "--generated-at",
        generated_at,
        "--test-attestation",
        str(attestation),
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    duration = (time.perf_counter() - started) * 1000
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout + completed.stderr)
    manifest = read_json(build / "manifest.json")
    bundle = out_root / "bundle.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(build.rglob("*")):
            if path.is_file():
                archive.write(path, Path("graph-v2") / path.relative_to(build))
        archive.write(attestation, "v2_test_attestation.json")
    return bundle, manifest, duration


def verify_bundle_isolated(
    bundle: Path,
    commit_sha: str,
    workspace: Path,
    iteration: int,
) -> dict[str, Any]:
    isolated = workspace / f"recovery-{iteration:04d}"
    isolated.mkdir(parents=True, exist_ok=False)
    verifier = isolated / "verifier.py"
    copied_bundle = isolated / "bundle.zip"
    shutil.copy2(ROOT / "scripts/verify_graph_v2_bundle.py", verifier)
    shutil.copy2(bundle, copied_bundle)
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            str(verifier),
            str(copied_bundle),
            "--expected-sha",
            commit_sha,
        ],
        cwd=isolated,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout + completed.stderr)
    report = json.loads(completed.stdout)
    if report.get("state") != "PASS":
        raise RuntimeError(f"recovery report failed: {report}")
    return report


def qualify(
    *,
    commit_sha: str,
    branch: str,
    generated_at: str,
    attestation: Path,
    next_path: Path,
    iterations: int,
    compile_iterations: int,
    out_path: Path,
) -> dict[str, Any]:
    if len(commit_sha) != 40:
        raise ValueError("commit SHA must contain 40 characters")
    if iterations < 3 or compile_iterations < 2:
        raise ValueError("qualification requires at least 3 runtime and 2 compile iterations")
    if compile_iterations > iterations:
        raise ValueError("compile_iterations cannot exceed iterations")
    attestation_payload = read_json(attestation)
    if attestation_payload.get("commit_sha") != commit_sha:
        raise ValueError("test attestation does not match commit SHA")
    next_payload = read_json(next_path)
    if not isinstance(next_payload, dict):
        raise ValueError("NEXT must be a JSON object")

    compile_times: list[float] = []
    compile_manifests: list[dict[str, Any]] = []
    recovery_times: list[float] = []
    runtime_times: list[float] = []
    shadow_times: list[float] = []
    failures: list[dict[str, Any]] = []
    runtime_result_digests: set[str] = set()
    shadow_shape_digests: set[str] = set()

    with tempfile.TemporaryDirectory(prefix="graph-v2-qualification-") as temp:
        workspace = Path(temp)
        bundles: list[Path] = []
        for index in range(compile_iterations):
            output = workspace / f"compile-{index:04d}"
            output.mkdir()
            try:
                bundle, manifest, duration = build_bundle(
                    commit_sha=commit_sha,
                    branch=branch,
                    generated_at=generated_at,
                    attestation=attestation,
                    out_root=output,
                )
            except Exception as exc:
                failures.append(
                    {
                        "phase": "compile",
                        "iteration": index,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                continue
            compile_times.append(duration)
            compile_manifests.append(manifest)
            bundles.append(bundle)

        if not bundles:
            raise RuntimeError("no compile iteration produced a recovery bundle")

        baseline_manifest = compile_manifests[0]
        deterministic_fields = (
            "graph_digest",
            "contextpack_digest",
            "event_watermark",
            "files",
        )
        deterministic = all(
            all(item.get(field) == baseline_manifest.get(field) for field in deterministic_fields)
            for item in compile_manifests
        )

        for index in range(iterations):
            bundle = bundles[index % len(bundles)]
            try:
                duration, recovery = timed(
                    lambda index=index, bundle=bundle: verify_bundle_isolated(
                        bundle,
                        commit_sha,
                        workspace,
                        index,
                    )
                )
                recovery_times.append(duration)
                if recovery.get("main_sha") != commit_sha:
                    raise RuntimeError("recovery returned wrong main SHA")
            except Exception as exc:
                failures.append(
                    {
                        "phase": "recovery",
                        "iteration": index,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

            try:
                duration, runtime = timed(
                    lambda: run_all_runtime_drills(commit_sha).to_dict()
                )
                runtime_times.append(duration)
                if runtime.get("passed") is not True:
                    raise RuntimeError("runtime drill suite returned non-PASS")
                runtime_result_digests.add(
                    hashlib.sha256(
                        json.dumps(
                            [
                                {
                                    "drill_id": item["drill_id"],
                                    "state": item["state"],
                                    "assertions": item["assertions"],
                                    "evidence": item["evidence"],
                                }
                                for item in runtime["results"]
                            ],
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest()
                )
            except Exception as exc:
                failures.append(
                    {
                        "phase": "runtime",
                        "iteration": index,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

            try:
                duration, shadow = timed(
                    lambda: execute_read_only_next_shadow(
                        next_payload,
                        main_sha=commit_sha,
                        generated_at=generated_at,
                    ).to_dict()
                )
                shadow_times.append(duration)
                if shadow.get("passed") is not True:
                    raise RuntimeError("CRM shadow returned non-PASS")
                shadow_shape_digests.add(
                    hashlib.sha256(
                        json.dumps(
                            {
                                "graph": shadow["graph"],
                                "event_watermark": shadow["event_watermark"],
                                "contextpack": shadow["contextpack"],
                                "next_route": shadow["next_route"],
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest()
                )
            except Exception as exc:
                failures.append(
                    {
                        "phase": "shadow",
                        "iteration": index,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

    thresholds = {
        "compile_p95_ms": 5000,
        "zero_context_recovery_p95_ms": 5000,
        "runtime_suite_p95_ms": 2000,
        "crm_shadow_p95_ms": 1000,
        "failure_count": 0,
        "unique_compile_manifest_shapes": 1,
        "unique_runtime_result_shapes": 1,
        "unique_shadow_shapes": 1,
    }
    measurements = {
        "compile": stats(compile_times),
        "zero_context_recovery": stats(recovery_times),
        "runtime_suite": stats(runtime_times),
        "crm_shadow": stats(shadow_times),
        "compile_successes": len(compile_times),
        "recovery_successes": len(recovery_times),
        "runtime_successes": len(runtime_times),
        "shadow_successes": len(shadow_times),
        "failures": failures,
        "failure_count": len(failures),
        "deterministic_compile": deterministic,
        "unique_runtime_result_shapes": len(runtime_result_digests),
        "unique_shadow_shapes": len(shadow_shape_digests),
    }
    gates = {
        "compile_success_count": len(compile_times) == compile_iterations,
        "recovery_success_count": len(recovery_times) == iterations,
        "runtime_success_count": len(runtime_times) == iterations,
        "shadow_success_count": len(shadow_times) == iterations,
        "failure_count": len(failures) == 0,
        "deterministic_compile": deterministic,
        "deterministic_runtime_shape": len(runtime_result_digests) == 1,
        "deterministic_shadow_shape": len(shadow_shape_digests) == 1,
        "compile_p95": measurements["compile"]["p95_ms"] <= thresholds["compile_p95_ms"],
        "recovery_p95": measurements["zero_context_recovery"]["p95_ms"] <= thresholds["zero_context_recovery_p95_ms"],
        "runtime_p95": measurements["runtime_suite"]["p95_ms"] <= thresholds["runtime_suite_p95_ms"],
        "shadow_p95": measurements["crm_shadow"]["p95_ms"] <= thresholds["crm_shadow_p95_ms"],
    }
    passed = all(gates.values())
    report = {
        "schema_version": "GRAPH_V2_EMPIRICAL_QUALIFICATION_1",
        "state": "PASS" if passed else "FAIL",
        "commit_sha": commit_sha,
        "branch": branch,
        "generated_at": generated_at,
        "iterations": iterations,
        "compile_iterations": compile_iterations,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "thresholds": thresholds,
        "measurements": measurements,
        "gates": gates,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    write_json(out_path, report)
    if not passed:
        raise RuntimeError("empirical qualification failed")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--branch", default="unknown")
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--test-attestation", type=Path, required=True)
    parser.add_argument("--next", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--compile-iterations", type=int, default=5)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = qualify(
        commit_sha=args.commit_sha,
        branch=args.branch,
        generated_at=args.generated_at,
        attestation=args.test_attestation,
        next_path=args.next,
        iterations=args.iterations,
        compile_iterations=args.compile_iterations,
        out_path=args.out,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
