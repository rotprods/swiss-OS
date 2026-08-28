# Drive → GitHub Migration Manifest

> **HISTORICAL BOOTSTRAP RECORD — NOT CURRENT AUTHORITY.**  
> This document records the repository bootstrap migration. Any counts/frontiers below are historical observations from that migration and MUST NOT be used for current execution. Current state is resolved from the live control plane + authority-eligible manifest + `STATE.md`.

Bootstrap target: `rotprods/swiss-OS`.

## Migrated into canonical repository contracts

Drive concepts represented directly in this repository:

- `GOAL.md` → normalized stable goal contract;
- `AGENTS.md` / `AGENT_PROMPT.md` → normalized stable `AGENTS.md`;
- `OPERATING_RULES.md` → `OPERATING_RULES.md`;
- `RUNBOOK_V6.md` → normalized `RUNBOOK.md`;
- `SYSTEM_RELEASE.md` / `REALTIME_PROJECT.md` / handoffs → normalized `STATE.md` pointer;
- authority/storage semantics → `docs/architecture/*`;
- Drive persistence boundaries → `SECURITY.md` + `.gitignore`.

The repository intentionally prefers one stable contract per concern over duplicating mutable prose across many files.

## Kept in Drive / operational storage

These are **not copied into the public repository**:

- `HOTELS_MASTER` live spreadsheet data;
- operational SQLite shadows and snapshots;
- raw runtime/meta graph payloads containing operational state;
- candidate/contact/private evidence rows;
- CV/portfolio/private media;
- generated operational exports;
- temporary staging and recovery payloads.

## Why

Drive remains the human/control-plane persistence layer and the constrained DB remains the operational state backend. GitHub provides version control and reproducibility without leaking private operational data or creating a competing production database.

## Historical bootstrap reconciliation

At bootstrap, older Drive prose and newer machine state disagreed. The repository used the newer reconciled frontier and recorded older prose as superseded rather than cloning its drift.

That bootstrap frontier is intentionally not repeated here as a live instruction. Future agents must follow `docs/operations/WAVE_OPERATING_PROTOCOL.md` and reconstruct authority before material work.