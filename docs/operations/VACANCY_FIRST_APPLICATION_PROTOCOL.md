# Vacancy-First Application Protocol — VFA-2.0 + AAG-3.0

Status: **CURRENT PROPOSED SYSTEM DEFINITION / NO-SEND**

Purpose: convert current hotel-market evidence plus private Candidate Truth into truthful, role-specific Swiss job application packets while learning from employer responses. This protocol never authorizes sending.

AAG-3.0 (`docs/operations/APPLICATION_ADVERSARIAL_GATE_V3.md`) is now a mandatory downstream readiness gate. The recruiter 10-second gate remains necessary but is no longer sufficient by itself.

## Why V2 exists

Wave 1 produced 10 Swiss hotel applications, 6 employer responses and 0 interviews. Private response evidence is stored outside the public repository. Public-safe learning is limited to aggregate behavior:

- exact vacancy/timing matters;
- generic spontaneous breadth is weaker than a named live role;
- operational fit must be legible before creative/digital differentiation;
- generic rejection or no reply cannot be converted into an invented language, education, permit or experience failure;
- a filled vacancy suppresses that vacancy, not the employer forever.

## Primary decision pipeline

```text
current market evidence
→ exact live vacancy
→ requirement extraction
→ Candidate Truth join (private)
→ lane-specific CV/assets
→ role-specific application packet
→ AAG-3.0: hard gates + 19D score + 100 questions + risk + 6 stakeholders
→ AAG READY/ELITE receipt
→ recruiter 10-second gate
→ factual/legal/deliverability QA
→ APPLICATION_READY_NO_SEND
→ explicit user authorization required for any later external action
```

A careers page without a current compatible vacancy is **not** a primary application target. Spontaneous applications are fallback research only unless a separate policy explicitly promotes them from current employer need evidence.

## Candidate lanes

- `HOUSEKEEPING`
- `SERVICE_FNB`
- `KITCHEN_SUPPORT`
- `OPERATIONS_GENERAL`
- `GUEST_SUPPORT`
- `HYBRID_DIGITAL`

Operational lanes use a lane-specific CV and do not attach the broad creative/digital portfolio by default. `HYBRID_DIGITAL` may attach a verified portfolio by default.

## Candidate Truth contract

Before a packet can be `APPLICATION_READY_NO_SEND`, private Candidate Truth must provide:

- role-relevant evidence;
- truthful language wording;
- exact/current availability wording;
- permanent-relocation intent;
- current Swiss work-eligibility wording;
- contact identity;
- approved real headshot if a headshot is rendered;
- verified real links if links are rendered;
- an AAG-3.0 receipt in `APPLICATION_READY_NO_SEND` or `ELITE_MATCH` state.

Founder/CEO/operator claims require evidence before external use. For operational applications, verified founder/operator history remains secondary to exact role fit.

## Motivation policy

Allowed: authentic positive reasons for building a permanent future in Switzerland, and specific evidence-grounded appreciation of the employer, property, destination or community.

Forbidden as persuasion tactics:

- political grievance or victimhood about Spain;
- fabricated praise;
- generic superlatives presented as personal psychology;
- invented employer facts;
- manipulative pressure.

The application should communicate long-term commitment, responsibility, contribution and motivation without requiring the recruiter to agree with a political narrative.

Permanent/indefinite relocation intent does **not** require an immediately permanent contract. A compatible seasonal role may be a valid first step toward a long-term Swiss career.

## Creative-value pilot

Professional photography, video, design, signage, content, ads, campaigns, web/digital work and automation may be offered as **secondary employer value**.

A recurring creative deliverable without a separate freelance fee is allowed only when:

1. the employer explicitly agrees;
2. it is inside lawful agreed employment scope/working time or another clear arrangement;
3. it is not an unconditional promise of unlimited/off-the-clock free labour.

Creative value never compensates for a failed hard requirement of the target job.

## Employer feedback taxonomy

Outcomes:

