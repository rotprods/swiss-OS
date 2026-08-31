# AAG-3.1 — Application Adversarial Gate

Status: **CURRENT PROPOSED SYSTEM DEFINITION / NO-SEND**

AAG-3.1 preserves the 100-point / 100-question / six-stakeholder AAG-3.0 foundation and adds five non-compensable vacancy-provenance hard gates discovered by the live 436-hotel Vacancy Detail recovery.

## Why 3.1 exists

The recovered 436/436 research aggregate proved that a high-quality role-looking signal is not sufficient evidence of an application target. Real escaped cases included:

- one shared group vacancy URL multiplied across several hotel records without property-level ownership proof;
- restaurant/venue/navigation labels interpreted as roles;
- department/program buckets interpreted as exact vacancies;
- structured JobPosting data with contradictory future `datePosted` and expired `validThrough` values;
- page headings that could otherwise bypass a structured temporal conflict.

Therefore `vacancy_current=true` is necessary but no longer sufficient.

## Sixteen hard gates

AAG-3.1 requires all eleven AAG-3.0 gates plus:

```text
vacancy_semantic_validity_verified = TRUE
vacancy_temporal_validity_verified = TRUE
employer_scope_verified = TRUE
mandatory_requirements_extracted = TRUE
application_route_verified = TRUE
```

A false value is terminal `REJECT`. An unknown value prevents readiness and normally produces `LIMBO`. No quality, portfolio, motivation or creative-value score can compensate.

## Versioned pipeline

```text
436/436 Vacancy Detail evidence
→ Application Wave 3.1 signal-quality + owner-scope quarantine
→ Application Wave 3.2 AAG-3.1-bound shortlist
→ current first-party requirement + employer/property + route recheck
→ private Candidate Truth + lane assets
→ AAG-3.1
→ Private Packet 3.1
→ recruiter 10-second gate
→ APPLICATION_READY_NO_SEND / ELITE_MATCH
```

A V3.2 seed requires an AAG-3.1 receipt. AAG-3.0 receipts are intentionally rejected by the V3.1 private recruiter gate. Historical V2/V3.1 artifacts remain replayable but are not upgraded silently.

## Readiness remains NO-SEND

All previous AAG thresholds still apply. In addition, every AAG-3.1 provenance hard gate must be terminal PASS.

```text
final_send_ready = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

No AAG decision authorizes external action. Explicit outbound authorization remains a separate system boundary.
