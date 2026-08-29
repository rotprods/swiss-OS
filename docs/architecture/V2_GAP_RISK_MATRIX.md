# V2 GAP / RISK MATRIX

Priority is impact × probability × blast radius × strategic importance ÷ cost, with P0 correctness/security overrides.

| Gap | Sev | Probability | Blast | Detection now | Target fix | Owner | Test / evidence | Phase |
|---|---|---:|---:|---|---|---|---|---|
| No first-class Session/Claim/EventWatermark/ContextPack contract | P0 | High | Project-wide | manual prose/PR inspection | coordination kernel + ledger/projections | Agentic/Event architects | V2 unit + death drill | P5–P9 |
| Duplicate coordination action on retry | P0 | Medium | Multi-agent | human noticing; escaped in this session | deterministic idempotency + collision guard | Reliability/Test | duplicate event/idempotency regression | P5/P10 |
| Stale writer after concurrent main movement | P0 | High | State/architecture | ancestry convention | main pin + fencing + pre-merge reread | Git/CI + Agentic | stale-main ContextPack rejection | P7–P14 |
| `STATE.md` can describe newer counters while parent pointer lags live main | P1 | High | Handoff | human comparison | machine project-state + ancestry guard | Observability | state/main consistency guard | P6/P10 |
| Stale/overlapping PRs remain open after semantic supersession | P1 | High | Coordination | manual PR reading | explicit SUPERSEDED relation + claims | Mission/Git | PR semantic inventory receipt | P8/P14 |
| Handoff information fragmented across many historical files | P1 | High | Continuity | directory browsing | root HANDOFF + hash-pinned ContextPack | Memory/Docs | 5-minute death drill | P8/P9 |
| Projection could become hidden authority | P0 | Medium | Authority | prose warnings | `DERIVED_FROM` contract + rebuild test | Graph/Data | delete/rebuild projection equality | P7/P11 |
| Similarity evidence misused as identity authority | P0 | Medium | Canonical IDs | current domain guards | preserve review-only semantics in V2 lexicon | Entity/QA | no fuzzy auto-bind tests | Domain + P10 |
| Public repo could receive secrets/PII via new event payloads | P0 | Low–Med | Security | repo_guard | public-safe event schema + guard | CISO | repo guard + malicious fixture | P12 |
| Claim itself could escalate authority | P0 | Medium | Authority/outbound | none machine-native | immutable authority ceiling/excluded scopes | CISO/Agentic | outbound/H-ID boolean tests | P5/P12 |
| External provider key blocks SSR structured equivalence | P0 domain | High until credential | G-0500 | typed blocker | acquire key or continue qualified MEP fallback | Operator/Discovery | capture-valid manifest | domain |
| Full terminal coverage rebuild lags latest incremental delta | P1 domain | Medium | reverse-gap hash | STATE warning | deterministic rebuild/re-attestation | Entity/Data | 657 coverage hash receipt | domain |
| No local network from current runtime | P2 | High in this activation | DX only | tool failure | use GitHub API/Actions; do not make local cache authority | Tool/Git | CI evidence | current activation |
| Branch protection disabled on main | P1 | Medium | repository integrity | branch metadata | enable protected-main only after checking solo workflow friction | Git/DevSecOps | ruleset/PR-only write proof | P14 decision |
| V2 docs could duplicate V1 contracts | P1 | Medium | Cognitive | review | KEEP/REFINE map + root canonical pointer | Architecture/Docs | contract guard | P4/P9 |

Residual uncertainty must be a typed blocker/risk/unknown; no gap is considered closed from prose alone.
