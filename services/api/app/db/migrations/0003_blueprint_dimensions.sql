-- Migration: 0003_blueprint_dimensions
-- Description: Create tables for storing blueprint-extracted dimensions
-- Date: March 4, 2026

-- Blueprint source files and metadata
CREATE TABLE IF NOT EXISTS blueprints (
    blueprint_id TEXT PRIMARY KEY,

    -- Source info
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_hash TEXT,                    -- SHA256 for deduplication

    -- Instrument classification
    instrument_model TEXT,             -- 'archtop', 'es_335', 'dreadnought', etc.
    instrument_category TEXT,          -- 'electric', 'acoustic', 'bass', 'archtop'
    maker TEXT,                        -- 'Benedetto', 'Gibson', 'Martin', etc.

    -- Image metadata
    image_width_px INTEGER,
    image_height_px INTEGER,
    dpi_estimated REAL,

    -- Processing status
    ocr_processed INTEGER DEFAULT 0,   -- 1 = OCR complete
    geometry_extracted INTEGER DEFAULT 0,

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Individual extracted dimensions
CREATE TABLE IF NOT EXISTS blueprint_dimensions (
    dimension_id INTEGER PRIMARY KEY AUTOINCREMENT,
    blueprint_id TEXT NOT NULL,

    -- Raw extraction
    raw_text TEXT NOT NULL,            -- Original OCR text
    value_mm REAL NOT NULL,            -- Converted value in mm
    value_inches REAL,                 -- Value in inches
    detected_unit TEXT,                -- 'mm', 'in', 'unknown'
    confidence REAL,                   -- OCR confidence 0-1

    -- Location in image
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_width INTEGER,
    bbox_height INTEGER,

    -- Context and classification
    context_text TEXT,                 -- Nearby text for context
    dimension_type TEXT,               -- 'body_length', 'bout_width', 'depth', etc.
    is_verified INTEGER DEFAULT 0,     -- User verified

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (blueprint_id) REFERENCES blueprints(blueprint_id)
);

-- Aggregated instrument specifications from blueprints
CREATE TABLE IF NOT EXISTS instrument_specs (
    spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    blueprint_id TEXT,

    -- Instrument identification
    instrument_model TEXT NOT NULL,
    maker TEXT,
    model_name TEXT,                   -- Specific model like "La Venezia"

    -- Body dimensions (mm)
    body_length REAL,
    upper_bout_width REAL,
    lower_bout_width REAL,
    waist_width REAL,
    body_depth_side REAL,
    body_depth_heel REAL,

    -- Sound features (mm)
    soundhole_diameter REAL,
    f_hole_length REAL,
    f_hole_width REAL,

    -- Neck dimensions (mm)
    scale_length REAL,
    nut_width REAL,
    neck_width_12th REAL,
    neck_depth_1st REAL,
    neck_depth_9th REAL,

    -- Bracing info
    bracing_pattern TEXT,              -- 'X', 'ladder', 'fan', etc.

    -- Source tracking
    source_type TEXT DEFAULT 'ocr',    -- 'ocr', 'manual', 'imported'
    confidence_score REAL,

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (blueprint_id) REFERENCES blueprints(blueprint_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_dimensions_blueprint ON blueprint_dimensions(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_dimensions_type ON blueprint_dimensions(dimension_type);
CREATE INDEX IF NOT EXISTS idx_specs_model ON instrument_specs(instrument_model);
CREATE INDEX IF NOT EXISTS idx_specs_maker ON instrument_specs(maker);
CREATE INDEX IF NOT EXISTS idx_blueprints_model ON blueprints(instrument_model);

-- Record migration
INSERT OR IGNORE INTO _migrations (migration_id, applied_at)
VALUES ('0003_blueprint_dimensions', datetime('now'));
