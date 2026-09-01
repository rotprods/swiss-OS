#!/usr/bin/env python3
from __future__ import annotations
import base64
from pathlib import Path
from rebuild_v2_coordination import build_outputs, canonical_bytes
ROOT = Path(__file__).resolve().parents[1]
outputs = build_outputs(ROOT / "docs/refactor-v2/coordination_current_config.json")
for name in ("context-pack.json","graph-snapshot.json","CONTEXT_SURVIVAL.json"):
    print(f"V2_CANDIDATE_B64:{name}:{base64.b64encode(canonical_bytes(outputs[name])).decode('ascii')}")
