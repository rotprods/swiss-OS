# SWITZERLAND_JOB_OS

Evidence-first operating system for securing a viable Swiss hospitality job offer and supporting a sustainable relocation decision.

## North Star

Secure at least one **truthful, legal, verifiable and economically viable Swiss employment offer** that Roberto can realistically accept and use to relocate sustainably.

## Read order

For material execution, read in this order:

1. [`docs/operations/WAVE_OPERATING_PROTOCOL.md`](docs/operations/WAVE_OPERATING_PROTOCOL.md)
2. [`GOAL.md`](GOAL.md)
3. [`STATE.md`](STATE.md)
4. [`AGENTS.md`](AGENTS.md)
5. [`OPERATING_RULES.md`](OPERATING_RULES.md)
6. reconcile against live Drive/Sheets + the latest authority-eligible constrained manifest.

For cross-engine or production-readiness work, also use:

- [`docs/architecture/ENGINE_REGISTRY.md`](docs/architecture/ENGINE_REGISTRY.md)
- [`docs/operations/PRODUCTION_READINESS_GAUNTLET.md`](docs/operations/PRODUCTION_READINESS_GAUNTLET.md)
- [`RUNBOOK.md`](RUNBOOK.md)

`STATE.md` is the **only mutable current-state pointer in the repository**. README, GOAL, AGENTS, RUNBOOK and architecture maps deliberately do not duplicate live counts/frontiers.

## Repository role

GitHub is the **version-control and executable-contract plane** for architecture, schemas, migrations, tests, runbooks, engine contracts, operating protocol and durable decision logic.

Google Drive/Sheets are the human/control-plane mirror. The constrained operational database stores PK/FK/UNIQUE/CHECK-enforced state. ChatGPT Library is a recovery/cold-persistence surface.

```text
GitHub                      Drive / Sheets                  Constrained DB              Library
code + contracts            human control plane            operational state           recovery bundles
schemas + migrations        live registries                PK/FK/UNIQUE/CHECK          manifests/digests
tests + CI                  observability                  restore/replay              cold persistence
STATE pointer               Graph/Intelligence mirror      operational graph truth     NOT operational truth
```

A local DB canary is not canonical by itself. Canonical promotion requires the synchronization chain declared in the Wave Operating Protocol.

## Execution model

Every material mutation executes inside a bounded **WAVE**:

```text
BOOTSTRAP AUTHORITY
→ RECONCILE
→ DISPATCH AFFECTED ENGINES
→ EXECUTE BOUNDED TASK
→ STAGE/CANARY
→ VALIDATE
→ DB COMMIT
→ SHEETS MIRROR
→ GRAPH / INTELLIGENCE
→ INVARIANTS / SLO
→ METRICS / SCHEDULER / TRANSITIONS
→ GITHUB HANDOFF
→ LIBRARY / DRIVE RECOVERY
→ FINAL RECONCILIATION
```

If a required authority plane is unavailable, the wave switches to `DEGRADED_CANARY` and cannot advance canonical state.

## Production readiness

A production continuation or checkpoint promotion is challenged by `PRODUCTION_READINESS_GAUNTLET.md`, covering authority, data integrity, evidence, entity resolution, freshness, scheduler, Graph, Intelligence, candidate truth, scoring, privacy/channel policy, outbound, observability, documentation drift, CI, recovery and concurrency.

CI includes both:

```text
repo_guard.py
system_contract_guard.py
```

The second guard prevents stable architecture/agent documents from silently becoming stale copies of mutable operational state.

## Run the core

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/repo_guard.py
python scripts/system_contract_guard.py
PYTHONPATH=src python -m swiss_os.cli manifest validate tests/fixtures/manifest_superseded.json
```

## Safety boundary

This repository is public. Do not commit SQLite databases, contact exports, candidate private data, credentials, CV/media payloads, raw evidence dumps or other operational/PII artifacts. See [`SECURITY.md`](SECURITY.md) and [`.gitignore`](.gitignore).
