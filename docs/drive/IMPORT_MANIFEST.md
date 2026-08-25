# Drive → GitHub Migration Manifest

Bootstrap target: `rotprods/swiss-OS`.

## Migrated into canonical repository contracts

Drive concepts represented directly in this repository:

- `GOAL.md` → normalized live `GOAL.md`
- `AGENTS.md` / `AGENT_PROMPT.md` → normalized `AGENTS.md`
- `OPERATING_RULES.md` → `OPERATING_RULES.md`
- `RUNBOOK_V6.md` → normalized `RUNBOOK.md`
- `SYSTEM_RELEASE.md` / `REALTIME_PROJECT.md` / handoffs → normalized `STATE.md`
- authority/storage semantics → `docs/architecture/*`
- Drive persistence boundaries → `SECURITY.md` + `.gitignore`

The repository intentionally prefers one current contract over duplicating stale prose across many files.

## Kept in Drive / operational storage

These are **not copied into the public repository**:

- `HOTELS_MASTER` live spreadsheet data;
- operational SQLite shadows and snapshots;
- raw `graph_registry.json` runtime/meta-state payloads;
- candidate/contact/private evidence rows;
- CV/portfolio/private media;
- generated operational exports;
- temporary staging and recovery payloads.

## Why

Drive remains the human/control-plane persistence layer and the constrained DB remains operational truth. GitHub provides version control and reproducibility without leaking operational data or creating a second competing state backend.

## Reconciliation performed during bootstrap

Drive prose still contained older 667-state references, while live `GOAL_STATE`, current `HOTELS_V2` and Scheduler V2 reflected Batch03 at 677. The repository bootstrap uses the newer live 677 frontier and records the older prose as superseded rather than cloning its drift.
