# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T03:56:00Z**. Parent main SHA: **`6c64f747dd7ec707d42a221c8c7e2eaa4ce9329f`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
ASR-1.0                         EXACT
HOTEL_INTELLIGENCE_V1           690 / 690
Graph HOTEL / INTEL / edges     690 / 690
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Authority parent SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`; authority workbook recovery SHA `434fab60a1260f08b647e9f6ed718575de195a11fc09177a4c42da84b66b920e`. ECV, staging, provider, cache and canary state are non-authoritative.

## CRM universe / mapping frontier

```text
source pages / records              172 / 2061
ACTIVE_MATCH / TRUE_MISSING          623 / 1438
effective terminal mappings         627
RECONCILE_REQUIRED                  1434
reverse authority/source gaps        66
source artifact                     9700376482
source ZIP SHA                      721f9ff9f84e2d5d9df62c6b22f12e7354cef3a298cb8990be66a202e1e769ce
candidate records                   1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
candidate gzip SHA                  8107499196092fe3a505ee54b64b26362ea3669380e3ee57754825f6acd5c95f
```

The full deterministic candidate export is durable at `docs/state/CRM_CANDIDATE_EXPORT_33206402141.json.gz`; CI reconstructs and validates all 1,438 ordered records from it. Drive recovery pointer sheet `1bQ74_WJlXFP6-nyGmkD97u-jgk6xhlz22j6t9H0e9sE` is explicitly non-authoritative. Local spreadsheet materialization degraded, so MEP used Git as the durable data plane rather than idling. Discover.swiss structured parity remains blocked by missing `DISCOVER_SWISS_SUBSCRIPTION_KEY`.

## Exact-current frontier — SUB0024 green

Actions `33232080824`, job `99046528179`, artifact `9708807620`, artifact ZIP SHA `56a21fe827881a3ea4a8ac860c7d73092d67eea4bbfc33a7c3746f23e6f62dce`; normalized ECV packet SHA `8685490197f0a580e6cfc69a03c71161eb66b5ee4775a7b82ddd4b373915fb79`; validator violations `0`.

ECV verified frontier             469 / 1438
ECV remaining never verified     969
ECV pending requeue                 0

SUB0024 is 20/20 `CURRENT_DETAIL_VERIFIED`, provider-record changes `0`. Exact-current evidence reserves/allocates no canonical ID and advances no authority.

## CWP lineage repair

Replay of the frozen source against E4 reproduced exactly `2061 / 623 / 1438` and proved that merged SUB0024 did **not** correspond to original candidate offsets `440..459`. Its actual source keys map to `440..452,454..460`: offset `453` was skipped while offset `460` was verified early.

```text
lineage hole offset                 453
lineage hole key                    MD-4ac3fbacbb0490ec9371
lineage hole entity                 Hotel Stern Chur | Chur
recovery batch                      SUB0024R1
recovery items                      1
recovery items SHA                  274a92b447ca1272dfbad5ffe214254aad3bb1be48c72f66b87e0e0225d933f6
next forward offset after repair    461
```

No verified evidence is discarded. SUB0024R1 stages only the skipped source record and remains non-authoritative.

## P0 / NEXT

Open P0s are `CWP_LINEAGE_HOLE_SUB0024_OFFSET_453` until SUB0024R1 verifies, `EFFECTIVE_RECONCILE_REQUIRED_1434_NOT_ZERO`, `REVERSE_AUTHORITY_SOURCE_DISCREPANCIES_66_REQUIRE_RESOLUTION`, and discover.swiss provider-key absence.

```text
merge lineage-repair meta-PR only after green repo-guard + adversarial review
→ observe auto SUB0024R1 ECV
→ validate/persist evidence with authority_advanced=false, h_id_allocations=0, OUTBOUND=CLOSED, send_allowed=0
→ if green, contiguous verified lineage reaches offset 460 and forward staging starts at 461
→ stage offsets 461..480 as SUB0025 from the durable candidate export
→ continue terminal entity-resolution + reverse-gap work
→ require full 2061 mapping replay, RECONCILE_REQUIRED=0, reverse gaps=0 and SSR-1.0 before any authoritative cross-plane reconciliation
```

Canonical recovery pointer: `docs/state/NEXT.json`. E4 remains `690/690/0`; `H-0691` remains unallocated.
