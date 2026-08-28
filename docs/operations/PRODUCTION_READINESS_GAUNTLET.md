# PRODUCTION READINESS GAUNTLET — SWITZERLAND_JOB_OS

Version: **PRG-1.0**  
Status: **CANONICAL QA CONTRACT**

This gauntlet is the release/wave-level adversarial review for deciding whether SWITZERLAND_JOB_OS may continue production work or advance canonical authority.

It complements the Wave Operating Protocol. WOP defines *how work executes*; this document defines *what must be true before the system calls itself ready*.

## Result vocabulary

Every gate returns exactly one:

```text
PASS
PASS_WITH_DEFERRED_NONCRITICAL
BLOCKED
NOT_APPLICABLE
```

A `P0` blocked gate prevents `COMPLETE_AUTHORITY`.

## G00 — North Star integrity

Verify:

- G-0001 remains the optimization target;
- infrastructure metrics are not substituted for a verified viable accepted offer;
- current wave scope has a clear contribution to G-0001;
- unnecessary infrastructure work is rejected.

Failure examples:

- optimizing canonical count without decision/application value;
- building a new platform because it is interesting rather than required.

## G01 — Authority reconstruction

Verify:

- authority parent is explicit;
- authority epoch is explicit;
- physical vs active semantics reconcile;
- canary state is clearly separated from authority;
- current live control-plane state was re-read when available;
- stale prose never silently wins.

P0 on contradiction or unavailable required authority plane for a write wave.

## G02 — Capability preflight

Verify availability/limitations of:

```text
Drive/Sheets read/write
constrained DB bytes/parent
GitHub read/write + CI
web/evidence access when needed
Library persistence when material recovery is required
outbound provider only if separately authorized
```

A missing authority layer changes execution mode before work begins.

## G03 — Data integrity

Applicable checks:

```text
SQLite integrity_check = ok
foreign_key_check = 0
PK uniqueness = PASS
CHECK/UNIQUE domains = PASS
unexplained ID gaps = 0
invalid alias targets = 0
active name+city conflicts = 0
active non-empty domain conflicts = 0
```

## G04 — Restore / replay / idempotency

Verify:

- replay produces zero unintended inserts/side effects;
- restore passes logical equivalence;
- schema and table sets reconcile;
- source↔restore bidirectional content differences are empty;
- external action idempotency is independent from DB replay.

Binary SHA equality is a transfer check, not SQLite logical restore equivalence.

## G05 — Entity resolution

Challenge every newly promoted entity:

- could this be an alias of an existing hotel?
- could city/location normalization hide a duplicate?
- could a shared group/domain create a false merge?
- could the source describe a parent company rather than property?
- is a superseded ID being accidentally resurrected?

Promotion is blocked on unresolved material identity conflict.

## G06 — Evidence scope and provenance

Verify:

- evidence tier/scope is explicit;
- current exact detail, current support, historical discovery and secondary evidence remain distinct;
- `observed_at`, provenance and freshness exist where material;
- stronger claims are not inferred from weaker sources;
- unresolved fields remain typed unknown/search pending.

## G07 — Freshness / TTL

Verify:

- send-critical facts are current enough for policy;
- expired facts have refresh tasks;
- stale vacancies are not treated as open;
- stale people/channel records are not used for external routing;
- evidence freshness and known-value state are tracked separately.

## G08 — Scheduler correctness

Verify:

- selected task is the highest-value unblocked canonical task;
- active task keys are unique by declared semantics;
- completed identical-freshness work is anti-joined;
- dependencies are explicit;
- stale facts generate refresh work;
- finished batch tasks are terminalized instead of becoming infinite containers.

## G09 — Graph integrity

Classify `GRAPH_IMPACT` and verify affected scope.

For operational mutations:

- required hotel/entity node exists exactly once;
- aliases/groups use explicit edges;
- evidence/vacancy/person/channel/task relations reference canonical PKs;
- required canonical→Intelligence relationship exists;
- no orphan active nodes/edges;
- graph denominator equals active canonical denominator where applicable.

For meta mutations:

- goal/checkpoint/wave/release/artifact lineage is coherent.

## G10 — Intelligence integrity

Verify:

- exactly one current intelligence package/seed per active canonical hotel where required;
- dimension states are typed;
- resolution, known-value, evidence and freshness are independent;
- L4/L9 promotion is earned by evidence, not inherited from entity creation;
- canary research does not change authoritative depth counters.

## G11 — Candidate truth

For candidate-dependent work verify:

