# SWISS_OS META HANDOFF — SUB0024 lineage repair → SUB0024R1

Parent main `6c64f747dd7ec707d42a221c8c7e2eaa4ce9329f`; authority epoch `HS_ENTITY_EPOCH_2026-08-25_E4`.

SUB0024 live ECV is green: Actions/job `33232080824 / 99046528179`, artifact `9708807620`, ZIP SHA `56a21fe827881a3ea4a8ac860c7d73092d67eea4bbfc33a7c3746f23e6f62dce`, normalized packet SHA `8685490197f0a580e6cfc69a03c71161eb66b5ee4775a7b82ddd4b373915fb79`, 20/20 `CURRENT_DETAIL_VERIFIED`, provider changes `0`, validator violations `0`. Unique ECV frontier is `469/1438`; remaining never verified `969`.

Deterministic replay of frozen source artifact `9700376482` against E4 reproduced exactly `2061` source records, `623` exact name+city matches and `1438` pre-authority candidates. This exposed a staging lineage defect: merged SUB0024 keys map to original candidate offsets `440..452,454..460`, not `440..459`. Original offset `453`, `MD-4ac3fbacbb0490ec9371` / `Hotel Stern Chur` / `Chur`, was skipped. Offset `460` was verified early and remains valid evidence.

Recovery is bounded: `SUB0024R1` contains only offset `453`, one item, SHA `274a92b447ca1272dfbad5ffe214254aad3bb1be48c72f66b87e0e0225d933f6`. It allocates/reserves no H-ID and cannot advance authority. After a green recovery result, forward staging starts at original candidate offset `461` and SUB0025 must cover `461..480` from the durable candidate export.

Full deterministic candidate export is persisted as `docs/state/CRM_CANDIDATE_EXPORT_33206402141.json.gz`, gzip SHA `8107499196092fe3a505ee54b64b26362ea3669380e3ee57754825f6acd5c95f`, records SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`. Drive recovery pointer sheet: `1bQ74_WJlXFP6-nyGmkD97u-jgk6xhlz22j6t9H0e9sE`; it is non-authoritative. Local spreadsheet artifact materialization degraded, so MEP used Git as the durable data plane.

Hard locks: E4 remains `690/690/0`; `H-0691` unallocated; `authority_advance_allowed=false`; `canonical_id_allocation_allowed=false`; `OUTBOUND=CLOSED`; `send_allowed=0`.

Open P0s after the lineage repair PR is staged: `CWP_LINEAGE_HOLE_SUB0024_OFFSET_453`, `EFFECTIVE_RECONCILE_REQUIRED_1434_NOT_ZERO`, `REVERSE_AUTHORITY_SOURCE_DISCREPANCIES_66_REQUIRE_RESOLUTION`, and missing `DISCOVER_SWISS_SUBSCRIPTION_KEY`.

NEXT: require green repo-guard + adversarial PR review → merge → observe automatic SUB0024R1 ECV → persist its evidence → if terminal/green stage SUB0025 offsets `461..480` and continue. Authority remains ineligible until full 2061 mapping replay has `RECONCILE_REQUIRED=0`, reverse gaps `0`, SSR-1.0 and fresh cross-plane reconciliation.
