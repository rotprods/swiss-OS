# ENGINE REGISTRY — SWITZERLAND_JOB_OS

Version: **ER-1.0**  
Status: **CANONICAL ARCHITECTURE CONTRACT**

This registry defines the engines that collectively implement SWITZERLAND_JOB_OS. It is intentionally bounded: an engine exists only when it owns a distinct responsibility, authority boundary, invariant set or persistent output.

Mutable frontier counts do not live here. Current state lives in the live control plane, authority-eligible manifests and `STATE.md`.

## Global engine contract

Every engine MUST declare:

```text
purpose
inputs
outputs
source/authority requirements
persistence surfaces
graph impact
minimum invariants
fail-closed condition
```

Every material cross-engine mutation executes inside `docs/operations/WAVE_OPERATING_PROTOCOL.md`.

## E01 — Mission Commander

**Purpose** — optimize G-0001 and prevent local metrics from replacing the North Star.

**Inputs** — `GOAL.md`, live GOAL_STATE, checkpoints, current blockers, candidate truth.

**Outputs** — wave scope, priority, accepted Definition of Done, escalation/block decisions.

**Persistence** — GitHub contracts; Drive goal/checkpoint state when available.

**Graph impact** — `META`.

**Minimum invariants** — no checkpoint/volume metric may be treated as final success; G-0001 closes only on a verified viable accepted offer.

**Fail closed when** — goal hierarchy or current checkpoint authority is ambiguous.

## E02 — Authority & Reconciliation Engine

**Purpose** — reconstruct the last authority-eligible synchronized state and detect drift between DB, Sheets, manifests, Graph/Intelligence and GitHub pointers.

**Inputs** — constrained DB, live Sheets/control plane, manifests, `STATE.md`, recovery pointers.

**Outputs** — authority parent, epoch, reconciled counts, drift report, permitted execution mode.

**Persistence** — run/preflight records, issues, handoff/state pointer.

**Graph impact** — `META` or `BOTH` when operational repair is required.

**Minimum invariants** — exact active PK reconciliation; no canary count may become authority; parent epoch/manifest must be explicit.

**Fail closed when** — required authority plane is unavailable or contradictory.

## E03 — Wave Transaction Engine

**Purpose** — wrap every material mutation in a bounded transaction-like execution envelope.

**Inputs** — authority state, scheduler task, batch limit, graph impact.

**Outputs** — wave/run identity, execution mode, closure state, final reconciliation.

**Persistence** — RUN_LOG, transitions, GitHub handoff, Library recovery.

**Graph impact** — declared per wave: `NONE | META | OPERATIONAL | BOTH`.

**Minimum invariants** — exactly one closure state; no anonymous material mutation; DB→Sheets→Graph/Intelligence→observability is one logical promotion chain.

**Fail closed when** — a required downstream promotion step fails.

## E04 — Market Discovery Engine

**Purpose** — discover candidate Swiss hospitality entities and market evidence without conflating discovery with canonical promotion.

**Inputs** — current first-party sources, bounded search scopes, discovery backlog.

**Outputs** — staged candidate identities and Search Proof.

**Persistence** — discovery candidate registry/evidence ledger.

**Graph impact** — `OPERATIONAL` only after canonical promotion; staging may remain off-graph or in a staging scope.

**Minimum invariants** — historical/index sources remain discovery-only unless current scope is proven; source scope is typed.

**Fail closed when** — identity or source scope is ambiguous.

## E05 — Entity Resolution Engine

**Purpose** — normalize names/cities/domains, deduplicate, resolve aliases/groups and preserve immutable physical lineage.

**Inputs** — staged identity, active canonical set, alias/group registry, domains.

**Outputs** — `NEW_CANONICAL | ALIAS | GROUP_RELATION | RECONCILE_REQUIRED | REJECT`.

**Persistence** — canonical entity state, alias/group relations, resolution evidence.

**Graph impact** — `OPERATIONAL`.

**Minimum invariants** — immutable IDs; zero unexplained active name+city conflicts; zero active non-empty domain conflicts; superseded IDs retain explicit targets.

**Fail closed when** — duplicate/alias target cannot be resolved deterministically.

## E06 — Evidence Engine

**Purpose** — store what each source actually proves, with provenance, scope, observation time, freshness, confidence and conflict state.

**Inputs** — source observations and entity context.

**Outputs** — typed claims/evidence records and unknown/search-proof state.

**Persistence** — evidence ledger, Search Proof, TTL/freshness metadata.

**Graph impact** — `OPERATIONAL`.

**Minimum invariants** — evidence > inference; weaker source scope is never silently upgraded; `UNKNOWN_AFTER_SEARCH` requires valid search proof.

**Fail closed when** — a send-critical or promotion-critical claim lacks adequate provenance/scope.

## E07 — Vacancy Engine

**Purpose** — resolve current vacancies, careers routes, role requirements and vacancy freshness.

**Inputs** — official careers/property pages, allowed secondary sources, entity identity.

**Outputs** — vacancy records, role requirements, source tier, freshness/TTL.

