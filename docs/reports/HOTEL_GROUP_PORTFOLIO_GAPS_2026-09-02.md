# Hotel Groups / Multi-property Operators — graph gap research

Status: **RESEARCH_ONLY / NON-AUTHORITATIVE**  
Project: `SWITZERLAND_JOB_OS`  
Observed main base: `38ba0e31594f7f794eae3a283c87ed21f933ebfb`  
Authority observed read-only: E4 / 690 canonical / `H-0691_UNALLOCATED`  
Drive surfaces read-only: `HOTELS_V2`, `HOTEL_GROUPS_V2`  
Authority effect: **NONE**  
Drive writes: **0**  
Outbound: **CLOSED**

## Objective

Turn group/brand/portfolio evidence discovered during B07/B08 into typed graph candidates without collapsing distinct physical properties or treating every affiliation as an operator relationship.

Current `HOTEL_GROUPS_V2` exact-text searches returned no group rows for:

- Accor / Mövenpick;
- La Rocca Living Hotel Group;
- LUVITA Hotels & Spa AG;
- Swiss Quality Hotels;
- VCH Hotels Schweiz;
- Los Lorentes.

Absence here means **no exact current group node found by these names**, not proof that no semantically equivalent row exists under an unrelated name.

## Canonical relationship vocabulary proposed

Do not overload `ALIAS` or a generic `MEMBER_OF` edge.

- `OPERATED_BY`: legal/operational hotel operator controls the property.
- `BRANDED_BY`: property operates under a hotel brand/chain.
- `MARKETING_NETWORK_MEMBER_OF`: independent property participates in a booking/marketing cooperative or affiliation network.
- `ASSOCIATION_MEMBER_OF`: hotel belongs to an association; does not imply operator control.
- `PORTFOLIO_COMPONENT_OF`: accommodation product/property belongs to one commercial portfolio.
- `SHARED_RECEPTION_WITH`: separately addressable components share a reception/front desk.
- `SIBLING_PROPERTY_OF`: two distinct physical properties share operator/brand/group.
- `SHARED_RECRUITING_ROUTE_WITH`: only when current hiring evidence proves a shared application/HR route.

A group-level duplicate outreach lock must **not** be inferred from brand/association membership alone.

## G-01 — La Rocca Living Hotel Group

Classification: `HOTEL_GROUP_OPERATOR`  
Confidence: high / first-party

First-party Hotel Nessi evidence states that Hotel Nessi is part of **La Rocca Living Hotel Group**, identifies Marcel Krähenmann as General Manager of the group, and lists other facilities:

- Hotel Nessi — Locarno;
- Boutique Hotel La Rocca**** — Ronco sopra Ascona;
- Parkhotel Emmaus — Losone;
- Ristorante panoramico — non-hotel portfolio component.

The Hotel Nessi history states that the group was created after acquisition of Hotel Nessi and identifies Krähenmann as owner of Boutique-Hotel La Rocca and director of Parkhotel Emmaus.

Sources:
- https://www.hotelnessi.ch/en/hotel/team
- https://www.hotelnessi.ch/en/hotel

Current E4 exact-name search found no `La Rocca` property row and no current `HOTEL_GROUPS_V2` row named La Rocca Living Hotel Group.

Proposed edges:

```text
Hotel Nessi              ──OPERATED_BY──────────────► La Rocca Living Hotel Group
Boutique Hotel La Rocca  ──OPERATED_BY──────────────► La Rocca Living Hotel Group
Parkhotel Emmaus         ──OPERATED_BY──────────────► La Rocca Living Hotel Group
Ristorante panoramico    ──PORTFOLIO_COMPONENT_OF───► La Rocca Living Hotel Group
```

Do not create H-IDs for missing portfolio components from this research packet.

## G-02 — LUVITA Hotels & Spa AG

Classification: `HOTEL_GROUP_OPERATOR / LEGAL_OPERATOR`  
Confidence: high / first-party legal imprints

Both BEATUS and ERMITAGE official imprints identify the same company:

`LUVITA Hotels & Spa AG`, Innerdorfstrasse 12, 3658 Merligen.

Sources:
- https://www.beatus.ch/en/impressum
- https://www.ermitage.ch/en/impressum

Properties evidenced:

- BEATUS Wellness- & Spa-Hotel — Merligen;
- ERMITAGE Wellness- & Spa-Hôtel — Gstaad-Schönried.

Current E4 exact-name searches found neither `BEATUS` nor `ERMITAGE`, and `HOTEL_GROUPS_V2` has no exact `LUVITA` group row.

Proposed edges:

```text
BEATUS Wellness- & Spa-Hotel    ──OPERATED_BY────► LUVITA Hotels & Spa AG
ERMITAGE Wellness- & Spa-Hôtel ──OPERATED_BY────► LUVITA Hotels & Spa AG
BEATUS                          ──SIBLING_PROPERTY_OF──► ERMITAGE
```

A shared recruiting route must be researched separately before enabling group-level application dedupe.

## G-03 — Accor / Mövenpick

Classification: `HOTEL_CHAIN_BRAND` with parent hospitality group context  
Confidence: high / first-party Accor hotel surfaces

Current official Accor pages independently list:

- Mövenpick Hotel Geneva — 350 rooms, airport property;
- Mövenpick Hotel Lausanne — lakeside Lausanne property.

Sources:
- https://all.accor.com/hotel/B4G7/index.en.shtml
- https://all.accor.com/hotel/B4H5/index.en.shtml

E4 already contains `H-0614 Mövenpick Hotel Lausanne`. B07 independently identified Mövenpick Genève as a distinct current property, not an alias of H-0614.

`HOTEL_GROUPS_V2` currently has no exact Accor/Mövenpick row.

Proposed relations:

