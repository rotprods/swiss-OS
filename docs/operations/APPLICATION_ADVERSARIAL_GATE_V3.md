# Application Adversarial Gate — AAG-3.0

Status: **CURRENT PROPOSED SYSTEM DEFINITION / NO-SEND**

AAG-3.0 is the mandatory final pre-outbound quality gate for Swiss employment application packets. It is downstream of current vacancy evidence, private Candidate Truth, lane-specific assets and the recruiter 10-second gate. It never authorizes sending.

## Objective

Evaluate an application from the adversarial perspective of the people who can reject it:

1. ATS / recruiter;
2. department head;
3. HR manager;
4. General Manager / CEO;
5. Brand / PR;
6. candidate long-term fit.

The system optimizes for **low perceived hiring friction and risk first, exact fit second, trust third, motivation/likeability next, differentiation/upside last**. Creative or founder differentiation can never compensate for a failed mandatory job requirement.

## Hard-gate semantics

AAG uses non-compensable hard gates for:

- current vacancy;
- exact verified role;
- mandatory language;
- work eligibility;
- mandatory experience where the role requires it;
- compatible start date;
- verified application route;
- unsupported external claims;
- suppression state;
- duplicate application state;
- already-filled vacancy.

`FALSE` on an expected-positive gate or `TRUE` on an expected-negative gate is a terminal hard failure. `UNKNOWN` prevents readiness and places the packet in LIMBO. Soft scores never offset a hard failure.

## 100-point quality model

AAG produces a 0–100 `APPLICATION_QUALITY_SCORE` across 19 dimensions whose weights total exactly 100:

| Dimension | Weight |
|---|---:|
| Eligibility / permit | 8 |
| Vacancy freshness | 8 |
| Hard requirement match | 10 |
| Role evidence match | 9 |
| Language match | 7 |
| Start / schedule availability | 5 |
| Relocation / logistics | 4 |
| Experience credibility | 7 |
| Operational readiness | 6 |
| Brand fit | 4 |
| Motivation specificity | 4 |
| Retention / permanence | 4 |
| Employer-risk profile | 5 |
| Additional-value relevance | 5 |
| Portfolio / proof | 5 |
| Email communication | 4 |
| ATS / deliverability | 3 |
| Reply friction | 1 |
| Housing / economic compatibility | 1 |

These weights are an operational heuristic, **not a calibrated probability of hire**. The output is explicitly labelled `HEURISTIC_UNCALIBRATED_UNTIL_OUTCOME_SAMPLE`. Calibration must use real response/interview/offer outcomes later.

## Independent scores

AAG deliberately refuses to hide important weaknesses inside one average. In addition to quality it reports:

- `EVIDENCE_CONFIDENCE_SCORE` — how well the claims are actually supported;
- `EMPLOYER_RISK_SCORE` — 0 is ideal, 100 is high risk;
- `HUMAN_RESONANCE_SCORE` — credible motivation, likeability, humility and fit;
- `DESPERATION_SCORE` — 0 is ideal; detects any-role framing, victimhood, excessive flattery, unlimited-free-work signals and related risk;
- `CONFIDENCE_ADJUSTED_SCORE` — explicitly heuristic ordinal summary, never a probability.

Employer-risk components are: flight, overqualification, hierarchy/ego, operational credibility, language, relocation, housing, role confusion, brand and retention.

## 100-question adversarial bank

Every packet is evaluated against exactly 100 questions:

```text
eligibility                10
vacancy requirements       15
languages                  10
experience                 10
operational credibility    10
employer risk              10
culture / brand            10
evidence                   10
relocation                  5
email                       5
portfolio                   5
TOTAL                     100
```

Answers are `PASS`, `WEAK`, `FAIL` or `UNKNOWN`. Critical failures are terminal rejects. Critical unknowns force LIMBO. All 100 questions require an explicit answer before readiness.

The executable canonical bank lives in `src/swiss_os/application_adversarial.py`; documentation must not become a second independently maintained question source.

## Six-stakeholder unanimity

An application cannot become ready unless all six stakeholder votes are explicitly YES:

