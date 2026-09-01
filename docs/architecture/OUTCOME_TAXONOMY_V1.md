# EMPLOYER RESPONSE / OUTCOME TAXONOMY V1

Status: W6 contract drafted during W1.

Canonical response outcomes:
- ACKNOWLEDGED
- NO_VACANCY
- REJECTED
- MORE_INFO
- INTERVIEW
- OFFER
- WITHDRAWN
- OTHER

## Evidence rule

`observed_reason` contains only what the employer explicitly communicated. `inferred_reason` is optional analytical hypothesis and must never overwrite observed truth.

Examples:
- “all relevant vacancies have been filled” -> NO_VACANCY; observed reason preserved.
- “other applicants meet our demands better” -> REJECTED; do not invent language/experience as reason.
- automated receipt only -> ACKNOWLEDGED, not positive response.
- request for interview times -> INTERVIEW.
- compensation/role terms proposed -> OFFER candidate, then offer verification gate.

## Learning dimensions

Aggregate only after linking to application, organization, niche, lane, asset versions, template schema and channel. Track response rate, positive-response rate, interview rate and offer rate. Do not call any rate a probability of hiring for an individual application.
