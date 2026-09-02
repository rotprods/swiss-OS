#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swiss_os.agent_runtime_graph import reduce_agent_runtime_graph

ROOT = Path(__file__).resolve().parents[1]


def load_jsons(directory: Path) -> list[dict[str, object]]:
    if not directory.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.json"))]


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild canonical Agent Runtime Graph projection")
    parser.add_argument("--receipts-dir", type=Path, default=ROOT / "docs/state/agent-runtime/iterations")
    parser.add_argument("--heartbeats-dir", type=Path, default=ROOT / "docs/state/agent-runtime/heartbeats")
    parser.add_argument("--as-of")
    parser.add_argument("--ttl-seconds", type=int, default=1800)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/state/agent-runtime/runtime-graph.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.as_of:
        as_of = args.as_of
    elif args.check and args.output.exists():
        existing_payload = json.loads(args.output.read_text(encoding="utf-8"))
        as_of = existing_payload.get("as_of")
        if not isinstance(as_of, str) or not as_of.strip():
            raise SystemExit("canonical runtime graph has no valid as_of")
    else:
        raise SystemExit("--as-of is required when writing a runtime graph")

    graph = reduce_agent_runtime_graph(
        load_jsons(args.receipts_dir), load_jsons(args.heartbeats_dir),
        as_of=as_of, heartbeat_ttl_seconds=args.ttl_seconds,
    )
    if graph["violations"]:
        print(json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True))
        raise SystemExit(f"agent runtime graph violations: {graph['violations']}")
    rendered = canonical(graph)
    if args.check:
        if not args.output.exists():
            raise SystemExit(f"missing canonical runtime graph: {args.output}")
        existing = args.output.read_text(encoding="utf-8")
        if existing != rendered:
            raise SystemExit("agent runtime graph drift: rebuild does not equal canonical projection")
        print(f"agent_runtime_graph: PASS {graph['projection_revision']}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"agent_runtime_graph: WROTE {args.output} {graph['projection_revision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
