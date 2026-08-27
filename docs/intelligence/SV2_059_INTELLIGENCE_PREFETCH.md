# SV2-059 Intelligence Prefetch — Public-Safe Staging

Status: **STAGING ONLY — NON-AUTHORITATIVE**  
Canonical authority remains E4 / 686 active entities.  
Outbound remains CLOSED and `send_allowed = 0`.

This prefetch is keyed to the current local Batch05 canary allocation `H-0691..H-0703`. Those IDs are provisional until the live Drive/Sheets authority plane is re-read and the batch is re-anti-joined. If an intervening canonical commit has consumed any ID, reallocate before promotion.

## Purpose

Reduce the amount of blind L1 work after a future synchronized canonical commit without inflating L4/L9 progress now. Research below distinguishes direct recruitment routes, general contact routes, brand-level routes and unresolved states.

## Signals resolved

### H-0691 — Hotel City Inn, Basel

- current operator/group relationship resolved to Manz Privacy Hotels / Euler AG
- general hotel contact exists
- dedicated property recruitment route not resolved in this pass
- state: `GROUP_OPERATOR_RESOLVED_RECRUITMENT_PENDING`

General contact must not be promoted to recruitment without explicit evidence.

### H-0692 — Hotel City Zürich, Zürich

- official policy material explicitly contemplates spontaneous applications and applications to a specific position
- application policy therefore exists
- exact recruitment endpoint/person remains unresolved
- state: `APPLICATION_POLICY_CONFIRMED_ROUTE_NOT_FULLY_RESOLVED`

### H-0693 — Hotel City Lugano - Hospitality & design, Lugano

- official current property/contact surface resolved
- only general contact route resolved in this pass
- careers/vacancy route remains `SEARCH_PENDING`

### H-0694 — Hotel Continental, Zermatt

- current operation and relationship to Zermatt Hospitality Group corroborated through official hotel/group surfaces
- careers/vacancy route remains `SEARCH_PENDING`
- group identity does not by itself imply a shared recruiting route

### H-0695 — Hotel Crowne Plaza, Zürich

- current IHG/Crowne Plaza brand career infrastructure exists
- no exact Zürich-property recruitment endpoint was resolved in this pass
- state: `BRAND_CAREERS_ROUTE_FOUND_PROPERTY_ROUTE_PENDING`

A global brand portal must not be mislabeled as a property-specific application route.

### H-0696 — Hotel Crusch Alba, Zernez

- identity exact-detail canary resolved
- careers/vacancy/person/channel dimensions remain `SEARCH_PENDING`

### H-0697 — Hotel Crusch Alva, Zuoz

- identity exact-detail canary resolved
- careers/vacancy/person/channel dimensions remain `SEARCH_PENDING`

### H-0698 — Hotel Crystal, Interlaken

- current official general inquiry route resolved
- no recruitment-specific route resolved in this pass
- state: `GENERAL_CONTACT_ONLY_RECRUITMENT_PENDING`

### H-0699 — Hotel Crystal, St. Moritz

Strongest Batch05 intelligence signal so far:

- current official careers page resolved
- official open-positions section resolved
- direct personnel/application route resolved
- state: `CURRENT_CAREERS_ROUTE_FOUND`
- vacancy state: `CURRENT_OPEN_POSITIONS_SECTION_FOUND`
- application state: `DIRECT_PERSONNEL_ROUTE_FOUND`

This is a strong L4 input, but **does not itself earn L4** because housing/person/channel/search-proof completeness must still satisfy the level contract.

### H-0700 — Hotel Crystal Engelberg, Engelberg

- identity exact-detail canary resolved
- careers/vacancy/person/channel dimensions remain `SEARCH_PENDING`

### H-0701 — Hôtel d'Allèves, Genève

- current official property and general contact surface resolved
- no recruitment-specific route resolved in this pass
- state: `GENERAL_CONTACT_ONLY_RECRUITMENT_PENDING`

### H-0702 — Hotel Daniela, Zermatt

- operator/group relationship resolved to The Sisters Zermatt / Hotel Daniela AG
- group/general contact exists
- no explicit recruitment route resolved in this pass
- state: `GROUP_OPERATOR_RESOLVED_RECRUITMENT_PENDING`

### H-0703 — Hotel David 22, St. Gallen

- current official property/general contact surface resolved
- no recruitment-specific route resolved in this pass
- state: `GENERAL_CONTACT_ONLY_RECRUITMENT_PENDING`

## Prefetch summary

```text
Batch05 identities researched                    13
current direct property careers routes found      1
brand/application-policy signals                  2
operator/group relationships additionally resolved 3
L4 promotions                                     0
L9 promotions                                     0
external actions                                  0
send_allowed                                      0
```

## Hard rules preserved

1. General email/contact form ≠ recruitment route.
2. Group ownership ≠ shared recruiting scope unless explicitly evidenced.
3. Brand career portal ≠ property-specific vacancy/application route.
4. “No route found” remains `SEARCH_PENDING` unless a complete Search Proof earns a typed unknown.
5. A direct careers route does not automatically earn L4; all required core dimensions still need resolution/evidence.
6. This document is staging memory only and never advances canonical/Intelligence/Graph/checkpoint counters.
