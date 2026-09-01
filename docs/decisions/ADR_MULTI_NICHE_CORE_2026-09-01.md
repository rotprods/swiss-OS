# ADR — Generalize SWITZERLAND_JOB_OS to multi-niche core

Date: 2026-09-01
Status: ACCEPTED FOR IMPLEMENTATION
Graph impact: PROJECT_MEMORY_META_GRAPH + future OPERATIONAL_GRAPH schema; no current authority mutation.

## Context

The system North Star is a viable Swiss job offer and relocation, while the most mature market implementation is hotel-specific. Treating hotels as the system boundary would optimize an infrastructure proxy rather than G-0001.

## Decision

Adopt one generic Swiss Employment Acquisition core with versioned niche adapters. Hotels become NICHE-001 and remain fully backward-compatible during migration.

Existing E4/690 hotel authority, canonical H-IDs, CP-0750 and current source/entity-resolution work remain intact. Generalization starts additively. No destructive rename/migration and no H-ID allocation occurs in this ADR.

Candidate assets, email identity, application compilation, response ingestion, interview, offer, financial viability and relocation are first-class core domains rather than hotel-specific appendices.

## Consequences

Positive:
- reusable across dozens/hundreds of Swiss employment niches;
- hotel investment is preserved;
- outcomes become comparable across niches/lanes/templates/channels;
- North Star becomes the organizing abstraction.

Costs/risks:
- schema migration complexity;
- compatibility burden;
- temptation to over-generalize before a second adapter proves the abstraction.

Mitigation:
- additive overlay;
- Hotels as golden compatibility fixture;
- NICHE-002 as abstraction test;
- no generic abstraction without demonstrated cross-niche responsibility;
- small PRs and invariant gates.

## Rejected alternatives

1. Finish all hotels before generalizing — rejected because hotel completion is not the North Star and delays candidate/acquisition learning.
2. Build independent systems per niche — rejected due to duplicated identity/evidence/application/governance logic.
3. Destructively replace hotel tables immediately — rejected due to authority/recovery risk.

## Implementation reference

See `docs/architecture/MULTI_NICHE_EMPLOYMENT_OS_V1.md`.
