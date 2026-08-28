# UNIFIED CLI — SWITZERLAND_JOB_OS

Version: **UCLI-2.0**  
Status: **CANONICAL OPERATOR ROUTER**

## Objective

Expose the executable OS through one backwards-compatible command surface without rewriting or destabilizing the legacy CLI.

Canonical source-tree invocation:

```bash
PYTHONPATH=src python -m swiss_os <command> [options]
```

The router preserves every legacy command and adds the activation/acquisition stack.

## Legacy commands preserved

```text
manifest
db
crm-universe
crm-snapshot
discover-swiss
crm-ingest
crm-scope
```

These are forwarded unchanged to the legacy `swiss_os.cli` implementation.

## Meta execution commands

```bash
python -m swiss_os meta-run validate-next NEXT.json

python -m swiss_os meta-run select-route \
  config/meta_execution_routes.json \
  capabilities.json \
  --blockers blockers.json
```

## Member-directory commands

```bash
python -m swiss_os member-directory capture \
  --root-url <official directory root> \
  --locale de \
  --out-dir private/captures/current-de

python -m swiss_os member-directory build records.json \
  --snapshot-id <id> \
  --observed-at <ISO8601> \
  --locale de \
  --source-url <root> \
  --source-epoch <epoch> \
  --expected-partitions <n> \
  --declared-raw-records <n> \
  --coverage-complete \
  --out manifest.json

python -m swiss_os member-directory validate manifest.json
```

## Staging evidence command

```bash
python -m swiss_os staging-evidence extract-workbook \
  CRM_UNIVERSE_STAGING_LATEST.xlsx \
  --out-dir private/mdm-cohorts \
  --observed-at <ISO8601> \
  --v16-epoch <epoch>
```

## Directory → CMI command

```bash
python -m swiss_os directory-export \
  MEMBER_DIRECTORY_MANIFEST.json \
  --records-out CRM_INGEST_RECORDS.json \
  --attestation-out DIRECTORY_TO_CMI_ATTESTATION.json
```

## Safety

The router does not create additional authority.

All delegated contracts preserve:

```text
staging/capture/export authority_advanced = false
staging/capture/export H_ID_ALLOCATIONS = 0
CRM_UNIVERSE_COMPLETE remains independently gated
OUTBOUND = CLOSED
send_allowed = 0
```

Unknown commands fail closed. `outbound-open` is deliberately not a command.

## Packaging note

`python -m swiss_os` is the canonical unified source-tree entrypoint. The existing installed `swiss-os` console script remains backwards-compatible with the legacy command surface until packaging metadata is migrated in a separately tested release; the executable protocols are already available through the module entrypoint.
