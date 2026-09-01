# CANDIDATE ASSET OS V2

Status: W3 contract drafted during W1; no candidate claims changed.

## Asset lineage

Candidate Canon -> Claims Ledger -> Asset Manifest -> Renderer -> Extracted-text QA -> Lane Gate -> Approved Asset Version.

Required assets:
- CV_MASTER_V2
- CV_ENTRY_V2
- CV_HYBRID_V2
- CV_CREATIVE_V2
- optional portfolio/case-study assets only where lane requires them

## Claim classes

- VERIFIED_FACT: directly supported candidate fact.
- VERIFIED_CAPABILITY: supported by evidence/work artifact.
- SAFE_WORDING: truthful wording that does not imply unsupported qualification.
- PROHIBITED_UNVERIFIED: CEFR level, degree, employer, metric, equipment, availability or other fact lacking durable support.

Every externally rendered claim must resolve to an allowed claim ID/version.

## Lane gates

ENTRY: email, phone, CV, language wording, availability.
HYBRID: ENTRY + LinkedIn + portfolio + case-study evidence.
CREATIVE: ENTRY + LinkedIn + portfolio + case-study evidence.
PORTAL: email, phone, CV, language wording, availability; additional assets contextual.

## CV QA

- 1-2 pages unless a justified role-specific exception exists
- selectable/extractable text
- ATS-safe hierarchy
- no text embedded only in images
- consistent dates and contact identity
- no invented CEFR/degree/title
- role/lane-specific top third
- file metadata/version/hash
- PDF text extraction equals intended critical facts
- link validation

## Selection policy

Application compiler selects the narrowest truthful asset matching lane and vacancy. Creative capability must not obscure ENTRY positioning; ENTRY must not erase relevant capability when an employer explicitly values it.
