PRAGMA foreign_keys = ON;

-- Additive W1 overlay. This file MUST NOT mutate legacy hotel authority.
CREATE TABLE IF NOT EXISTS niches (
  niche_id TEXT PRIMARY KEY CHECK (niche_id GLOB 'NICHE-[0-9][0-9][0-9]'),
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL CHECK(length(trim(name)) > 0),
  state TEXT NOT NULL CHECK(state IN ('ACTIVE','PLANNED','PAUSED','RETIRED')),
  adapter_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations (
  organization_id TEXT PRIMARY KEY,
  canonical_name TEXT NOT NULL CHECK(length(trim(canonical_name)) > 0),
  organization_type TEXT NOT NULL,
  canonical_domain TEXT,
  country TEXT NOT NULL DEFAULT 'Switzerland',
  state TEXT NOT NULL CHECK(state IN ('ACTIVE','QUARANTINED','SUPERSEDED','REMOVED_OR_STALE')),
  superseded_by TEXT REFERENCES organizations(organization_id),
  source_ref TEXT NOT NULL,
  first_seen TEXT,
  last_seen TEXT,
  identity_confidence REAL CHECK(identity_confidence IS NULL OR identity_confidence BETWEEN 0 AND 1),
  CHECK((state='SUPERSEDED' AND superseded_by IS NOT NULL) OR state<>'SUPERSEDED')
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_org_domain ON organizations(lower(canonical_domain)) WHERE canonical_domain IS NOT NULL AND state='ACTIVE';

CREATE TABLE IF NOT EXISTS organization_niches (
  organization_id TEXT NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
  niche_id TEXT NOT NULL REFERENCES niches(niche_id),
  relation_type TEXT NOT NULL CHECK(relation_type IN ('PRIMARY','SECONDARY')),
  evidence_ref TEXT NOT NULL,
  PRIMARY KEY(organization_id,niche_id)
);

CREATE TABLE IF NOT EXISTS organization_locations (
  location_id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
  city TEXT NOT NULL DEFAULT '', canton TEXT, country TEXT NOT NULL DEFAULT 'Switzerland',
  address_text TEXT, postal_code TEXT, state TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(state IN ('ACTIVE','STALE','REMOVED')),
  evidence_ref TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organization_aliases (
  alias_id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
  alias_name TEXT NOT NULL, alias_city TEXT NOT NULL DEFAULT '', reason_code TEXT NOT NULL, source_ref TEXT NOT NULL,
  UNIQUE(organization_id,alias_name,alias_city)
);

CREATE TABLE IF NOT EXISTS source_snapshots_v2 (
  snapshot_id TEXT PRIMARY KEY, niche_id TEXT NOT NULL REFERENCES niches(niche_id), source_id TEXT NOT NULL,
  source_url TEXT NOT NULL, locale TEXT NOT NULL DEFAULT '', observed_at TEXT NOT NULL,
  raw_record_count INTEGER NOT NULL CHECK(raw_record_count>=0), page_count INTEGER CHECK(page_count IS NULL OR page_count>=0),
  source_scope TEXT NOT NULL, snapshot_state TEXT NOT NULL CHECK(snapshot_state IN ('DISCOVERED','STAGED','FROZEN_CANDIDATE','FROZEN_VERIFIED','SUPERSEDED')),
  records_sha256 TEXT, created_at TEXT NOT NULL, frozen_at TEXT,
  CHECK((snapshot_state='FROZEN_VERIFIED' AND frozen_at IS NOT NULL) OR snapshot_state<>'FROZEN_VERIFIED')
);

CREATE TABLE IF NOT EXISTS source_records_v2 (
  source_record_id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES source_snapshots_v2(snapshot_id) ON DELETE CASCADE,
  source_record_key TEXT NOT NULL, source_url TEXT NOT NULL, raw_name TEXT NOT NULL, raw_location TEXT NOT NULL DEFAULT '',
  normalized_name TEXT NOT NULL, normalized_location TEXT NOT NULL DEFAULT '', observed_at TEXT NOT NULL, evidence_ref TEXT NOT NULL,
  UNIQUE(snapshot_id,source_record_key)
);

CREATE TABLE IF NOT EXISTS source_record_mappings_v2 (
  source_record_id TEXT PRIMARY KEY REFERENCES source_records_v2(source_record_id) ON DELETE CASCADE,
  mapping_state TEXT NOT NULL CHECK(mapping_state IN ('ACTIVE_CANONICAL','ALIAS_TO_CANONICAL','EXCLUDED_WITH_REASON','RECONCILE_REQUIRED')),
  organization_id TEXT REFERENCES organizations(organization_id), exclusion_reason TEXT, reconcile_reason TEXT,
  confidence REAL CHECK(confidence IS NULL OR confidence BETWEEN 0 AND 1), evidence_ref TEXT NOT NULL, run_id TEXT, mapped_at TEXT NOT NULL,
  CHECK((mapping_state IN ('ACTIVE_CANONICAL','ALIAS_TO_CANONICAL') AND organization_id IS NOT NULL) OR (mapping_state NOT IN ('ACTIVE_CANONICAL','ALIAS_TO_CANONICAL') AND organization_id IS NULL))
);

CREATE TABLE IF NOT EXISTS role_families (
  role_family_id TEXT PRIMARY KEY, niche_id TEXT REFERENCES niches(niche_id), name TEXT NOT NULL, lane TEXT NOT NULL CHECK(lane IN ('ENTRY','HYBRID','CREATIVE','PORTAL','CROSS_LANE')), state TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS opportunities_v2 (
  opportunity_id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(organization_id), role_family_id TEXT REFERENCES role_families(role_family_id),
  external_ref TEXT, title TEXT NOT NULL, location_id TEXT REFERENCES organization_locations(location_id), state TEXT NOT NULL,
  source_ref TEXT NOT NULL, observed_at TEXT NOT NULL, fresh_until TEXT
);

CREATE TABLE IF NOT EXISTS applications_v2 (
  application_id TEXT PRIMARY KEY, opportunity_id TEXT REFERENCES opportunities_v2(opportunity_id), organization_id TEXT NOT NULL REFERENCES organizations(organization_id),
  lane TEXT NOT NULL CHECK(lane IN ('ENTRY','HYBRID','CREATIVE','PORTAL')), state TEXT NOT NULL,
  selected_asset_manifest_id TEXT, selected_channel_id TEXT, idempotency_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
);

-- Version-specific packet/readiness provenance. applications_v2 remains the stable
-- target/idempotency identity; re-rendering or re-validating cannot authorize a duplicate application.
CREATE TABLE IF NOT EXISTS application_packet_receipts_v1 (
  packet_id TEXT PRIMARY KEY,
  application_id TEXT NOT NULL REFERENCES applications_v2(application_id) ON DELETE CASCADE,
  readiness_binding_sha256 TEXT NOT NULL,
  aag_receipt_sha256 TEXT NOT NULL,
  target_role TEXT NOT NULL,
  vacancy_source_url TEXT NOT NULL,
  selected_asset_manifest_id TEXT NOT NULL,
  selected_channel_id TEXT NOT NULL,
  supplemental_asset_count INTEGER NOT NULL CHECK(supplemental_asset_count >= 0),
  state TEXT NOT NULL CHECK(state IN ('PACKET_COMPILED_NO_SEND','SUPERSEDED')),
  created_at TEXT NOT NULL,
  UNIQUE(application_id, readiness_binding_sha256, selected_asset_manifest_id, selected_channel_id)
);

CREATE TABLE IF NOT EXISTS responses_v2 (
  response_id TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES applications_v2(application_id) ON DELETE CASCADE,
  outcome_type TEXT NOT NULL CHECK(outcome_type IN ('ACKNOWLEDGED','NO_VACANCY','REJECTED','MORE_INFO','INTERVIEW','OFFER','WITHDRAWN','OTHER')),
  observed_reason TEXT, inferred_reason TEXT, evidence_ref TEXT NOT NULL, received_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS offers_v2 (
  offer_id TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES applications_v2(application_id), organization_id TEXT NOT NULL REFERENCES organizations(organization_id),
  state TEXT NOT NULL CHECK(state IN ('RECEIVED','VERIFYING','VERIFIED','FINANCIALLY_VIABLE','NOT_VIABLE','ACCEPTED','DECLINED','WITHDRAWN')),
  gross_salary_text TEXT, housing_text TEXT, evidence_ref TEXT NOT NULL, received_at TEXT NOT NULL
);

-- Compatibility bridge: hotel authority remains canonical_hotels; this table maps, never replaces it.
CREATE TABLE IF NOT EXISTS legacy_hotel_org_bridge (
  hotel_id TEXT PRIMARY KEY REFERENCES canonical_hotels(hotel_id) ON DELETE CASCADE,
  organization_id TEXT NOT NULL UNIQUE REFERENCES organizations(organization_id) ON DELETE CASCADE,
  bridge_state TEXT NOT NULL CHECK(bridge_state IN ('CANARY','VERIFIED_EQUIVALENT','RECONCILE_REQUIRED')),
  evidence_ref TEXT NOT NULL, verified_at TEXT
);

INSERT OR IGNORE INTO niches(niche_id,slug,name,state,adapter_version,created_at)
VALUES('NICHE-001','hotels','Hotels','ACTIVE','NICHE-CONTRACT-1.0','2026-09-01T00:00:00Z');