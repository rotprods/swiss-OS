# EMAIL IDENTITY OS V1

Status: W4 contract drafted during W1. No Gmail settings changed and no email sent.

## Identity layers

1. sender account
2. display name
3. reply identity
4. HTML signature
5. plain-text fallback
6. contact/link manifest
7. lane/message schema
8. render QA

## Signature design contract

Professional candidate identity, not an agency advertisement. Must remain useful with images blocked and in dark mode.

Permitted fields only when Candidate Canon confirms them:
- full professional name
- concise positioning line
- phone
- email
- LinkedIn
- portfolio/site
- Switzerland relocation positioning where approved

Do not expose private/internal IDs, tracking pixels or hidden analytics.

## HTML constraints

- email-safe table layout where necessary
- inline CSS only for critical presentation
- no JavaScript
- no external fonts required
- no tracking pixels
- accessible link text
- plain-text equivalent
- max-width/mobile-safe
- graceful dark-mode degradation

## Render gauntlet

Gmail web; Gmail mobile; Apple Mail; Outlook; images disabled; dark mode; plain-text. Verify link targets and copy/paste behavior.

## Message families

ENTRY, VACANCY_SPECIFIC_ENTRY, SPONTANEOUS, HYBRID, CREATIVE, RECRUITER, GROUP_LEVEL, PORTAL_SUPPORT, FOLLOWUP_1, FOLLOWUP_2, INTERVIEW_THANK_YOU, REACTIVATION.

Templates are schemas, not blind prose. Render requires exact organization/opportunity/channel/lane/claim/asset context.

## Installation boundary

A signature HTML artifact is not proof of Gmail installation. Real account mutation must use a supported Gmail/settings capability and be separately verified. Until then state is `ARTIFACT_READY_NOT_INSTALLED`.
