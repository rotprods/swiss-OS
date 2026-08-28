"""CLI for deterministic MEP planning and COLETTE loop-guard evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .meta_execution import context_from_mapping, render_next
from .meta_loop import ActivationJournal, plan_chained_next


def _read_object(path: str) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_object(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def cmd_plan(input_path: str, out_path: str) -> int:
    pointer = render_next(_read_object(input_path))
    _write_object(out_path, pointer)
    print(json.dumps(pointer, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_chained_plan(input_path: str, journal_path: str, out_path: str) -> int:
    context = context_from_mapping(_read_object(input_path))
    journal = ActivationJournal.from_mapping(_read_object(journal_path))
    pointer, guards = plan_chained_next(context, journal)
    payload = {
        "next": pointer.as_dict(),
        "loop_guards": [result.__dict__ for result in guards],
    }
    _write_object(out_path, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.meta_cli")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Emit a deterministic durable NEXT pointer")
    plan.add_argument("input")
    plan.add_argument("--out", required=True)

    chained = sub.add_parser(
        "chained-plan",
        help="Apply loop guards before emitting durable NEXT",
    )
    chained.add_argument("input")
    chained.add_argument("journal")
    chained.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            return cmd_plan(args.input, args.out)
        if args.command == "chained-plan":
            return cmd_chained_plan(args.input, args.journal, args.out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc), "output_written": False}), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
