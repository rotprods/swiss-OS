#!/usr/bin/env python3
"""Guard the stable CEP-1.0 pre-authority contract."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKERS = {
    "docs/operations/CANDIDATE_ENTITY_PARTITION.md": [
        "CEP-1.0",
        "EXACT_DETAIL_URL",
        "NAME_CITY_MULTIPLE_STABLE_IDENTITIES",
        "canonical_id_reservations = 0",
        "OUTBOUND = CLOSED",
        "send_allowed = 0",
    ],
    "src/swiss_os/candidate_entity_partition.py": [
        'SCHEMA_VERSION = "CEP-1.0"',
        "candidate records SHA mismatch",
        "source record assigned to multiple clusters",
        '"authority_advanced": False',
        '"h_id_allocations": 0',
        '"canonical_id_reservations": 0',
        '"outbound": "CLOSED"',
        '"send_allowed": 0',
    ],
    ".github/workflows/candidate-entity-partition-canary.yml": [
        "candidate_records\"] == 1438",
        "exact_assignment_count\"] == 1438",
        "canonical_id_reservations",
        "outbound_opened",
        "send_allowed",
    ],
}

errors: list[str] = []
for relative, markers in REQUIRED_MARKERS.items():
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing CEP contract artifact: {relative}")
        continue
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"missing CEP marker in {relative}: {marker}")

if errors:
    print("cep_contract_guard: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("cep_contract_guard: PASS")
