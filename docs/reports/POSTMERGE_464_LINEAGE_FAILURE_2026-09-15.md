# PR #464 post-merge qualification failure

Observed 2026-09-15 after merge `e1f2fcb7487cbec8aced0e8cfb37cd26f2a5e06a`.

Push `repo-guard` run `34959545311` FAILED at Material Mutation Lineage Guard:
`MATERIAL_CHANGE_REQUIRES_ONE_ACTIVE_OR_TERMINALIZED_CLAIM:2`.

Pre-merge exact-head `34948226000` was PASS. On the merge commit the branch context becomes `main`; terminal lineage selection can no longer use the PR head branch and sees two terminal candidates. Later gates were SKIPPED, so post-merge qualification is NOT complete.

Safety remains fail-closed: no hotel/CRM/H-ID/candidate/outbound authority was granted; E4/690 and OUTBOUND=CLOSED remain locks.

Next: repair merge-commit terminal-lineage semantics under a new globally leased claim/session; add regression PR-head PASS -> merge-main FAIL; rerun exact-main full gauntlet; only then close convergence/#54. Do not open B12 meanwhile.
