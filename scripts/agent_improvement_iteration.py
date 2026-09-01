#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swiss_os.agent_improvement_runtime import AgentRunContext, IterationProposal, MetricSpec, evaluate_iteration


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate one GRAPH-REFACTOR-V2 agent improvement iteration")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = load(args.manifest)
    context = AgentRunContext(
        **{**raw["context"], "goal_ids": tuple(raw["context"]["goal_ids"])}
    )
    proposal = IterationProposal(
        **{
            **raw["proposal"],
            "changed_paths": tuple(raw["proposal"]["changed_paths"]),
            "evaluation_suite": tuple(raw["proposal"]["evaluation_suite"]),
        }
    )
    metrics = tuple(MetricSpec(**item) for item in raw.get("metrics", []))
    outcome = raw.get("outcome", {})
    result = evaluate_iteration(
        context,
        proposal,
        metrics,
        tests_passed=bool(outcome.get("tests_passed", False)),
        invariant_violations=outcome.get("invariant_violations", []),
        security_violations=outcome.get("security_violations", []),
        crashed=bool(outcome.get("crashed", False)),
        blocked_reason=outcome.get("blocked_reason"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result.as_record(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"{result.iteration_id} {result.decision}: {result.reason}")
    return 0 if result.decision == "KEEP" else 2


if __name__ == "__main__":
    raise SystemExit(main())
