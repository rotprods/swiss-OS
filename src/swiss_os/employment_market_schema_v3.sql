-- EMPLOYMENT MARKET V3 — ADDITIVE SOURCE/VACANCY SEMANTICS
-- Token35 / A10+A30. This overlay preserves multi_niche_schema.sql V2 unchanged.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_families_v1 (
  source_family_id TEXT PRIMARY KEY CHECK (source_family_id LIKE 'FAM-%'),
  family_name TEXT NOT NULL,
  provider_name TEXT NOT NULL,
  family_class TEXT NOT NULL CHECK (family_class IN (
    'PUBLIC_INFRASTRUCTURE','PRIVATE_PLATFORM','EMPLOYER','STAFFING','SECTOR_PLATFORM'
  ))
);

CREATE TABLE IF NOT EXISTS source_surfaces_v1 (
  source_surface_id TEXT PRIMARY KEY CHECK (source_surface_id LIKE 'SRC-%'),
  source_family_id TEXT NOT NULL,
  surface_name TEXT NOT NULL,
  canonical_url TEXT NOT NULL,
  surface_type TEXT NOT NULL CHECK (surface_type IN (
    'OFFICIAL_PUBLIC_INVENTORY','EMPLOYER_FIRST_PARTY','STAFFING_AGENCY',
    'NATIONAL_JOB_BOARD','SECTOR_JOB_BOARD','SECONDARY_AGGREGATOR',
    'GUIDANCE_SURFACE','PUBLICATION_API'
  )),
  scope TEXT NOT NULL,
  inventory_role INTEGER NOT NULL CHECK (inventory_role IN (0,1)),
  automation_policy TEXT NOT NULL CHECK (automation_policy IN (
    'AUTHORIZED','PROHIBITED','UNKNOWN_REQUIRES_REVIEW'
  )),
  canonicality TEXT NOT NULL CHECK (canonicality IN (
    'PRIMARY_EMPLOYER','PRIMARY_PUBLIC_RECORD','DISCOVERY',
    'SECONDARY_DISCOVERY','POLICY_GUIDANCE','PUBLICATION_ONLY'
  )),
  api_role TEXT NOT NULL DEFAULT 'NONE' CHECK (api_role IN (
    'NONE','READ_INVENTORY','PUBLICATION_ONLY'
  )),
  observed_at TEXT NOT NULL,
  FOREIGN KEY (source_family_id) REFERENCES source_families_v1(source_family_id),
  CHECK (surface_type NOT IN ('GUIDANCE_SURFACE','PUBLICATION_API') OR inventory_role = 0),
  CHECK (surface_type != 'PUBLICATION_API' OR api_role = 'PUBLICATION_ONLY')
);

