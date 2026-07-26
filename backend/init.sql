-- TRINETRA Database Schema
-- Initializes tables for OSINT scan results, watches, and alerts

-- Scan results table
CREATE TABLE IF NOT EXISTS scan_results (
    id SERIAL PRIMARY KEY,
    target VARCHAR(512) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    plugin_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    gui_data JSONB,
    terminal_data TEXT,
    freshness VARCHAR(50) DEFAULT 'fresh',
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups by target
CREATE INDEX IF NOT EXISTS idx_scan_results_target ON scan_results(target);
CREATE INDEX IF NOT EXISTS idx_scan_results_created_at ON scan_results(created_at DESC);

-- Watches table (for the Watch / monitoring feature)
CREATE TABLE IF NOT EXISTS watches (
    id SERIAL PRIMARY KEY,
    target VARCHAR(512) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    plugin_ids TEXT[] DEFAULT '{}',
    interval_seconds INTEGER DEFAULT 3600,
    webhook_url VARCHAR(1024),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_watches_active ON watches(is_active, last_checked_at);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    watch_id INTEGER REFERENCES watches(id) ON DELETE CASCADE,
    target VARCHAR(512) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_watch_id ON alerts(watch_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
