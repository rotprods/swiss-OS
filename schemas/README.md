# Schemas

Schema definitions should move here as executable contracts when implementation begins.

Primary domains:

- canonical hotel/entity identity;
- groups/operators;
- vacancies;
- people;
- channels;
- housing/benefits;
- evidence + Search Proof;
- QA V3;
- scoring V3;
- scheduler V2;
- graph nodes/edges;
- candidate claims/assets;
- personalization/message render keys;
- state transitions and observability.

Rules:

1. immutable canonical IDs;
2. declared schema versions;
3. migrations for breaking changes;
4. constrained DB enforcement where possible;
5. Sheets mirrors do not weaken DB semantics.
