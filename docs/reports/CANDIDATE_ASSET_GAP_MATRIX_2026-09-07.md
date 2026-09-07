# CANDIDATE ASSET GAP MATRIX — 2026-09-07

Mode: PUBLIC-SAFE RESEARCH RECEIPT / NO PII / NO CLAIM PROMOTION
Authority effect: NONE
Outbound: CLOSED

## Evidence recovered

From private control-plane manifest (not copied here):
- CV_ENTRY_V2: approved asset state reported 2026-09-01.
- CV_HYBRID_V2: approved asset state reported 2026-09-01.
- email signature V1 artifact exists privately; installation was not verified in that manifest.

From public repo architecture:
- Candidate Asset OS V2 requires CV_MASTER_V2 / CV_ENTRY_V2 / CV_HYBRID_V2 / CV_CREATIVE_V2.
- every external claim must trace to Candidate Canon / Claims Ledger.
- HYBRID and CREATIVE lanes require LinkedIn + portfolio + case-study evidence in addition to ENTRY gates.
- open PR #425 contains a professional email signature V2 but is explicitly a salvage/rebase candidate and is not main authority.

## Gap matrix

| Asset / capability | ENTRY | HYBRID | CREATIVE | PORTAL | Current public-safe state | Next gate |
|---|---:|---:|---:|---:|---|---|
| Candidate Canon reconciled | REQUIRED | REQUIRED | REQUIRED | REQUIRED | private authority exists; freshness must be re-read | lane completeness report |
| Claims Ledger | REQUIRED | REQUIRED | REQUIRED | REQUIRED | contract exists | verify every rendered claim ID/version |
| CV_MASTER_V2 | compiler input | compiler input | compiler input | compiler input | required by architecture; approval not proven here | compile from current Canon |
| CV_ENTRY_V2 | REQUIRED | optional | optional | selectable | private approved receipt recovered | role-family specialization QA |
| CV_HYBRID_V2 | optional | REQUIRED | optional | selectable | private approved receipt recovered | current-link/case-study QA |
| CV_CREATIVE_V2 | no | optional | REQUIRED | contextual | not proven approved | build only from curated evidence |
| Portfolio master evidence index | no | REQUIRED | REQUIRED | contextual | not proven complete | evidence archaeology + case-study registry |
| Creative portfolio projection | no | contextual | REQUIRED | contextual | not proven complete | compile role-specific projection |
| Marketing portfolio projection | no | REQUIRED when marketing | REQUIRED when marketing | contextual | not proven complete | compile verified cases/results |
| AI/tech portfolio projection | no | REQUIRED when tech | contextual | contextual | not proven complete | compile code/product evidence |
| LinkedIn | optional | REQUIRED | REQUIRED | contextual | public-safe repo mentions a verified LinkedIn route in salvage PR; main reconciliation pending | verify current live target and consistency |
| Email signature | REQUIRED for email lane | REQUIRED | REQUIRED | N/A for portal-only | V2 salvage PR open; not main authority | rebase/reconcile/test then promote separately |
| Plain-text fallback | REQUIRED | REQUIRED | REQUIRED | N/A | architecture requires | render/readback QA |
| Headshot | optional by CV design | optional | optional | contextual | private asset state not revalidated here | verify current approved image + consent/use |
| ATS QA | REQUIRED | REQUIRED | REQUIRED | REQUIRED | architecture requires | automated extraction + recruiter scan |
| Link validation | REQUIRED when links present | REQUIRED | REQUIRED | REQUIRED when links present | not current-horizon proven | 200/redirect/domain QA immediately before use |
| Language-safe wording | REQUIRED | REQUIRED | REQUIRED | REQUIRED | architecture requires | reconcile with vacancy requirement semantics |
| Availability wording | REQUIRED | REQUIRED | REQUIRED | REQUIRED | private Canon; exact role recheck required | explicit start-window gate |
| Relocation/work-right wording | REQUIRED | REQUIRED | REQUIRED | REQUIRED | route exists conceptually | current official evidence + concise wording |
| Application packet compiler | REQUIRED | REQUIRED | REQUIRED | REQUIRED | architecture target | deterministic asset selector + unsupported-claim rejection |

## Required portfolio case-study contract

Every public case must contain:
1. case_id;
2. project/client identity only when publication is authorized;
3. problem/context;
4. exact candidate responsibility;
5. deliverables;
6. tools/process only when true;
7. outcome/metric with evidence or `OUTCOME_NOT_QUANTIFIED`;
8. artifact/evidence refs;
9. date/time range;
10. confidentiality/publication policy;
11. role-family relevance tags;
12. last_verified.

A visual artifact without verified responsibility is not sufficient evidence for a CV claim.

## CV compiler policy to implement

`CandidateCanon + Claims + VacancyRequirements + RoleFamily + Lane -> SectionSelection -> Wording -> Render -> ATS/Fact/Link QA -> Versioned Asset`

Must be deterministic for identical inputs and reject:
- unapproved claims;
- invented CEFR;
- role titles that overstate evidence;
- stale links;
- private references copied into public artifacts;
- irrelevant creative density that obscures ENTRY fit;
- generic one-CV-fits-all output when role-specific evidence exists.

## Recruiter 10-second contract

Top third of each CV must answer, without inference:
- who is the candidate professionally for THIS role;
- exact target role/family;
- strongest 2–4 relevant evidence-backed capabilities;
- current language truth relevant to the vacancy;
- relocation/availability status in concise form;
- no contradictory lane signal.

## DoD before outbound

- Candidate Canon freshness reviewed;
- all externally used claims resolve to allowed IDs;
- CV_MASTER + required lane CVs approved with hashes;
- portfolio case registry complete enough for every lane actually used;
- signature identity reconciled and render-tested for email lanes;
- live links verified;
- ATS/text extraction PASS;
- 10-second recruiter test PASS;
- no PII/private-reference leakage;
- application compiler rejects unsupported claims and stale assets;
- outbound authorization remains a separate gate.
