# CONTEXT PACK PROTOCOL — CPP-2.0

Status: **V2 CANDIDATE CONTRACT**

A ContextPack is an acceleration and continuity artifact, never authority. It captures the minimum zero-context reconstruction state: ContextPack ID/timestamp, session identity, current main SHA, authority epoch and parent SHA-256, projection revision, event watermark, fencing token, state digest, contract versions, active barriers, active claims and next-safe actions.

## Freshness barrier

Immediately before any material mutation the pack is compared with live authority. Any mismatch in `main_sha`, `authority_parent_sha256`, `event_watermark` or `fencing_token` invalidates the pack and requires live reconstruction under MEP/WOP.

A newer ContextPack cannot override a stricter authority, evidence, privacy or outbound gate.

## Recovery target

A zero-context successor using stable contracts + current `STATE.md` + authority parent + ContextPack/event watermark + active claims must be able to determine the next safe action without chat memory.

## Prohibited

- treating ContextPack as canonical state;
- putting credentials/PII in a public pack;
- copying mutable source counts into stable contracts;
- using an old pack after main/authority/watermark/fence moves;
- overwriting concurrent shared progress without ancestry reconciliation.