- all facts are user-confirmed/asserted with explicit truth state;
- no invented phone, CEFR, availability, portfolio, employment, clients or metrics;
- lane requirements remain independent;
- ENTRY is not blocked by CREATIVE-only requirements;
- assets used in an application correspond to the selected lane/version.

## G12 — Scoring integrity

Verify:

- scale/version declared;
- evidence-backed features only;
- confidence and blocker/reason vectors included;
- no score presented as calibrated `P(hire)`;
- missing critical information cannot create a misleadingly high rank.

## G13 — Channel / privacy / suppression

Verify:

- channel ownership and route are explicit;
- phone ≠ WhatsApp permission;
- portal-only policy overrides preferred channel;
- public-professional purpose limitation holds;
- opt-outs, rejections and do-not-contact state propagate;
- stale personal contact data is refreshed/deleted per policy.

## G14 — Outbound hard gate

Default:

```text
OUTBOUND = CLOSED
send_allowed = 0
```

No irreversible action unless all applicable evidence, freshness, channel, candidate, suppression, idempotency and explicit-user-authorization gates independently pass.

Research never implies authorization.

## G15 — Observability consistency

Verify emitted state includes:

```text
wave/run identity
execution mode
authority parent/epoch
canonical before/after authoritative
canary count separately
physical before/after authoritative
DB/FK/duplicate/drift state
Graph denominator
Intelligence denominator
issues/SLOs
tasks attempted/completed/failed
closure state
next bottleneck
```

No duplicate semantic metric keys.

## G16 — Documentation / agent consistency

Verify:

- `STATE.md` is the only mutable current-state pointer in GitHub;
- README/GOAL/AGENTS/SYSTEM_MAP/AUTHORITY_MODEL/RUNBOOK contain no live frontier values;
- `AGENTS.md` points to WOP;
- stable docs do not name stale active tasks/parents/counts;
- historical examples are explicitly labeled historical/precedent;
- engine registry and WOP agree on persistence/graph boundaries.

This gate is executable via `scripts/system_contract_guard.py`.

## G17 — Git / CI

For system-definition changes verify:

```text
branch
→ implementation
→ tests/guards
→ PR
→ CI PASS
→ diff/adversarial review
→ merge
```

CI validates repository contracts. It does not prove runtime Drive/DB synchronization.

## G18 — Recovery / cold persistence

For material DB/schema/recovery waves verify:

- recovery bundle exists;
- manifest/digest exists;
- authority vs canary label is explicit;
- SHA recorded where relevant;
- Library latest pointer is updated;
- Drive recovery copy is updated when available/required;
- recovery lineage points to exact parent/wave.

## G19 — Concurrency

Immediately before canonical commit verify live parent has not moved.

Anti-join:

```text
IDs
name+city
aliases/superseded IDs
domains
active task keys
parent manifest/epoch
```

If parent moved: `RECOVERY_RECONCILE`, never force-write.

## G20 — Closure correctness

Wave closes as exactly one:

```text
COMPLETE_AUTHORITY
COMPLETE_READ_ONLY
SAFE_STOP_CANARY
BLOCKED_P0
SUPERSEDED
```

`COMPLETE_AUTHORITY` requires all affected authority/persistence/reconciliation layers to agree.

## Adversarial questions

Before production continuation, attempt to falsify the system with at least these questions:

1. Which layer can currently lie without another layer detecting it?
2. Can a valid local DB accidentally be reported as canonical?
3. Can two agents allocate the same physical ID after a stale handoff?
4. Can a hotel alias inflate checkpoint counts?
5. Can a regional/support page be mislabeled as exact membership?
6. Can a stale vacancy route an application?
7. Can a person/contact become send-eligible merely because a phone/email exists?
8. Can an old README/AGENTS copy override live state?
9. Can Graph/Intelligence lag while canonical counts advance?
10. Can a recovery bundle be confused with authority?
11. Can CI pass while runtime authority is broken?
12. Can a checkpoint close solely because its numeric target was reached?
13. Can a secondary-source fact silently become T1?
14. Can a metric denominator change without dependent backlog recomputation?
15. Can an external action execute twice after retry/replay?

Any unanswered material question becomes an issue or explicit deferred risk before production continuation.

## Production continuation criterion

Production work may continue when:

```text
SYSTEM DESIGN GAUNTLET = PASS
REPOSITORY / CI GAUNTLET = PASS
LATEST AUTHORITY STATE = RECONSTRUCTABLE
NO OPEN APPLICABLE P0
OUTBOUND remains independently gated
```

Canonical write production additionally requires all affected authority planes available and preflight PASS.