- `INTERVIEW`
- `INTEREST`
- `QUESTION`
- `REJECTION_FILLED`
- `REJECTION_NO_MATCHING_VACANCY`
- `REJECTION_COMPETITIVE_FIT`
- `REJECTION_INTERNAL_NEEDS`
- `REJECTION_REQUIREMENT`
- `REJECTION_GENERIC`
- `NO_REPLY`

Evidence classes:

- `EXPLICIT_EMPLOYER_REASON`
- `STRONG_INFERENCE`
- `WEAK_HYPOTHESIS`

Rules:

- generic rejection and no reply never infer a specific failed requirement;
- `REJECTION_FILLED` suppresses the exact vacancy only;
- `REJECTION_NO_MATCHING_VACANCY` penalizes an immediate spontaneous retry, not future exact roles;
- competitive/internal-fit feedback raises role-specificity pressure without inventing which requirement failed.

## AAG-3.0 adversarial gate

AAG evaluates the packet as ATS/recruiter, department head, HR, GM/CEO, Brand/PR and candidate long-term fit. It separates:

- `APPLICATION_QUALITY_SCORE`;
- `EVIDENCE_CONFIDENCE_SCORE`;
- `EMPLOYER_RISK_SCORE`;
- `HUMAN_RESONANCE_SCORE`;
- `DESPERATION_SCORE`;
- explicitly heuristic `CONFIDENCE_ADJUSTED_SCORE`.

Mandatory job requirements are non-compensable. A perfect creative portfolio or email cannot offset an unmet mandatory language, work-eligibility, experience, vacancy-freshness, duplicate/suppression or other hard gate.

AAG's full 100-question bank and readiness thresholds are defined only in the executable module `src/swiss_os/application_adversarial.py` and the AAG protocol; VFA does not maintain a duplicate question list.

## Recruiter 10-second gate

After AAG has passed, a packet still fails unless a recruiter can identify immediately:

- exact role;
- role-relevant evidence;
- languages;
- availability;
- permanent relocation intent;
- Swiss employment eligibility wording;
- valid contact identity;
- absence of known hard-requirement failure.

Unverified headshots, links or founder/CEO claims are hard failures when included.

The implementation also validates the AAG receipt. Missing AAG, LIMBO/WEAK/REJECT decisions, threshold mismatches, blockers, or outbound-safety drift fail closed.

## Email presentation

A polished HTML profile/signature is permitted only as static, lightweight enhancement. It requires a plain-text fallback and verified real assets.

Forbidden:

- JavaScript;
- iframes;
- forms/inputs;
- embedded active objects;
- hidden tracking pixels;
- fake interaction;
- unverified links/images.

Visual polish is downstream of role fit and deliverability. Any genuinely interactive experience belongs on an external verified recruiter landing/portfolio.

## Integration with the 2061 market factory

`src/swiss_os/market_enrichment.py` remains the canonical public-web research crawler. VFA consumes its aggregate through `src/swiss_os/application_wave.py` and does not create a second market crawler.

Public phase:

```text
market aggregate
→ compile_top_exact_vacancy_seeds(limit=25)
```

Current vacancy-detail phase:

```text
436 current opening-route hotels
→ Vacancy Detail Resolver
→ current role evidence / requirements / housing / channels
→ compile_top_resolved_vacancy_seeds(limit=25)
```

Private phase:

```text
selected seed
+ private Candidate Truth
+ role-relevant evidence
+ approved asset refs
→ AAG-3.0 evaluate_application()
→ persist private AAG receipt
→ compile_private_packet()
→ recruiter_10_second_gate()
```

Private PII and evidence must not be committed to the public repository.

## Hard locks

```text
final_send_ready = FALSE
OUTBOUND = CLOSED
send_allowed = 0
canonical ID allocations = 0
canonical ID reservations = 0
authority advance = FALSE
```

No operation in VFA-2.0 or AAG-3.0 sends an email or submits an application.
