#!/usr/bin/env python3
from pathlib import Path
import re
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
    "pyproject.toml",
    "docs/operations/WAVE_OPERATING_PROTOCOL.md",
    "docs/operations/PRODUCTION_READINESS_GAUNTLET.md",
    "docs/architecture/ENGINE_REGISTRY.md",
    "docs/architecture/AUTHORITY_MODEL.md",
    "docs/architecture/SYSTEM_MAP.md",
    "src/swiss_os/schema.sql",
    "src/swiss_os/manifest.py",
    "src/swiss_os/invariants.py",
    "src/swiss_os/reconcile.py",
    "src/swiss_os/scheduler.py",
    "scripts/system_contract_guard.py",
    "tests/test_manifest.py",
    "tests/test_restore.py",
]
FORBIDDEN_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".pem", ".p12"}
FORBIDDEN_NAMES = {".env", "credentials.json"}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
]

errors = []
for rel in REQUIRED:
    if not (ROOT / rel).exists():
        errors.append(f"missing required contract/core file: {rel}")

for p in ROOT.rglob("*"):
    if not p.is_file() or ".git" in p.parts:
        continue
    if p.suffix.lower() in FORBIDDEN_SUFFIXES or p.name in FORBIDDEN_NAMES:
        errors.append(f"forbidden public-repo artifact: {p.relative_to(ROOT)}")
        continue
    if p.stat().st_size > 2_000_000:
        errors.append(f"unexpected large public-repo artifact: {p.relative_to(ROOT)}")
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"possible secret material: {p.relative_to(ROOT)}")

if errors:
    print("repo_guard: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("repo_guard: PASS")
