# SWITZERLAND_JOB_OS

Evidence-first operating system for securing a viable Swiss hospitality job offer and supporting a sustainable relocation decision.

## North Star

Secure at least one **truthful, legal, verifiable and economically viable Swiss employment offer** that Roberto can realistically accept and use to relocate sustainably.

## Current state

| Dimension | Current state |
|---|---|
| Physical hotel rows | `677` |
| Superseded duplicate rows | `4` |
| Active canonical entities | `673` |
| Active canonical checkpoint | `CP-0750 — 673 / 750` |
| Control-plane counter | `677` — drift pending reconciliation |
| G-0700 final L9 | `0 / 2050` |
| Candidate lanes | `0 / 4 — BLOCKED_USER_INPUT` |
| Outbound | `CLOSED` |
| `send_allowed` | `0` |

The distinction between physical rows and active canonical entities is executable and tested in `src/swiss_os`.

## Repository role

GitHub is the **version-control and executable-contract plane** for architecture, schemas, migrations, tests, runbooks and durable decision logic. Google Drive/Sheets remain the human/control-plane mirror and the constrained operational database remains the authoritative state backend.

```text
GitHub                         Google Drive / Sheets            Operational DB
contracts + executable core   human/control-plane mirror      constrained state
schemas + migrations          live registries                 PK/FK/UNIQUE/CHECK
tests + decisions             executive observability         restore/replay
```

## Run the core

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m swiss_os.cli manifest validate tests/fixtures/manifest_superseded.json
```

Start with [`GOAL.md`](GOAL.md), [`STATE.md`](STATE.md), [`AGENTS.md`](AGENTS.md) and [`docs/architecture/EXECUTABLE_CORE.md`](docs/architecture/EXECUTABLE_CORE.md).

## Safety boundary

This repository is public. Do not commit SQLite databases, contact exports, candidate private data, credentials, CV/media payloads, raw evidence dumps or other operational/PII artifacts. See [`SECURITY.md`](SECURITY.md) and [`.gitignore`](.gitignore).
