# Meta Execution handoff — Delta / Overlook entity granularity

Parent main: `a09f8cb722744c8e5c987a05278b8cd5192d9e11`  
Authority: `HS_ENTITY_EPOCH_2026-08-25_E4` / `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`  
Active claim: `CLAIM-CRM-SRR-SPECIAL-006`, fencing token 6  
Execution mode: `READ_ONLY_RESEARCH` / preauthority only

## Result

EGR-1.0 was introduced as a fail-closed entity-granularity rule: a parent/component or subproperty relationship is preserved as relationship metadata and is never sufficient by itself for identity collapse.

`Delta Resort Apartments` is typed `NEW_CANONICAL` preauthority while preserving `OPERATED_AS_SUBPROPERTY_OF -> H-0220 Parkhotel Delta Wellbeing Resort`. Current operator and tourism evidence expose it as its own accommodation product; no alias or terminal mapping is created.

`OVERLOOK Lodge by CERVO Mountain Resort` is typed `NEW_CANONICAL` preauthority while preserving `COMPONENT_OF_OR_OPERATED_WITHIN -> H-0012 CERVO Mountain Resort`. CERVO currently markets Overlook as five serviced flats 350m below the resort and separate from Nomad/Alpinist/Huntsman. Live CRM also contains `H-0201 Nomad Lodge by CERVO Mountain Resort` alongside parent `H-0012`, providing a canonical granularity consistency precedent without serving as sole proof.

```text
relationship/granularity reviewed       2 / 2
relationship/granularity unresolved         0
NEW_CANONICAL preauthority delta            2
cumulative NEW_CANONICAL preauthority      67
terminal mapping delta                      0
RECONCILE_REQUIRED                       1403
```

No H-ID was allocated/reserved. Authority remains E4/690. `OUTBOUND=CLOSED`, `send_allowed=0`.

## QA / adversarial checks

- shared operator/license/address does not imply same entity: PASS
- child/component relation is preserved rather than aliased: PASS
- live H-0012/H-0201/H-0220 comparator readback: PASS
- current first-party source evidence: PASS
- staging/canary/cache cannot advance authority: PASS
- H-0691 reservation/allocation: none
- terminal mapping conservation: 658
- irreversible external action: none

## NEXT

Compile the 47 ordinary lower49 current-public-distinctness reviews into a deterministic preauthority materialization workset, excluding the already-special `Neu-Schönstatt` terminal case and `Delta Resort Apartments` relationship-resolution case. The compiler/workset must preserve source-key lineage, evidence packet provenance, suggested comparators and stable batching; it must not itself create terminal mappings, H-ID reservations or authority effects.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**