```text
Mövenpick Hotel Geneva   ──BRANDED_BY────────► Mövenpick
Mövenpick Hotel Lausanne ──BRANDED_BY────────► Mövenpick
Mövenpick                ──BRAND_OF───────────► Accor
Geneva                    ──SIBLING_PROPERTY_OF──► Lausanne
```

Do not infer shared HR/application routing merely from the Accor/Mövenpick brand.

## G-04 — Swiss Quality Hotels Genossenschaft

Classification: `BOOKING / MARKETING COOPERATIVE`, not property operator  
Confidence: high for Hotel Herisau affiliation; operator semantics intentionally rejected

Hotel Herisau's own privacy policy names **Swiss Quality Hotels Genossenschaft** as a booking/platform counterparty. Swiss tourism membership sources separately list Swiss Quality Hotels Genossenschaft as an organization.

Sources:
- https://hotelherisau.ch/en/privacy-policy/
- https://www.stv-fst.ch/verband/mitgliedschaft/mitgliederverzeichnis

B08 source record is named `Herisau Swiss Quality Hotel`, and several existing E4 property names also contain the `Swiss Quality` descriptor. That lexical/booking affiliation must never be treated as same-property identity.

`HOTEL_GROUPS_V2` currently has no exact Swiss Quality row.

Proposed semantics:

```text
Hotel Herisau ──MARKETING_NETWORK_MEMBER_OF──► Swiss Quality Hotels Genossenschaft
```

Other member edges require current per-property evidence or a current authoritative member list before materialization.

No automatic duplicate-outreach lock: cooperative membership does not prove centralized HR.

## G-05 — VCH Hotels Schweiz

Classification: `HOTEL_ASSOCIATION / AFFILIATION_NETWORK`, not operator  
Confidence: high / first-party association

VCH describes itself as `Verband Christlicher Hotels` and currently lists Parkhotel Gunten among its hotels/accommodations.

Sources:
- https://www.vch.ch/en/
- https://www.vch.ch/hotel/gunten-parkhotel

`HOTEL_GROUPS_V2` has no exact VCH row.

Correct edge:

```text
Parkhotel Gunten ──ASSOCIATION_MEMBER_OF──► VCH Hotels Schweiz
```

Incorrect edges that must be rejected:

```text
Parkhotel Gunten ──OPERATED_BY──► VCH      # unsupported
Parkhotel Gunten ──ALIAS_OF─────► VCH      # semantically wrong
```

VCH membership does not itself justify group-level recruiting dedupe.

## G-06 — Los Lorentes

Classification: `MULTI_PROPERTY / MULTI_FORMAT ACCOMMODATION PORTFOLIO`  
Confidence: high / first-party

Official Los Lorentes surfaces expose locations in:

- Bulle;
- Bern;
- Bern Airport.

The Bulle surface explicitly combines **Los Lorentes Residences + Hôtel du Cheval Blanc**, offers hotel rooms plus furnished studios/apartments at several addresses, and states that the main reception is at Rue de Gruyères 18 with the Hôtel du Cheval Blanc beside it.

Sources:
- https://loslorentes.com/
- https://loslorentes.com/hotel-du-cheval-blanc-bulle/

Qualified current destination evidence confirms Hôtel du Cheval Blanc is managed by Los Lorentes Residences and distinguishes the historic hotel from the several residence addresses:
- https://fribourg.ch/en/la-gruyere/hotels/los-lorentes-residences-hotel-du-cheval-blanc/

Current E4 exact-name search found no `Los Lorentes` row and `HOTEL_GROUPS_V2` has no exact Los Lorentes group row.

This must **not** be represented as one physical hotel identity.

Proposed graph:

```text
Los Lorentes Portfolio
  ├─ PORTFOLIO_COMPONENT_OF ◄─ Hôtel du Cheval Blanc — Bulle
  ├─ PORTFOLIO_COMPONENT_OF ◄─ Bulle residence components [multiple addresses]
  ├─ PORTFOLIO_COMPONENT_OF ◄─ Bern location
  └─ PORTFOLIO_COMPONENT_OF ◄─ Bern Airport location

Hôtel du Cheval Blanc ──SHARED_RECEPTION_WITH──► Bulle residence components
```

Entity-resolution must decide which components warrant independent accommodation identities. The source record `MD-2b51224ee38c42763d77` remains `EGR_REQUIRED_MULTI_COMPONENT_ACCOMMODATION_PORTFOLIO` until then.

## Proposed discovery priority

1. **LUVITA** — high-value operator edge and two independently evidenced hotels.
2. **La Rocca Living Hotel Group** — explicit group portfolio discovered from B07; likely fills multiple property gaps.
3. **Los Lorentes** — highest EGR value because one provider record represents multiple addressable accommodation components.
4. **Accor/Mövenpick** — useful brand-chain graph and dedupe context; property identities already clearly distinct.
5. **Swiss Quality Hotels** — model as cooperative/booking affiliation, not operator.
6. **VCH Hotels Schweiz** — model as association membership only.

## Formal materialization gate

A future domain claim may materialize these nodes/edges only after:

- fresh E4/HOTELS_V2 reread;
- exact existing group/entity lookup;
- current first-party evidence remains valid;
- relation type is proven (`OPERATED_BY` vs affiliation vs brand vs portfolio);
- no property identity is collapsed from shared brand/address/reception alone;
- shared recruiting route is independently verified before any duplicate outreach lock;
- all changes pass cross-plane integrity and graph invariants.

## Hard locks

```text
authority_advanced = false
HOTELS_V2 writes = 0
HOTEL_GROUPS_V2 writes = 0
H-ID allocations = 0
canonical ID reservations = 0
terminal mapping delta = 0
CRM_UNIVERSE_COMPLETE = false
OUTBOUND = CLOSED
send_allowed = 0
```
