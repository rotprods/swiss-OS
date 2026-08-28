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

`STATE.md` is the **only mutable current-state pointer in the repository**. README and AGENTS deliberately do not duplicate live counts/frontiers.

## Repository role

GitHub is the **version-control and executable-contract plane** for architecture, schemas, migrations, tests, runbooks, operating protocol and durable decision logic.

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
→ EXECUTE BOUNDED TASK
→ STAGE/CANARY
→ VALIDATE
→ DB COMMIT
→ SHEETS MIRROR
→ GRAPH / INTELLIGENCE
→ INVARIANTS / SLO
→ METRICS / SCHEDULER / TRANSITIONS
→ GITHUB HANDOFF
→ LIBRARY RECOVERY
→ FINAL RECONCILIATION
```

If a required authority plane is unavailable, the wave switches to `DEGRADED_CANARY` and cannot advance canonical state.

## Run the core

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m swiss_os.cli manifest validate tests/fixtures/manifest_superseded.json
```

## Safety boundary

This repository is public. Do not commit SQLite databases, contact exports, candidate private data, credentials, CV/media payloads, raw evidence dumps or other operational/PII artifacts. See [`SECURITY.md`](SECURITY.md) and [`.gitignore`](.gitignore).