**Persistence** — vacancy registry and evidence.

**Graph impact** — `OPERATIONAL`.

**Minimum invariants** — property vacancy, group careers route and secondary vacancy are distinct states; stale roles cannot be presented as open.

**Fail closed when** — current vacancy status cannot be verified for send-critical use.

## E08 — Housing Engine

**Purpose** — distinguish role-linked housing, employer policy, staff accommodation signals and generic local housing context.

**Inputs** — vacancy/property/employer evidence.

**Outputs** — typed housing facts/unknowns with evidence and freshness.

**Persistence** — housing registry/evidence.

**Graph impact** — `OPERATIONAL`.

**Minimum invariants** — no inference from hospitality norms; vacancy-linked housing is not equivalent to general employer housing policy.

**Fail closed when** — housing claim is unsupported or stale.

## E09 — People Engine

**Purpose** — resolve public-professional hiring/recruitment/management contacts with role and employer scope.

**Inputs** — official team/contact/careers sources and public-professional sources.

**Outputs** — person identities, roles, employer scope, confidence/freshness.

**Persistence** — people registry and evidence.

**Graph impact** — `OPERATIONAL`.

**Minimum invariants** — purpose-limited public-professional data only; role/employer scope explicit; stale personal data queued for refresh/deletion.

**Fail closed when** — identity or employer relationship is uncertain.

## E10 — Channel Engine

**Purpose** — determine allowed recruitment/contact routes and channel-specific policy.

**Inputs** — careers/contact routes, person records, employer portal policy.

**Outputs** — channel records, ownership, portal/email/DM eligibility and restrictions.

**Persistence** — channels + owner edges + suppression/policy facts.

**Graph impact** — `OPERATIONAL`.

**Minimum invariants** — phone does not imply WhatsApp; portal-only overrides preferred email/DM; channel owner edge must be explicit.

**Fail closed when** — channel legality/policy/ownership is unresolved for an external action.

## E11 — Intelligence Engine

**Purpose** — progressively resolve hotel-level intelligence from identity seed through deeper L4/L9 packages.

**Inputs** — canonical hotel, evidence from vacancy/housing/people/channel/social/digital/tech research.

**Outputs** — dimension states, evidence coverage, freshness, conflict status, intelligence depth stage.

**Persistence** — Intelligence registry and depth-stage state.

**Graph impact** — `OPERATIONAL`.

**Minimum invariants** — exactly one Intelligence node/package per active canonical entity; typed unknowns do not count as known values; dimension states are evidence-backed.

**Fail closed when** — intelligence denominators or PK mapping diverge from the active canonical set.

## E12 — Operational Graph Engine

**Purpose** — maintain PK-keyed relationships across hotels, aliases/groups, evidence, vacancies, housing, people, channels, tasks, applications and outcomes.

**Inputs** — authoritative operational mutations.

**Outputs** — nodes/edges with deterministic IDs and referential semantics.

**Persistence** — constrained graph tables + human-readable projections where useful.

**Graph impact** — `OPERATIONAL` by definition.

**Minimum invariants** — no authoritative operational mutation may leave its required graph representation behind; no orphan nodes/edges; one canonical→Intelligence relation where applicable.

**Fail closed when** — graph denominator or required edge set diverges from canonical state.

## E13 — Project Memory Meta Graph Engine

**Purpose** — preserve durable relationships among goals, checkpoints, releases, waves, decisions, architecture and artifacts.

**Inputs** — material system decisions and wave closures.

**Outputs** — project-memory nodes/edges and artifact lineage.

**Persistence** — GitHub public-safe docs/registries; Drive project memory when available.

**Graph impact** — `META`.

**Minimum invariants** — meta graph never substitutes for the operational graph; current-state pointers are not duplicated as historical truth.

**Fail closed when** — artifact/release/wave lineage is contradictory.

## E14 — Scheduler & TTL Engine

**Purpose** — turn unresolved/stale work into deterministic idempotent tasks ordered by priority, dependencies and freshness.

**Inputs** — canonical entities, unresolved dimensions, TTL expiry, issues/checkpoints.

**Outputs** — READY/ACTIVE/BLOCKED/COMPLETE/FAILED/CANCELLED tasks.

**Persistence** — scheduler tables/control-plane mirror.

**Graph impact** — `OPERATIONAL` for entity-scoped tasks; `META` for project tasks.

**Minimum invariants** — active-task anti-join by scope/type/freshness; completed work is not re-enqueued for identical freshness; dependencies explicit.

**Fail closed when** — duplicate active task keys or stale critical facts lack refresh tasks.

## E15 — Scoring & Prioritization Engine

**Purpose** — prioritize research/application opportunities with declared 0–100 heuristic dimensions.

**Inputs** — evidence-backed market/candidate/intelligence features.

**Outputs** — scores, confidence, reason vectors and blockers.

**Persistence** — versioned score records.

**Graph impact** — `OPERATIONAL` where score attaches to an entity/vacancy/application.

**Minimum invariants** — scores are heuristics, not calibrated hiring probabilities; scale/version declared; unsupported features prohibited.

