# ALIAS REPAIR REPLAY — SWITZERLAND_JOB_OS

Version: **ARR-1.0**  
Status: **FAIL-CLOSED RECOVERY TOOLING**

## Purpose

ARR-1.0 converts a proven semantic-alias corruption into a deterministic copy-on-write SQLite repair artifact. It exists for recovery/replay only; it does not itself advance authority.

## Hard preconditions

A repair plan must bind every affected alias to:

```text
alias_hotel_id
canonical_hotel_id
expected alias name + city
expected target name + city
restore_state
```

Execution additionally requires an exact parent SHA-256. Parent bytes are never modified in place.

The replay fails closed when:

- parent SHA differs;
- either physical hotel identity drifted;
- the persisted alias target differs from the plan;
- the superseded state differs from the expected target;
- the proposed removal would delete an alias whose alias/target name+city already represent the same identity;
- PK/FK/integrity preconditions fail;
- mutation cardinality differs from one expected state restore + one expected alias deletion per repair instruction.

## Invocation

```bash
python -m swiss_os.alias_repair \
  parent.sqlite \
  repair-plan.json \
  --out repaired.sqlite \
  --manifest repaired-manifest.json
```

Repair-plan shape:

```json
{
  "expected_parent_sha256": "<64 hex chars>",
  "instructions": [
    {
      "alias_hotel_id": "H-0001",
      "canonical_hotel_id": "H-0002",
      "expected_alias_name": "Physical alias-side identity",
      "expected_alias_city": "City A",
      "expected_target_name": "Physical target identity",
      "expected_target_city": "City B",
      "restore_state": "CANONICAL_CURRENT_RECONCILED"
    }
  ]
}
```

## Idempotency

Replaying from an already-repaired parent is allowed only when the alias edge is absent and the alias-side hotel is already in the requested restored state. The second replay performs zero logical mutations.

## Authority boundary

ARR output always reports:

```text
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

A repaired SQLite artifact becomes authority only inside a later WOP recovery wave after exact DB ↔ HOTELS_MASTER ↔ Intelligence ↔ Operational Graph ↔ observability reconciliation, rollback/replay validation, ASR-1.0 `EXACT`, and all applicable production gates.

For issue #89, ARR-1.0 is the portable reconstruction path for the V13 repair canary when a runtime cannot egress locally generated SQLite bytes.
