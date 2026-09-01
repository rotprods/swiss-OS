#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from swiss_os.hotel_niche_projection import compatibility_receipt, materialize_canary

OVERLAY = ROOT / "src" / "swiss_os" / "multi_niche_schema.sql"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a non-authoritative NICHE-001 compatibility canary from a source SQLite DB."
    )
    parser.add_argument("--source-db", required=True, type=Path)
    parser.add_argument("--canary-db", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--evidence-ref", default="W2-NICHE001-CANARY")
    args = parser.parse_args()

    source = args.source_db.resolve()
    canary = args.canary_db.resolve()
    if source == canary:
        raise SystemExit("source-db and canary-db must be different; authority mutation is forbidden")
    if not source.exists():
        raise SystemExit(f"source DB not found: {source}")

    canary.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    if canary.exists():
        canary.unlink()
    shutil.copy2(source, canary)

    db = sqlite3.connect(canary)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(OVERLAY.read_text())
        materialize_canary(db, args.evidence_ref)
        db.commit()
        receipt = compatibility_receipt(db)
        receipt.update(
            {
                "source_db": str(source),
                "canary_db": str(canary),
                "authority_mutated": False,
                "niche_id": "NICHE-001",
            }
        )
    finally:
        db.close()

    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