**Fail closed when** — score depends on missing/unsupported claims.

## E16 — Candidate Truth & Asset Engine

**Purpose** — maintain lane-specific candidate facts, CV/case-study/portfolio requirements and claim provenance.

**Inputs** — user-confirmed/asserted facts and approved artifacts.

**Outputs** — ENTRY/HYBRID/CREATIVE/PORTAL readiness states and deterministic assets.

**Persistence** — private candidate store outside the public repo; public repo stores only contracts.

**Graph impact** — `OPERATIONAL` for candidate/application relationships, subject to privacy boundaries.

**Minimum invariants** — never fabricate phone, CEFR, availability, portfolio, metrics, employment or cases; lane independence preserved.

**Fail closed when** — required lane facts/assets are unverified.

## E17 — Template / Message Engine

**Purpose** — render deterministic evidence-backed employer-facing copy and application packages.

**Inputs** — approved candidate lane facts, vacancy/employer evidence, channel policy.

**Outputs** — versioned draft/render artifacts.

**Persistence** — private artifacts; public repo stores templates/contracts only.

**Graph impact** — `OPERATIONAL` when attached to an application route.

**Minimum invariants** — no unsupported personalization; rendering is deterministic/versioned; draft state is not send authorization.

**Fail closed when** — send-critical source/candidate facts are unresolved.

## E18 — QA / Governance Engine

**Purpose** — evaluate invariants, SLOs, semantic gates and checkpoint eligibility independently of production volume.

**Inputs** — DB/control-plane/Graph/Intelligence/run state.

**Outputs** — PASS/FAIL results, issues, closure eligibility.

**Persistence** — invariant/SLO/issue/run records.

**Graph impact** — `META`, plus audit edges where useful.

**Minimum invariants** — integrity/FK/duplicates/drift/replay/restore/DB↔Sheets/Graph/Intelligence/send lock; checkpoint requires gates, not merely target count.

**Fail closed when** — any P0 applicable invariant fails.

## E19 — Observability Engine

**Purpose** — expose what happened, what changed, what is blocked and what the next bottleneck is.

**Inputs** — wave execution, metrics, health, SLO, issues, scheduler.

**Outputs** — unique metrics, health state, run logs, transitions and state digest.

**Persistence** — control-plane observability + public-safe `STATE.md` pointer.

**Graph impact** — `META`.

**Minimum invariants** — one active metric key per semantic metric; authoritative vs canary counts separated; next bottleneck explicit.

**Fail closed when** — observability contradicts constrained state.

## E20 — Recovery & Persistence Engine

**Purpose** — make a material wave recoverable after context loss, connector outage or concurrent-agent interruption.

**Inputs** — latest DB/manifest, wave state, public-safe handoff, recovery pointers.

**Outputs** — recovery bundle, SHA/manifest, `LATEST_RECOVERY` pointer and cold-store copy.

**Persistence** — ChatGPT Library and Drive when available; GitHub stores public-safe recovery semantics only.

**Graph impact** — `META`.

**Minimum invariants** — canary bundles labeled CANARY; authority bundles labeled AUTHORITATIVE only after full promotion; latest pointer names exact artifact lineage.

**Fail closed when** — recovery artifact cannot be traced to its authority/canary parent.

## E21 — Git / CI Engine

**Purpose** — version architecture/code/contracts and prevent regressions before merge.

**Inputs** — branch changes, tests, contract guards.

**Outputs** — PR, CI results, reviewed merge commit.

**Persistence** — GitHub.

**Graph impact** — `META` for material architecture/release changes.

**Minimum invariants** — branch→tests→PR→CI→diff/review→merge; public-repo secret/PII guard; stable-doc state-drift guard.

**Fail closed when** — CI or review gate fails.

## E22 — Security / Privacy / Outbound Gate Engine

**Purpose** — enforce public-repo boundaries, privacy/purpose limitation, suppression, idempotency and irreversible-action authorization.

**Inputs** — candidate/channel/application state, suppression state, explicit authorization.

**Outputs** — action eligibility or hard block.

**Persistence** — private operational state; public repo only stores policy/contracts.

**Graph impact** — `OPERATIONAL` for application/action state and `META` for policy decisions.

**Minimum invariants** — default `OUTBOUND = CLOSED`, `send_allowed = 0`; no implicit authorization; no CAPTCHA/auth/paywall bypass; opt-outs/rejections propagate.

**Fail closed when** — any applicable authorization, evidence, freshness, suppression, channel or idempotency gate is missing.

## Cross-engine production sequence

The canonical material-production path is:

```text
Mission Commander
→ Authority & Reconciliation
→ Wave Transaction
→ Scheduler
→ Discovery / Evidence
→ Entity Resolution
→ Domain Engines
→ Stage / Canary
→ Data Commit
→ Graph + Intelligence
→ QA / Governance
→ Observability
→ Git / CI where system definition changed
→ Recovery / Persistence
→ Final Reconciliation
→ Wave Close
```

No engine may claim a successful authoritative mutation while an affected downstream engine in this sequence remains unsynchronized.