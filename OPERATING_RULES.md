# OPERATING_RULES — V6.2

1. Truth > volume.
2. Evidence > inference.
3. Direct current first-party evidence > secondary sources for send-critical claims.
4. Never invent candidate facts, credentials, language levels, employment, clients, metrics, housing, vacancies, people, channels or internal business gaps.
5. Preserve truth states: OBSERVED / DIRECT / INFERRED / USER_CONFIRMED / USER_ASSERTED / UNVERIFIED / UNKNOWN_AFTER_SEARCH.
6. `UNKNOWN_AFTER_SEARCH` is valid only after the minimum search contract is recorded.
7. Resolution completeness, known-value coverage, evidence coverage and freshness are separate metrics.
8. Canonical IDs are immutable; aliases merge through entity resolution.
9. Canonical operational storage is physical/idempotent; no spill-based primary storage.
10. Every authoritative table has a schema version. Schema changes require a migration identifier.
11. Numeric scales are declared. New scoring uses 0–100 unless schema states otherwise.
12. Every material claim stores provenance, observed_at, freshness, confidence and conflict state.
13. Current T1 source outranks lower tiers; conflicts must use deterministic precedence and role-vs-employer scope.
14. No state promotion without QA and a state-transition record.
15. Every live metric has one canonical metric ID.
16. Snapshot coverage and canonical count update atomically.
17. Scheduler uses canonical IDs, anti-joins completed work and creates explicit REFRESH tasks for stale facts.
18. Legacy scheduler and V1 application routes are never execution sources.
19. Candidate readiness is lane-specific; market readiness is independent; irreversible send requires explicit approval.
20. No external action without suppression check and an idempotency key.
21. Any opt-out, rejection, role-filled state or do-not-contact request propagates to relevant future actions.
22. Portal-only policy overrides preferred email/DM copy.
23. Public-professional contact data only; purpose-limit it and refresh/delete stale personal data.
24. Never bypass CAPTCHA, authentication, paywalls, robots, anti-bot systems or provider restrictions.
25. Do not submit roles with hard unmet requirements unless the employer explicitly permits equivalents/flexibility.
26. Employer-facing motivation stays positive; never frame relocation as political grievance.
27. Overtime is flexibility for additional paid hours where lawful, never unpaid labor.
28. Financial fields distinguish published facts, sourced assumptions and personal reserves.
29. Migrations follow STAGE → CANARY → VALIDATE → COMMIT → ROLLBACK.
30. Google Sheets is the executive/control plane; operational state is constrained in SQLite or a verified successor backend.
31. Every substantial run updates issues/invariants/metrics/health/run log and material-memory artifacts.
32. No checkpoint is complete because a counter reached a target; invariants and quality gates must pass.
33. Every material mutation executes inside a named WAVE under `docs/operations/WAVE_OPERATING_PROTOCOL.md`.
34. A physically valid local canary is non-authoritative until the full synchronization chain passes.
35. `AGENTS.md` must contain stable behavior only; mutable task/frontier state belongs in live control-plane data and `STATE.md`.
36. Sheets mutations resolve canonical keys/PKs; blind positional writes are prohibited for authoritative data.
37. Every authoritative entity/evidence/task mutation synchronizes the affected operational graph in the same wave.
38. ChatGPT Library is recovery/cold persistence, never operational truth.
39. If a required authority layer is unavailable, switch to `DEGRADED_CANARY` or `READ_ONLY_RESEARCH`; fail closed on canonical promotion.
40. “Real-time” means synchronous reconciliation before an authoritative wave closes; no background daemon is implied.
41. Every material wave closes as `COMPLETE_AUTHORITY`, `COMPLETE_READ_ONLY`, `SAFE_STOP_CANARY`, `BLOCKED_P0`, or `SUPERSEDED`.
42. Outbound remains independently hard-gated and CLOSED unless all applicable gates plus explicit authorization pass.
43. The complete CRM universe is a hard prerequisite to outbound: `CRM_UNIVERSE_COMPLETE = TRUE` must be proven against a frozen verified directory snapshot before any send gate may open.
44. CRM completeness means every snapshot source record is deterministically mapped; an intermediate canonical count or checkpoint can never substitute for 100% source-record coverage.
45. A changing upstream directory count creates a new versioned snapshot observation; it never silently rewrites the denominator of an in-flight wave.