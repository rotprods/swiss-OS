# NEXT ITERATION PHASES — ZERO-CONTEXT EXECUTION

## Phase 0 — Cold recovery

Before domain work:
1. fetch fresh `main`;
2. read STATE/GOAL/HANDOFF/TASKS;
3. read and validate CSP;
4. read active claims/fencing;
5. re-read Drive/Sheets/DB authority;
6. read NEXT + exact domain pointer;
7. inspect open PRs and concurrent branches;
8. reconcile drift.

Done when one live authority statement, one production NEXT and one set of active claims are proven.

## Phase 1 — Resolve PR #404 concurrency

At handoff PR #404 is OPEN.
- fetch metadata/diff;
- compare base/head to current main;
- confirm token7 claim/fencing;
- confirm no successor supersedes it;
- run/review CI/CSP/adversarial guards;
- merge only if fresh and compatible;
- otherwise supersede and rebuild B07 from fresh main.

GitHub `mergeable=true` is not sufficient evidence.

## Phase 2 — B07/B08 entity resolution

For each exact source key:
- bind coherent source record;
- resolve current first-party/qualified evidence;
- normalize locality;
- inspect same-city and cross-city collisions;
- classify accommodation type/granularity;
- preserve EGR sibling/operator/shared-reception relationships;
- use similarity only to reduce review space;
- emit typed preauthority disposition;
- allocate/reserve no H-ID.

## Phase 3 — CRM universe closure

Target: `CRM_UNIVERSE_COMPLETE = TRUE` only when:
- coherent source universe is frozen;
- all source records are terminally mapped/typed;
- `RECONCILE_REQUIRED = 0`;
- unmapped = 0;
- reverse authority/source gaps resolved;
- SSR/MDM/PAB/CUP gates pass;
- DB/Sheets/control-plane projections agree.

## Phase 4 — Vacancy Wave 3.2

Use 436/436 Vacancy Detail evidence through Application Wave 3.1 protections:
- semantic validity;
- temporal validity;
- ownership scope;
- mandatory requirements;
- route verification.

Quarantine shared vacancy identities until employer/property scope is known.

## Phase 5 — Private Candidate Truth

Private-only: contact truth, languages, availability, role-specific CVs, portfolio/case-study evidence, founder/operator claims and relocation positioning. Never commit private Candidate Truth to public GitHub.

## Phase 6 — AAG-3.1

Any candidate/vacancy pair needs 16/16 hard gates plus the adversarial questionnaire, risk/confidence/human-resonance requirements and recruiter gate. `APPLICATION_READY_NO_SEND` remains no-send.

## Phase 7 — Authorized canary outbound

Only after CRM gate, candidate truth/assets, correct route, suppression, idempotency and explicit human authorization. Start small; measure outcomes; do not bulk-send.

## Permanent invariant

```text
open PR != authority
staging != authority
cache != authority
research != application
ready != send
```
