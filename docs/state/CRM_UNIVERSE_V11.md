# CRM UNIVERSE — V11 PUBLIC-SAFE HANDOFF

Date: **2026-08-28**  
Wave: `WAVE-20260828-CRM-UNIVERSE-03`  
Mode: `READ_ONLY_RESEARCH → DEGRADED_CANARY`  
Authority mutation: **NONE**

## Objective

Continue mass discovery and anti-join toward 100% frozen HotellerieSuisse CRM mapping before outbound eligibility is evaluated.

## Authority unchanged

```text
E4 active canonical    686
physical lineage       690
superseded aliases       4
CRM_UNIVERSE_COMPLETE FALSE
OUTBOUND              CLOSED
send_allowed            0
```

## v11 staging metrics

```text
reference pages                          171
pages with historical/cache evidence      57
pages pending refresh                    114
cache observations                       629
historical missing identities staged     182
CRM import/staging queue                 248
V16 exact-detail canary                   25
reserve/no-ID                              7
snapshot conflict records                  4
normalized name+city import duplicates     0
H-ID reservations from staging             0
formula errors                             0
```

Artifact:

`CRM_UNIVERSE_STAGING_2026-08-28_v11.xlsx`

SHA-256:

`97486f7e4ae176f447ab8b57ab5ec199cdf3eb5bba556dfb8569235a87f482a1`

Drive file:

`external-gdrive:file:1kqKPZtWziaERbYbHbBBjPaFAbI_wGD-S`

## v11 harvest

Only member-directory pages actually returned by the indexed official HotellerieSuisse surface were ingested. Unrelated results, filtered sub-universes and the broader Branchenverzeichnis were rejected.

New page slices:

```text
page 94  DE  cached 2067 / 173  12 observations  8 true missing  4 overlap
page 145 FR  cached 2060 / 172  12 observations  0 true missing 12 overlap
```

Page 145's complete overlap is retained as useful anti-join evidence but does not count as current snapshot completion.

## Invariants

```text
historical cache → discovery only
no H-ID allocation at crawl/staging time
V16/current exact reserve > historical cache staging
normalized name+city import duplicates = 0
formula errors = 0
canary/cache counts never advance canonical authority
```

## Source-snapshot caution

The indexed root currently exposes a cached 2050/171 DE view while the FR root exposes 2052/171; older cached pages expose larger totals and shifted pagination. The same page number may therefore refer to different record slices across locale/cache epochs.

Final completion remains based on one explicit frozen snapshot plus source-record mapping, not on collecting every historical page cache.

## Next

Continue finding valid pending member-directory pages and prioritize any page surfaces belonging to the 2050/171 reference epoch. In parallel, prepare exact-current refresh of true missing identities. When the native HOTELS_MASTER writer is restored, perform `/wave recover` and the full authority transaction before allocating any new canonical IDs.
