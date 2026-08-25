# Security and Data Handling

This repository is public. It contains system architecture and reproducible contracts, not operational/private datasets.

## Never commit

- SQLite or database dumps;
- `.env` files, credentials, API keys or tokens;
- CVs, passports, IDs, addresses, phone numbers or private candidate data;
- raw contact/person exports;
- raw evidence archives containing personal data;
- private Google Drive exports;
- private portfolio/media payloads;
- browser/session/auth artifacts.

## Allowed

- architecture;
- schemas without private records;
- migrations;
- validation code;
- synthetic test fixtures;
- public-safe manifests/checksums;
- runbooks and governance contracts;
- aggregate operational counters that do not expose private data.

## Operational storage

Live data belongs in the constrained operational database and authorized Google Drive/Sheets control plane. GitHub should receive only reproducible code/contracts and sanitized state pointers.

## Incident rule

If sensitive data is accidentally committed, treat history as compromised: revoke affected credentials immediately, remove the material from Git history, rotate secrets and record the incident.
