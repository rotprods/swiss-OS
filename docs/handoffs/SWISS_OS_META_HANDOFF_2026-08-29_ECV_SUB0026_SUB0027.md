# SWISS_OS META HANDOFF — SUB0026 → SUB0027

Parent main `216481c7993198daef4585fb90b9acbc9bfeeefc`; authority epoch `HS_ENTITY_EPOCH_2026-08-25_E4`.

SUB0026 ECV is green: run/job `33234983579 / 99054272445`, artifact `9709651108`, ZIP SHA `1e47cd331c265024cd243d3b4b33bbb49a7d835e914d9926fb8fa0f784957963`, normalized packet SHA `a39cebfd453df089e4a42c1f7d93b613c8ef14240f72fb64c4571e21e9f5a539`; 20/20 `CURRENT_DETAIL_VERIFIED`, zero provider changes, zero validator violations. Unique ECV frontier = **510/1438**; remaining never verified = **928**; contiguous original-candidate prefix = **0..500**.

SUB0027 stages exact original candidate offsets **501..520**. Adversarial CI on PR #150 caught `STAGED_ITEMS_SHA_MISMATCH`; the candidate selection/order was unchanged and the deterministic canonical items hash was repaired to `f92f07e9d2753f9bf0b2d21965e05678c2633dfdf9029b09c332bb4428b2b5dd`. Next untouched offset **521**.

Authority remains E4 `690/690/0`; `H-0691` remains unallocated. P0s remain `RECONCILE_REQUIRED=1434`, 66 reverse gaps and missing discover.swiss key. NEXT: green post-repair CI → merge PR #150 → auto SUB0027 ECV → chain SUB0028 if safe. OUTBOUND=CLOSED; send_allowed=0.
