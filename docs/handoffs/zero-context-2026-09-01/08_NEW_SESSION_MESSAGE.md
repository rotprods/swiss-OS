# MESSAGE TO PASTE INTO A NEW CHAT

I am continuing an existing production project called `SWITZERLAND_JOB_OS`.

Treat this conversation as zero-context. Do **not** rely on memory from any previous chat and do not ask me to restate information that should exist in durable project state.

Repository: `rotprods/swiss-OS`

Your first task is to recover the live system using the project’s durable continuity/authority artifacts. Start from the repo handoff bundle under:

`docs/handoffs/zero-context-2026-09-01/`

especially:

`06_ZERO_CONTEXT_METAPROMPT.md`

Execute that METAPROMPT fully.

Hard requirements:
- verify fresh Git main;
- validate CSP before continuation;
- reconstruct hotel/CRM authority separately from Git state;
- inspect open PRs/concurrent claims before mutating state;
- never treat staging/canary/open PR/chat as authority;
- keep `OUTBOUND=CLOSED` and `send_allowed=0` unless a later explicit authorized gate proves otherwise;
- continue the highest-value safe NEXT rather than merely summarizing.

At the end of the first turn, tell me:
- exact recovered authority;
- exact active checkpoint/NEXT;
- any divergence from the handoff;
- what you executed;
- what PR/artifacts you produced;
- exact next action.
