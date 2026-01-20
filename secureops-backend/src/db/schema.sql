-- SecureOps Offline Safety Pipeline Schema
-- Generated: 2026-01-14
-- Scope: Offline persistence for construction safety monitoring (PPE, Zones, Proximity).
-- STRICTLY NO API/UI support tables.

-- 1. Safety Violations Table
-- Stores all safety events identified by the pipeline (PPE, Zone Intrusion, Time-based).
CREATE TABLE IF NOT EXISTS safety_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event Classification
    violation_type VARCHAR(50) NOT NULL, -- e.g. 'missing_helmet', 'zone_intrusion'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('warning', 'critical')),
    
    -- Timestamp (Pipeline execution time)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Context (Optional links to source media for audit)
    video_id VARCHAR(100),         -- Identifier of the video file
    frame_number INTEGER,          -- Frame index where violation occurred
    
    -- Entities Involved
    person_id INTEGER,             -- Tracker ID of the person (if available)
    zone_id VARCHAR(100),          -- ID/Name of the restricted zone (if applicable)
    
    -- Snapshot Data (JSONB justified for flexible context storage: bbox, rules triggered)
    -- Contains: bbox [x1,y1,x2,y2], specific rule metadata
    details JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for Safety Violations
-- 1. Reporting queries filter by date range and type.
CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON safety_violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_violations_type ON safety_violations(violation_type);
-- 2. Audit queries might look up violations for a specific person.
CREATE INDEX IF NOT EXISTS idx_violations_person ON safety_violations(person_id);


-- 2. Proximity Events Table
-- Stores detected unsafe proximity events between workers and machinery.
CREATE TABLE IF NOT EXISTS proximity_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event Timing
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Entities Involved (Tracker IDs)
    person_id INTEGER NOT NULL,
    machine_id INTEGER NOT NULL,
    machine_type VARCHAR(50) NOT NULL, -- e.g. 'excavator', 'forklift'
    
    -- Metrics
    distance_pixels FLOAT NOT NULL,   -- Camera-relative distance
    threshold_pixels FLOAT NOT NULL,  -- The threshold that was breached
    
    -- Classification
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('warning', 'critical')),
    
    -- Context
    video_id VARCHAR(100),
    frame_number INTEGER,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for Proximity Events
-- 1. Reporting queries filter by severity and date.
CREATE INDEX IF NOT EXISTS idx_proximity_timestamp ON proximity_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_proximity_severity ON proximity_events(severity);


-- 3. Site Metrics Table
-- Aggregated daily statistics for rapid reporting without scanning partial events.
CREATE TABLE IF NOT EXISTS site_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Daily Bucket
    metric_date DATE NOT NULL UNIQUE,
    
    -- Aggregated Counts
    total_detections INTEGER DEFAULT 0,
    total_violations INTEGER DEFAULT 0,
    
    -- Computed Metrics
    ppe_compliance_rate FLOAT DEFAULT 100.0, -- Percentage (0-100)
    
    -- Specific Breakdown
    zone_violations_count INTEGER DEFAULT 0,
    proximity_warnings_count INTEGER DEFAULT 0,
    proximity_critical_count INTEGER DEFAULT 0,
    
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for Site Metrics
-- 1. Lookups by date are the primary access pattern.
CREATE INDEX IF NOT EXISTS idx_metrics_date ON site_metrics(metric_date);

-- 4. PPE Violations Table
-- Normalized table for storing strict rule-engine violations (Helmet/Vest).
CREATE TABLE IF NOT EXISTS ppe_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tracking
    track_id INTEGER NOT NULL,
    source_id UUID,                 -- video_id / upload_id (nullable for offline)

    -- Violation metadata
    violation_type TEXT NOT NULL CHECK (violation_type = 'PPE'),
    missing_items TEXT[] NOT NULL,  -- ['helmet'], ['vest'], ['helmet','vest']

    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),

    -- Timing
    start_time TIMESTAMPTZ NOT NULL,
    end_time   TIMESTAMPTZ NOT NULL,
    duration_seconds REAL NOT NULL,

    -- Confidence
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for PPE Violations
CREATE INDEX IF NOT EXISTS idx_ppe_track_id ON ppe_violations(track_id);
CREATE INDEX IF NOT EXISTS idx_ppe_severity ON ppe_violations(severity);
CREATE INDEX IF NOT EXISTS idx_ppe_time ON ppe_violations(start_time, end_time);

CREATE TABLE IF NOT EXISTS proximity_events (
    id BIGSERIAL PRIMARY KEY,
    upload_id UUID,
    person_id INTEGER NOT NULL,
    machine_type TEXT NOT NULL CHECK (
        machine_type IN ('excavator', 'dump_truck')
    ),
    severity TEXT NOT NULL CHECK (
        severity IN ('WARNING', 'CRITICAL')
    ),
    distance_norm REAL NOT NULL CHECK (distance_norm >= 0 AND distance_norm <= 1),
    event_time TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_proximity_upload_id
    ON proximity_events (upload_id);

CREATE INDEX IF NOT EXISTS idx_proximity_severity
    ON proximity_events (severity);

CREATE INDEX IF NOT EXISTS idx_proximity_event_time
    ON proximity_events (event_time);

CREATE INDEX IF NOT EXISTS idx_proximity_person
    ON proximity_events (person_id);
