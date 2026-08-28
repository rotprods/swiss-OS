#!/usr/bin/env python3
"""Fail CI when stable contracts regress into stale operational-state copies."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/operations/META_EXECUTION_PROTOCOL.md",
    "docs/operations/NEXT_POINTER_PROTOCOL.md",
    "docs/operations/WAVE_OPERATING_PROTOCOL.md",
    "docs/operations/PRODUCTION_READINESS_GAUNTLET.md",
    "docs/operations/CRM_UNIVERSE_PROTOCOL.md",
    "docs/operations/DISCOVER_SWISS_SNAPSHOT_ADAPTER.md",
    "docs/operations/SOURCE_SCOPE_RECONCILIATION.md",
    "docs/architecture/ENGINE_REGISTRY.md",
    "docs/architecture/AUTHORITY_MODEL.md",
    "docs/architecture/SYSTEM_MAP.md",
    "docs/architecture/EXECUTABLE_CORE.md",
]

STATE_FREE_FILES = [
    "README.md",
    "GOAL.md",
    "AGENTS.md",
    "RUNBOOK.md",
    "docs/architecture/AUTHORITY_MODEL.md",
    "docs/architecture/SYSTEM_MAP.md",
    "docs/architecture/EXECUTABLE_CORE.md",
    "docs/operations/META_EXECUTION_PROTOCOL.md",
    "docs/operations/NEXT_POINTER_PROTOCOL.md",
    "docs/operations/CRM_UNIVERSE_PROTOCOL.md",
    "docs/operations/DISCOVER_SWISS_SNAPSHOT_ADAPTER.md",
    "docs/operations/SOURCE_SCOPE_RECONCILIATION.md",
]

MUTABLE_FRONTIER_PATTERNS = [
    ("scheduler frontier", re.compile(r"\bSV2-\d{3,}\b")),
    ("physical hotel ID", re.compile(r"\bH-\d{4}\b")),
    ("entity epoch", re.compile(r"\bHS_ENTITY_EPOCH_\d{4}-\d{2}-\d{2}_E\d+\b")),
    ("operational parent version", re.compile(r"\bOPERATIONAL_DB_SHADOW_MANIFEST_V\d+\b")),
    ("live checkpoint fraction", re.compile(r"\b\d{1,4}\s*/\s*(?:750|1000|2050)\b")),
]

REQUIRED_MARKERS = {
    "README.md": ["WAVE_OPERATING_PROTOCOL.md", "STATE.md", "only mutable current-state pointer"],
    "AGENTS.md": [
        "META_EXECUTION_PROTOCOL.md",
        "COLETTE",
        "WAVE_OPERATING_PROTOCOL.md",
        "DEGRADED_CANARY",
        "COMPLETE_AUTHORITY",
        "Operational Graph",
        "Library",
        "No-idle rule",
    ],
    "GOAL.md": ["OUTBOUND = CLOSED", "send_allowed = 0", "WAVE_OPERATING_PROTOCOL.md", "CRM_UNIVERSE_COMPLETE = TRUE", "CRM_UNIVERSE_PROTOCOL.md"],
    "docs/operations/META_EXECUTION_PROTOCOL.md": [
        "MEP-2.0",
        "COLETTE",
        "No-idle rule",
        "AUTHORITY_RECOVERY",
        "STRUCTURED_SOURCE_CAPTURE",
        "SOURCE_SCOPE_RECONCILIATION",
        "MASS_INGEST_STAGING",
        "AUTHORITATIVE_PROMOTION",
        "BLOCKED_P0",
        "OUTBOUND = CLOSED",
    ],
    "docs/operations/NEXT_POINTER_PROTOCOL.md": [
        "NPP-1.0",
        "parent_git_sha",
        "authority_epoch",
        "next_route",
        "Meta-PR chaining",
        "Activation chaining",
        "outbound_allowed",
    ],
    "docs/operations/WAVE_OPERATING_PROTOCOL.md": ["AUTHORITATIVE_WRITE", "READ_ONLY_RESEARCH", "DEGRADED_CANARY", "RECOVERY_RECONCILE", "GRAPH_IMPACT", "COMPLETE_AUTHORITY", "SAFE_STOP_CANARY", "Library"],
    "docs/operations/PRODUCTION_READINESS_GAUNTLET.md": ["G00", "G20", "system_contract_guard.py", "OUTBOUND = CLOSED"],
    "docs/operations/CRM_UNIVERSE_PROTOCOL.md": ["CRM_UNIVERSE_COMPLETE = TRUE", "snapshot_raw_records", "snapshot_unmapped_records = 0", "ALIAS_TO_CANONICAL", "RECONCILE_REQUIRED", "OUTBOUND", "discover.swiss", "member-directory scope"],
    "docs/operations/DISCOVER_SWISS_SNAPSHOT_ADAPTER.md": ["DSA-1.0", "dsod-hs", "continuationToken", "hsId", "member_directory_scope_reconciled", "DISCOVER_SWISS_SUBSCRIPTION_KEY"],
    "docs/operations/SOURCE_SCOPE_RECONCILIATION.md": ["SSR-1.0", "EXACT_HSID", "EXACT_DETAIL_URL", "EXACT_NAME_CITY", "FROZEN_CANDIDATE", "H_ID_ALLOCATIONS = 0"],
    "docs/architecture/ENGINE_REGISTRY.md": ["Mission Commander", "Authority & Reconciliation Engine", "Entity Resolution Engine", "Evidence Engine", "Operational Graph Engine", "Scheduler & TTL Engine", "QA / Governance Engine", "Recovery & Persistence Engine", "Git / CI Engine"],
    "docs/architecture/SYSTEM_MAP.md": ["Operational Graph", "Project Memory Meta Graph", "Library", "DEGRADED_CANARY", "MEP-2.0", "COLETTE"],
    "docs/architecture/AUTHORITY_MODEL.md": ["authority-eligible", "ChatGPT Library", "RECOVERY_RECONCILE", "CI PASS never proves runtime"],
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
    text = read(rel).lower()
    for marker in markers:
        if marker.lower() not in text:
            errors.append(f"missing contract marker in {rel}: {marker}")

state_text = read("STATE.md").lower()
for marker in (
    "authoritative",
    "canary",
    "outbound",
    "send_allowed",
):
    if marker not in state_text:
        errors.append(f"STATE.md missing authority/canary marker: {marker}")

for rel in STATE_FREE_FILES:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if re.search(r"\b(?:runs 24/7|continuous real-time daemon is active)\b", text, re.I):
        errors.append(f"unsupported daemon/real-time claim in stable document: {rel}")

if errors:
    print("system_contract_guard: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("system_contract_guard: PASS")
