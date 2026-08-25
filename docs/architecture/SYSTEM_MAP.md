# System Map

```text
                    ┌─────────────────────┐
                    │      G-0001         │
                    │ verified Swiss offer│
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
     Canonical Market     Candidate Truth     Intelligence OS
       G-0500               G-0600             G-0700/G-0800
           │                   │                   │
           └──────────────┬────┴──────────────┬────┘
                          │                   │
                    Governance / QA      Scheduler V2
                          │                   │
                          └────────┬──────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
            SQLite/DB          Sheets/Drive       Graph V2
          constrained truth    control plane      relationships
                │                  │                  │
                └──────────────────┼──────────────────┘
                                   │
                             GitHub contracts
```

## Current scale

- Canonical: 677
- Intelligence: 677
- Graph V2: 677
- L4 resolved: 105
- Target checkpoint: CP-0750
- Next canonical task: SV2-058

The graph and intelligence layers may enrich the current canonical set while canonical discovery continues toward the full frozen entity epoch.
