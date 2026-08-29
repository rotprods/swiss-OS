# SWISS_OS META HANDOFF — SUB0024R1 → SUB0025

Parent main `29812585f14b0793e9c65ac9dd1f6d20b1aaa4e0`; authority epoch `HS_ENTITY_EPOCH_2026-08-25_E4`.

SUB0024R1 ECV is green: run/job `33234381770 / 99052661724`, artifact `9709457433`, ZIP SHA `d58dae872067d9c76dafdfc72f83fb27f4cbb714395def56a6cdee695fda407e`, 1/1 `CURRENT_DETAIL_VERIFIED`, zero provider changes and zero validation violations. It closes the original candidate offset 453 lineage hole (`MD-4ac3fbacbb0490ec9371`, Hotel Stern Chur | Chur). Unique evidence frontier = **470/1438**; remaining never verified = **968**; contiguous candidate prefix is now **0..460**.

SUB0025 stages original candidate offsets **461..480**, items SHA `15daa56019f9e6017a56338de32a088c33e82b534d41f62783d9edafca2319af`; next untouched offset **481**.

Live Drive authority was re-read: HOTELS_V2 has exactly 690 H-ID rows H-0001..H-0690, no `SUPERSEDED_DUPLICATE`, and no H-0691. Authority remains E4 690/690/0; H-0691 unallocated. P0s remain 1434 unresolved source mappings, 66 reverse gaps, discover.swiss structured parity blocked by `DISCOVER_SWISS_SUBSCRIPTION_KEY`. NEXT: merge only after green CI + adversarial review; observe SUB0025 ECV; persist it; stage offsets 481..500 as SUB0026 if safe. OUTBOUND=CLOSED; send_allowed=0; no canonical ID reservation/allocation and no authority advance from ECV/cache/canary.
