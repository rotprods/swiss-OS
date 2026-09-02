#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_DIR = ROOT / "docs/state/v2/claims"
CANONICAL_PROJECTION = "docs/state/v2/active-claims.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_working_claims(claims_dir: Path = CLAIMS_DIR) -> list[dict[str, Any]]:
    return [_load(path) for path in sorted(claims_dir.glob("*.json"))]


def load_canonical_projection(ref: str = "origin/main", path: str = CANONICAL_PROJECTION) -> dict[str, Any]:
    try:
        raw = subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"cannot read canonical fencing projection from {ref}:{path}: {exc.stderr.strip()}") from exc
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("canonical active-claims projection must be an object")
    return value


def evaluate(canonical: dict[str, Any], working_claims: Iterable[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    watermark = int(canonical.get("fencing_high_watermark", 0))
    canonical_active = {
        str(item.get("claim_id")): item
        for item in canonical.get("claims", [])
        if isinstance(item, dict) and item.get("state") in {"ACTIVE", "BLOCKED"} and item.get("claim_id")
    }
    violations: list[str] = []
    evaluated: list[dict[str, Any]] = []
    seen_tokens: dict[int, str] = {}

    for claim in working_claims:
        if claim.get("state") not in {"ACTIVE", "BLOCKED"}:
            continue
        claim_id = str(claim.get("claim_id", ""))
        token_raw = claim.get("fencing_token")
        if not claim_id or not isinstance(token_raw, int):
            violations.append(f"INVALID_ACTIVE_CLAIM:{claim_id or '<missing>'}")
            continue
        token = int(token_raw)
        canonical_claim = canonical_active.get(claim_id)
        continuation = canonical_claim is not None

        if continuation:
            canonical_token = canonical_claim.get("fencing_token")
            if canonical_token != token:
                violations.append(f"CANONICAL_CLAIM_TOKEN_MISMATCH:{claim_id}:{canonical_token}!={token}")
        elif token <= watermark:
            violations.append(f"STALE_BRANCH_FENCING_TOKEN:{claim_id}:{token}<=CANONICAL_WATERMARK:{watermark}")

        other = seen_tokens.get(token)
        if other and other != claim_id:
            violations.append(f"DUPLICATE_ACTIVE_FENCING_TOKEN:{token}:{other}:{claim_id}")
        else:
            seen_tokens[token] = claim_id

        evaluated.append({
            "claim_id": claim_id,
            "fencing_token": token,
            "canonical_continuation": continuation,
            "canonical_watermark": watermark,
        })

    receipt = {
        "schema_version": "GRAPH-V2-STALE-BRANCH-FENCING-1.0",
        "canonical_watermark": watermark,
        "canonical_active_claim_ids": sorted(canonical_active),
        "evaluated_active_claims": evaluated,
        "violations": violations,
    }
    return not violations, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-json", help="Offline canonical active-claims JSON fixture")
    parser.add_argument("--canonical-ref", default="origin/main")
    parser.add_argument("--claims-dir", default=str(CLAIMS_DIR))
    parser.add_argument("--receipt")
    args = parser.parse_args()

    canonical = _load(Path(args.canonical_json)) if args.canonical_json else load_canonical_projection(args.canonical_ref)
    ok, receipt = evaluate(canonical, load_working_claims(Path(args.claims_dir)))
    text = json.dumps(receipt, sort_keys=True)
    print(text)
    if args.receipt:
        Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.receipt).write_text(text + "\n", encoding="utf-8")
    if not ok:
        for violation in receipt["violations"]:
            print(violation, file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
