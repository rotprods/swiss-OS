#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swiss_os.application_wave import compile_top_exact_vacancy_seeds, load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile public-safe vacancy-first Wave 2 seeds from a market-enrichment aggregate.")
    parser.add_argument("--market-aggregate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be between 1 and 100")
    aggregate = load_json(args.market_aggregate)
    payload = compile_top_exact_vacancy_seeds(aggregate, limit=args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_count": payload["selected_count"],
        "exact_vacancy_seed_count": payload["exact_vacancy_seed_count"],
        "outbound": payload["outbound"],
        "send_allowed": payload["send_allowed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
