PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS canonical_hotels (
    hotel_id TEXT PRIMARY KEY CHECK (hotel_id GLOB 'H-[0-9][0-9][0-9][0-9]'),
    canonical_name TEXT NOT NULL CHECK (length(trim(canonical_name)) > 0),
    city TEXT NOT NULL CHECK (length(trim(city)) > 0),
    canton TEXT,
    country TEXT NOT NULL DEFAULT 'Switzerland',
    canonical_domain TEXT,
    membership_state TEXT NOT NULL DEFAULT 'UNKNOWN_SCOPE',
    state TEXT NOT NULL CHECK (state IN ('ACTIVE','QUARANTINED','SUPERSEDED_DUPLICATE','REMOVED_OR_STALE')),
    superseded_by TEXT REFERENCES canonical_hotels(hotel_id),
    source_ref TEXT NOT NULL,
    first_seen TEXT,
    last_seen TEXT,
    identity_confidence REAL CHECK (identity_confidence IS NULL OR (identity_confidence >= 0.0 AND identity_confidence <= 1.0)),
    CHECK ((state = 'SUPERSEDED_DUPLICATE' AND superseded_by IS NOT NULL) OR state <> 'SUPERSEDED_DUPLICATE')
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_active_hotel_domain
ON canonical_hotels(lower(canonical_domain))
WHERE canonical_domain IS NOT NULL AND state = 'ACTIVE';

CREATE TABLE IF NOT EXISTS entity_aliases (
    alias_id TEXT PRIMARY KEY,
    canonical_hotel_id TEXT NOT NULL REFERENCES canonical_hotels(hotel_id) ON DELETE CASCADE,
    alias_name TEXT NOT NULL,
    alias_city TEXT NOT NULL DEFAULT '',
    reason_code TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    UNIQUE(canonical_hotel_id, alias_name, alias_city)
);

CREATE TABLE IF NOT EXISTS scheduler_tasks (
    task_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority >= 0 AND priority <= 1000),
    state TEXT NOT NULL CHECK (state IN ('READY','ACTIVE','BLOCKED','COMPLETE','FAILED','CANCELLED')),
    freshness_key TEXT NOT NULL DEFAULT '',
    dependency_ids_json TEXT NOT NULL DEFAULT '[]',
    reason_code TEXT,
    run_id TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_scheduler_active_task
ON scheduler_tasks(scope_id, task_type, freshness_key)
WHERE state IN ('READY','ACTIVE');

CREATE TABLE IF NOT EXISTS state_transitions (
    transition_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    run_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_records (
    run_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL,
    checkpoint_id TEXT,
    canonical_before INTEGER NOT NULL CHECK (canonical_before >= 0),
    canonical_after INTEGER NOT NULL CHECK (canonical_after >= 0),
    db_integrity TEXT NOT NULL,
    fk_violations INTEGER NOT NULL CHECK (fk_violations >= 0),
    duplicate_count INTEGER NOT NULL CHECK (duplicate_count >= 0),
    snapshot_drift INTEGER NOT NULL,
    send_allowed_count INTEGER NOT NULL CHECK (send_allowed_count >= 0),
    quality_result TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (send_allowed_count = 0)
);
