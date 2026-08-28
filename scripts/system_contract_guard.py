#!/usr/bin/env python3
"""Fail CI when stable contracts regress into stale operational-state copies."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/operations/WAVE_OPERATING_PROTOCOL.md",
    "docs/operations/PRODUCTION_READINESS_GAUNTLET.md",
    "docs/architecture/ENGINE_REGISTRY.md",
    "docs/architecture/AUTHORITY_MODEL.md",
    "docs/architecture/SYSTEM_MAP.md",
    "docs/architecture/EXECUTABLE_CORE.md",
]

# These documents define stable behavior/architecture. They must not duplicate
# mutable live frontier state. Historical/precedent docs and STATE.md are not
# included because exact IDs/counts are legitimate there.
STATE_FREE_FILES = [
    "README.md",
    "GOAL.md",
    "AGENTS.md",
    "RUNBOOK.md",
    "docs/architecture/AUTHORITY_MODEL.md",
    "docs/architecture/SYSTEM_MAP.md",
    "docs/architecture/EXECUTABLE_CORE.md",
]

MUTABLE_FRONTIER_PATTERNS = [
    ("scheduler frontier", re.compile(r"\bSV2-\d{3,}\b")),
    ("physical hotel ID", re.compile(r"\bH-\d{4}\b")),
    ("entity epoch", re.compile(r"\bHS_ENTITY_EPOCH_\d{4}-\d{2}-\d{2}_E\d+\b")),
    (
        "operational parent version",
        re.compile(r"\bOPERATIONAL_DB_SHADOW_MANIFEST_V\d+\b"),
    ),
    (
        "live checkpoint fraction",
        re.compile(r"\b\d{1,4}\s*/\s*(?:750|1000|2050)\b"),
    ),
]

REQUIRED_MARKERS = {
    "README.md": [
        "WAVE_OPERATING_PROTOCOL.md",
        "STATE.md",
        "only mutable current-state pointer",
    ],
    "AGENTS.md": [
        "WAVE_OPERATING_PROTOCOL.md",
        "DEGRADED_CANARY",
        "COMPLETE_AUTHORITY",
        "Operational Graph",
        "Library",
    ],
    "GOAL.md": [
        "OUTBOUND = CLOSED",
        "send_allowed = 0",
        "WAVE_OPERATING_PROTOCOL.md",
    ],
    "docs/operations/WAVE_OPERATING_PROTOCOL.md": [
        "AUTHORITATIVE_WRITE",
        "READ_ONLY_RESEARCH",
        "DEGRADED_CANARY",
        "RECOVERY_RECONCILE",
        "GRAPH_IMPACT",
        "COMPLETE_AUTHORITY",
        "SAFE_STOP_CANARY",
        "Library",
    ],
    "docs/operations/PRODUCTION_READINESS_GAUNTLET.md": [
        "G00",
        "G20",
        "system_contract_guard.py",
        "OUTBOUND = CLOSED",
    ],
    "docs/architecture/ENGINE_REGISTRY.md": [
        "Mission Commander",
        "Authority & Reconciliation Engine",
        "Entity Resolution Engine",
        "Evidence Engine",
        "Operational Graph Engine",
        "Scheduler & TTL Engine",
        "QA / Governance Engine",
        "Recovery & Persistence Engine",
        "Git / CI Engine",
    ],
    "docs/architecture/SYSTEM_MAP.md": [
        "Operational Graph",
        "Project Memory Meta Graph",
        "Library",
        "DEGRADED_CANARY",
    ],
    "docs/architecture/AUTHORITY_MODEL.md": [
        "authority-eligible",
        "ChatGPT Library",
        "RECOVERY_RECONCILE",
        "CI PASS never proves runtime",
    ],
}

errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing required system contract: {rel}")
        return ""
    return path.read_text(encoding="utf-8")


for rel in REQUIRED_FILES:
    read(rel)

for rel in STATE_FREE_FILES:
    text = read(rel)
    for label, pattern in MUTABLE_FRONTIER_PATTERNS:
        match = pattern.search(text)
        if match:
            errors.append(
                f"stable document contains mutable {label}: {rel}: {match.group(0)!r}"
            )

for rel, markers in REQUIRED_MARKERS.items():
    text = read(rel)
    lowered = text.lower()
    for marker in markers:
        if marker.lower() not in lowered:
            errors.append(f"missing contract marker in {rel}: {marker}")

# STATE must explicitly separate authority and canary semantics, but exact
# counts remain intentionally unconstrained because STATE is the mutable pointer.
state_text = read("STATE.md").lower()
for marker in (
    "authoritative",
    "canary",
    "outbound",
    "send_allowed",
):
    if marker not in state_text:
        errors.append(f"STATE.md missing authority/canary marker: {marker}")

# Stable docs must not positively claim an always-on daemon/absolute real-time
# service. Guard only explicit operational claims; policy text that says not to
# claim a daemon remains allowed.
for rel in STATE_FREE_FILES:
    text = (ROOT / rel).read_text(encoding="utf-8") if (ROOT / rel).exists() else ""
    if re.search(r"\b(?:runs 24/7|continuous real-time daemon is active)\b", text, re.I):
        errors.append(f"unsupported daemon/real-time claim in stable document: {rel}")

if errors:
    print("system_contract_guard: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("system_contract_guard: PASS")
