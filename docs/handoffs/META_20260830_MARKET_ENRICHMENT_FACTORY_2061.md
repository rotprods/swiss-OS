# Meta Execution handoff — MEF-2061 bulk market enrichment

Parent main: `c71af36dbe303e98e25f12369793e6e24504ba4f`  
Frozen source: `HS-MEMBER-DE-33206402141` — 2061 records  
Source records SHA: `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`  
Execution mode: `READ_ONLY_RESEARCH`  
Canonical authority effect: `NONE`

## Why this exists

The project had over-serialized CRM evidence review even though market research does not require canonical H-ID promotion. MEF-2061 changes the execution topology: CRM closure remains Lane A, while vacancy, careers, housing, people, channel, scoring and application preparation run in parallel against immutable source `record_id`s.

## Deliverable

A 42-shard GitHub Actions factory over the complete 2061-record HotellerieSuisse manifest. Each record produces a public-evidence packet for E07/E08/E09/E10/E11/E12/E14/E15/E16/E17/E18/E19/E20/E21/E22 and one hotel-specific application seed.

The full per-hotel output is kept as an Actions artifact; only the aggregate summary/run receipt enters the public repository. Candidate-specific claims remain blocked behind the private Candidate Truth join.

## Post-merge execution

Merging the system-definition PR triggers `.github/workflows/market-enrichment-2061.yml` because the run-request file enters `main`. The workflow:

1. downloads source artifact `9700376482`;
2. verifies exact snapshot/count/hash;
3. executes 42 bounded shards with max six parallel workers;
4. aggregates only if record coverage is exactly 2061/2061;
5. uploads the full aggregate artifact;
6. opens a public-safe summary PR with vacancy/career/channel metrics and safety locks.

## Parallel CRM lane

Token6 CRM work continues independently with the 24 `RAGR IN_SCOPE_NO_SOURCE_MATCH` source-identity sweep. MEF-2061 cannot consume or reserve H-0691 and cannot create source mappings.

## Hard locks

`CRM_UNIVERSE_COMPLETE=false`; `OUTBOUND=CLOSED`; `send_allowed=0`; no H-ID allocation/reservation; no authority advance; no irreversible external action.

## NEXT

After the aggregate exists, download and validate it, persist a Drive recovery copy if the provider accepts the artifact reference, join private Candidate Truth to E17 seeds, rank vacancy-positive / careers-positive / spontaneous-application properties, and prepare complete application packets without sending them.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
