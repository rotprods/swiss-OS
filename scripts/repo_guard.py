#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "GOAL.md",
    "STATE.md",
    "AGENTS.md",
    "OPERATING_RULES.md",
    "RUNBOOK.md",
    "SECURITY.md",
]

FORBIDDEN_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".pem", ".p12"}
FORBIDDEN_NAMES = {".env", "credentials.json"}

errors = []
for rel in REQUIRED:
    if not (ROOT / rel).exists():
        errors.append(f"missing required contract: {rel}")

for p in ROOT.rglob("*"):
    if not p.is_file() or ".git" in p.parts:
        continue
    if p.suffix.lower() in FORBIDDEN_SUFFIXES or p.name in FORBIDDEN_NAMES:
        errors.append(f"forbidden public-repo artifact: {p.relative_to(ROOT)}")

if errors:
    print("repo_guard: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("repo_guard: PASS")
