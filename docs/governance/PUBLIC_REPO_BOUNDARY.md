# Public Repository Boundary

Because `rotprods/swiss-OS` is public, the migration is **semantic and architectural**, not a byte-for-byte Drive dump.

## Commit

- goals;
- rules;
- agent contracts;
- architecture;
- schemas and migrations;
- deterministic validators/tests;
- sanitized manifests;
- public-safe aggregate state.

## Do not commit

- operational hotel/person/channel/evidence rows as bulk dumps;
- candidate private data;
- credentials;
- SQLite binaries;
- Drive exports containing private or operational data.

This boundary is part of the system design, not an incomplete migration.