CREATE TABLE IF NOT EXISTS source_surface_languages_v1 (
  source_surface_id TEXT NOT NULL,
  language_code TEXT NOT NULL,
  PRIMARY KEY (source_surface_id, language_code),
  FOREIGN KEY (source_surface_id) REFERENCES source_surfaces_v1(source_surface_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source_surface_niches_v1 (
  source_surface_id TEXT NOT NULL,
  niche_id TEXT NOT NULL,
  coverage_state TEXT NOT NULL DEFAULT 'DECLARED' CHECK (coverage_state IN (
    'DECLARED','OBSERVED','UNKNOWN'
  )),
  PRIMARY KEY (source_surface_id, niche_id),
  FOREIGN KEY (source_surface_id) REFERENCES source_surfaces_v1(source_surface_id) ON DELETE CASCADE,
  FOREIGN KEY (niche_id) REFERENCES niches(niche_id)
);

CREATE TABLE IF NOT EXISTS source_surface_evidence_v1 (
  source_surface_id TEXT NOT NULL,
  evidence_url TEXT NOT NULL,
  evidence_kind TEXT NOT NULL CHECK (evidence_kind IN (
    'SURFACE','TERMS','ACCESS_POLICY','OFFICIAL_GUIDANCE','CURRENT_INVENTORY'
  )),
  observed_at TEXT NOT NULL,
  PRIMARY KEY (source_surface_id, evidence_url, evidence_kind),
  FOREIGN KEY (source_surface_id) REFERENCES source_surfaces_v1(source_surface_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source_snapshots_v3 (
  source_snapshot_id TEXT PRIMARY KEY,
  source_surface_id TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  capture_mode TEXT NOT NULL CHECK (capture_mode IN (
    'MANUAL_WEB','SEARCH_ENGINE_DISCOVERY','OFFICIAL_READ_API','FIXTURE_ONLY','BLOCKED'
  )),
  payload_sha256 TEXT,
  parser_version TEXT,
  snapshot_state TEXT NOT NULL CHECK (snapshot_state IN (
    'CAPTURED','BLOCKED','FAILED','EMPTY_VERIFIED'
  )),
  evidence_scope TEXT NOT NULL CHECK (evidence_scope IN (
    'CURRENT_SNAPSHOT','HISTORICAL_INDEXED','RECONCILE_REQUIRED','UNKNOWN_SCOPE'
  )),
  FOREIGN KEY (source_surface_id) REFERENCES source_surfaces_v1(source_surface_id)
);

CREATE TABLE IF NOT EXISTS vacancy_source_records_v1 (
  source_record_id TEXT PRIMARY KEY,
  source_snapshot_id TEXT NOT NULL,
  source_surface_id TEXT NOT NULL,
  provider_record_key TEXT,
  detail_url TEXT,
  raw_title TEXT,
  raw_employer TEXT,
  raw_location TEXT,
  published_at TEXT,
  observed_at TEXT NOT NULL,
  content_sha256 TEXT,
  raw_payload_ref TEXT,
  parse_status TEXT NOT NULL CHECK (parse_status IN (
    'PARSED','PARTIAL','UNPARSED','BLOCKED'
  )),
  provenance_ref TEXT NOT NULL,
  FOREIGN KEY (source_snapshot_id) REFERENCES source_snapshots_v3(source_snapshot_id),
  FOREIGN KEY (source_surface_id) REFERENCES source_surfaces_v1(source_surface_id)
);

CREATE INDEX IF NOT EXISTS idx_vacancy_source_records_surface
  ON vacancy_source_records_v1(source_surface_id, provider_record_key);
CREATE INDEX IF NOT EXISTS idx_vacancy_source_records_snapshot
  ON vacancy_source_records_v1(source_snapshot_id);

CREATE TABLE IF NOT EXISTS normalized_vacancy_candidates_v1 (
  vacancy_candidate_id TEXT PRIMARY KEY,
  source_record_id TEXT NOT NULL UNIQUE,
  normalized_title TEXT,
  normalized_employer_name TEXT,
  normalized_city TEXT,
  normalized_canton TEXT,
  contract_type TEXT,
  workload_min INTEGER CHECK (workload_min IS NULL OR (workload_min >= 0 AND workload_min <= 100)),
  workload_max INTEGER CHECK (workload_max IS NULL OR (workload_max >= 0 AND workload_max <= 100)),
  start_date TEXT,
  end_date TEXT,
  parser_version TEXT NOT NULL,
  candidate_state TEXT NOT NULL CHECK (candidate_state IN (
    'NORMALIZED','REVIEW_REQUIRED','REJECTED'
  )),
  FOREIGN KEY (source_record_id) REFERENCES vacancy_source_records_v1(source_record_id),
  CHECK (workload_min IS NULL OR workload_max IS NULL OR workload_min <= workload_max)
);

CREATE TABLE IF NOT EXISTS canonical_vacancies_v1 (
  vacancy_id TEXT PRIMARY KEY,
  employer_name TEXT NOT NULL,
  organization_id TEXT,
  role_family_id TEXT,
  canonical_title TEXT NOT NULL,
  city TEXT,
  canton TEXT,
  contract_type TEXT,
  workload_min INTEGER CHECK (workload_min IS NULL OR (workload_min >= 0 AND workload_min <= 100)),
  workload_max INTEGER CHECK (workload_max IS NULL OR (workload_max >= 0 AND workload_max <= 100)),
  start_date TEXT,
  end_date TEXT,
  first_seen_at TEXT NOT NULL,
  last_verified_at TEXT NOT NULL,
  vacancy_state TEXT NOT NULL CHECK (vacancy_state IN (
    'DISCOVERED','CANONICAL_REVIEWED','LIVE_VERIFIED','FILLED',
    'EXPIRED','WITHDRAWN','UNKNOWN_AFTER_SEARCH'
  )),
  FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
  FOREIGN KEY (role_family_id) REFERENCES role_families(role_family_id),
  CHECK (workload_min IS NULL OR workload_max IS NULL OR workload_min <= workload_max)
);

CREATE TABLE IF NOT EXISTS canonical_vacancy_sources_v1 (
  vacancy_id TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  identity_basis TEXT NOT NULL CHECK (identity_basis IN (
    'EXACT_PROVIDER_KEY','EMPLOYER_FIRST_PARTY_ID','CANONICAL_URL_EXACT','MANUAL_REVIEW_CONFIRMED'
  )),
  linked_at TEXT NOT NULL,
  PRIMARY KEY (vacancy_id, source_record_id),
  FOREIGN KEY (vacancy_id) REFERENCES canonical_vacancies_v1(vacancy_id) ON DELETE CASCADE,
  FOREIGN KEY (source_record_id) REFERENCES vacancy_source_records_v1(source_record_id)
);

CREATE TABLE IF NOT EXISTS requirement_assertions_v1 (
  requirement_assertion_id TEXT PRIMARY KEY,
  vacancy_id TEXT NOT NULL,
  dimension TEXT NOT NULL,
  subject TEXT NOT NULL,
  assertion_state TEXT NOT NULL CHECK (assertion_state IN (
    'REQUIRED','PREFERRED','ADVANTAGE','NOT_REQUIRED','NOT_STATED','UNKNOWN_AFTER_SEARCH'
  )),
  explicit_value TEXT,
  evidence_ref TEXT NOT NULL,
  evidence_source_record_id TEXT,
  search_proof_ref TEXT,
  observed_at TEXT NOT NULL,
  FOREIGN KEY (vacancy_id) REFERENCES canonical_vacancies_v1(vacancy_id) ON DELETE CASCADE,
  FOREIGN KEY (evidence_source_record_id) REFERENCES vacancy_source_records_v1(source_record_id),
  CHECK (assertion_state != 'UNKNOWN_AFTER_SEARCH' OR search_proof_ref IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_requirement_assertions_vacancy
  ON requirement_assertions_v1(vacancy_id, dimension, subject);

CREATE TABLE IF NOT EXISTS salary_assertions_v1 (
  salary_assertion_id TEXT PRIMARY KEY,
  vacancy_id TEXT NOT NULL,
  salary_state TEXT NOT NULL CHECK (salary_state IN (
    'DISCLOSED','DERIVED_RULE','MARKET_ESTIMATE'
  )),
  currency TEXT NOT NULL DEFAULT 'CHF',
  amount_min REAL,
  amount_max REAL,
  period TEXT CHECK (period IS NULL OR period IN (
    'HOUR','DAY','MONTH','YEAR','TOTAL_CONTRACT'
  )),
  evidence_ref TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  FOREIGN KEY (vacancy_id) REFERENCES canonical_vacancies_v1(vacancy_id) ON DELETE CASCADE,
  CHECK (amount_min IS NULL OR amount_max IS NULL OR amount_min <= amount_max)
);

CREATE TABLE IF NOT EXISTS opportunities_v3 (
  opportunity_id TEXT PRIMARY KEY,
  vacancy_id TEXT NOT NULL,
  candidate_ref TEXT NOT NULL,
  lane TEXT NOT NULL CHECK (lane IN ('ENTRY','HYBRID','CREATIVE','PORTAL','CROSS_LANE')),
  fit_state TEXT NOT NULL CHECK (fit_state IN ('REVIEW','READY_NO_SEND','BLOCKED','DEFERRED')),
  blockers_json TEXT NOT NULL DEFAULT '[]',
  unknowns_json TEXT NOT NULL DEFAULT '[]',
  reason_vector_json TEXT NOT NULL DEFAULT '{}',
  evidence_quality TEXT NOT NULL CHECK (evidence_quality IN ('HIGH','MEDIUM','LOW','UNKNOWN')),
  observed_at TEXT NOT NULL,
  outbound_state TEXT NOT NULL DEFAULT 'CLOSED' CHECK (outbound_state = 'CLOSED'),
  send_allowed INTEGER NOT NULL DEFAULT 0 CHECK (send_allowed = 0),
  FOREIGN KEY (vacancy_id) REFERENCES canonical_vacancies_v1(vacancy_id),
  UNIQUE (vacancy_id, candidate_ref, lane)
);

CREATE INDEX IF NOT EXISTS idx_opportunities_v3_vacancy
  ON opportunities_v3(vacancy_id);
