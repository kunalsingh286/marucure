PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS local_miners (
    jan_aadhaar_no TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    exposure_years REAL NOT NULL,
    occupation_type TEXT NOT NULL CHECK(occupation_type IN ('stone_driller', 'stone_cutter', 'loading_transport', 'administrative')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
) STRICT;

CREATE TABLE IF NOT EXISTS local_screenings (
    screening_id TEXT PRIMARY KEY,
    jan_aadhaar_no TEXT NOT NULL,
    spirometry_fev1_fvc REAL NOT NULL,
    ai_confidence_score REAL NOT NULL,
    calculated_risk_index REAL NOT NULL,
    local_image_path TEXT NOT NULL UNIQUE,
    sync_status INTEGER DEFAULT 0 CHECK(sync_status IN (0, 1)),
    captured_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (jan_aadhaar_no) REFERENCES local_miners(jan_aadhaar_no) ON DELETE RESTRICT
) STRICT;
