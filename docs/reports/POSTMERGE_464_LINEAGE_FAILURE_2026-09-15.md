# PR #464 post-merge qualification failure

Observed 2026-09-15 after merge commit `e1f2fcb7487cbec8aced0e8cfb37cd26f2a5e06a`.

`repo-guard` push run `34959545311` failed at Material Mutation Lineage Guard with:

`MATERIAL_CHANGE_REQUIRES_ONE_ACTIVE_OR_TERMINALIZED_CLAIM:2`

Pre-merge exact-head run `34948226000` was PASS. The merge commit changes branch context to `main`; terminal lineage selection therefore no longer has the PR head branch name available and sees two terminal candidates. All later gates were skipped, so post-merge qualification is NOT complete.

Safety: no hotel/CRM/H-ID/candidate/outbound authority was granted by #464; E4/690 and OUTBOUND=CLOSED remain the intended locks.

Required next action: repair the merge-commit terminal-lineage semantics under a new globally leased claim/session, add a regression reproducing PR-head PASS -> merge-main FAIL, rerun exact-main full gauntlet, and only then close convergence/issue #54. Do not open B12 meanwhile.