```text
ATS_RECRUITER
DEPARTMENT_HEAD
HR_MANAGER
GENERAL_MANAGER_CEO
BRAND_PR
CANDIDATE_LONG_TERM_FIT
```

Five out of six is LIMBO.

## Readiness thresholds

A packet may become `APPLICATION_READY_NO_SEND` only when all are true:

```text
hard failures                  = 0
hard unknowns                  = 0
critical-question failures     = 0
critical-question unknowns     = 0
100 questions answered explicitly
all 19 quality dimensions known
all 10 employer-risk dimensions known
stakeholder votes              = 6 / 6 YES
APPLICATION_QUALITY_SCORE      >= 92
EVIDENCE_CONFIDENCE_SCORE      >= 95
EMPLOYER_RISK_SCORE            <= 20
DESPERATION_SCORE              <= 15
HUMAN_RESONANCE_SCORE          >= 85
```

If the same contract passes with `APPLICATION_QUALITY_SCORE >= 97`, decision becomes `ELITE_MATCH`.

Neither state authorizes sending.

## Decision states

```text
0–59   REJECT
60–74  WEAK
75–84  PROMISING
85+    LIMBO unless every readiness gate passes
92+    APPLICATION_READY_NO_SEND when every readiness gate passes
97+    ELITE_MATCH when every readiness gate passes
```

A hard failure is `REJECT` regardless of the aggregate quality score.

## Candidate-positioning adversarial rules

### Founder / CEO background

Founder/operator experience may demonstrate responsibility, initiative and ownership. It is not the primary signal for operational roles and requires evidence before use. The application must answer the implicit employer objection: **why will this candidate genuinely stay and perform this job?**

Preferred operational framing is high ambition with low ego: willingness to start where useful, learn hotel standards, respect hierarchy, contribute reliably and build a long-term Swiss career.

### Permanent relocation

The candidate's objective may be permanent/indefinite relocation while remaining open to a suitable seasonal first contract. Permanent intent must not be rendered as a demand for an immediately permanent contract.

### Creative / digital upside

Photography, video, design, content, signage, ads, campaigns, websites and automation are secondary upside. They never substitute for the target role. Any recurring creative contribution requires employer approval and lawful agreed scope/working-time treatment or another explicit arrangement.

### Switzerland / employer motivation

Specific evidence-grounded appreciation is positive. Generic superlatives, fake praise, political grievance, victimhood and manipulative psychology are forbidden. Nature/location references must be specific enough to show actual research rather than tourism clichés.

## Email / signature posture

The email itself must remain low-friction:

```text
WHO
EXACT ROLE
ROLE FIT
ELIGIBILITY
AVAILABILITY
SPECIFIC MOTIVATION
OPTIONAL DIFFERENTIATOR
SIMPLE CTA
```

HTML is static enhancement only. No JavaScript, iframe, forms, hidden active tracking or fake interactivity. Plain-text fallback remains mandatory. Rich interaction belongs on an external verified recruiter landing/portfolio, not inside the email body.

## Integration contract

```text
current vacancy evidence
→ VFA-2.0 public seed
→ private Candidate Truth
→ lane-specific CV/assets
→ AAG-3.0 evaluation
→ AAG receipt
→ recruiter_10_second_gate()
→ APPLICATION_READY_NO_SEND / ELITE_MATCH
→ explicit user authorization remains separately required
```

`recruiter_10_second_gate()` now fails closed unless Candidate Truth contains an AAG-3.0 receipt whose decision is `APPLICATION_READY_NO_SEND` or `ELITE_MATCH`, whose thresholds pass, whose blocker list is empty, and whose safety state remains NO-SEND.

## Safety invariants

```text
final_send_ready                 = FALSE
OUTBOUND                         = CLOSED
send_allowed                     = 0
irreversible external actions    = 0
canonical ID allocations         = 0
canonical ID reservations        = 0
authority advance                = FALSE
```

AAG-3.0 evaluates applications. It does not submit forms, send emails, allocate CRM authority IDs or reinterpret research evidence as hotel authority.
