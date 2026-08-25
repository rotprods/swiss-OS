# SWITZERLAND_JOB_OS

Evidence-first operating system for securing a viable Swiss hospitality job offer and supporting a sustainable relocation decision.

## North Star

Secure at least one **truthful, legal, verifiable and economically viable Swiss employment offer** that Roberto can realistically accept and use to relocate sustainably.

Hotel counts, research rows, enrichment, drafts and automation are infrastructure — not the mission.

## Live frontier

| Dimension | Current state |
|---|---|
| Release contract | `V6.5-G0800-MAXIMUM-READINESS` |
| Canonical market | `677 / 750` — `CP-0750 ACTIVE` |
| Entity epoch | `HS_ENTITY_EPOCH_2026-08-23_E3` |
| Intelligence coverage | `677 / 677` |
| Graph V2 | `677 / 677` synchronized |
| Current L4 depth | `105 / 677` |
| G-0700 final L9 | `0 / 2050` |
| Candidate lanes | `0 / 4 — BLOCKED_USER_INPUT` |
| Outbound | `CLOSED` |
| `send_allowed` | `0` |
| Next canonical task | `SV2-058 / CP0750-BATCH04` |

## Repository role

GitHub is the **version-control plane** for contracts, architecture, schemas, migrations, tests, runbooks and decision history.

It is **not** the operational database.

```text
GitHub                         Google Drive / Sheets            Operational DB
contracts + code              human/control-plane mirror      constrained state
schemas + migrations          live registries                 PK/FK/UNIQUE/CHECK
runbooks + decisions          executive observability         restore/replay
```

Start with [`GOAL.md`](GOAL.md), [`AGENTS.md`](AGENTS.md), [`STATE.md`](STATE.md) and [`docs/architecture/AUTHORITY_MODEL.md`](docs/architecture/AUTHORITY_MODEL.md).

## Safety boundary

This repository is public. Do not commit SQLite databases, contact exports, candidate private data, credentials, CV/media payloads, raw evidence dumps, or other operational/PII artifacts. See [`SECURITY.md`](SECURITY.md) and [`.gitignore`](.gitignore).
