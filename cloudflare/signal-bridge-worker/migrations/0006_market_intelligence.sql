CREATE TABLE IF NOT EXISTS market_intelligence_runs (
  id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  provider TEXT NOT NULL,
  data_type TEXT NOT NULL CHECK (data_type IN ('ECONOMIC_CALENDAR', 'HEADLINES')),
  status TEXT NOT NULL CHECK (status IN ('OK', 'UNAVAILABLE', 'ERROR')),
  item_count INTEGER NOT NULL DEFAULT 0,
  error_code TEXT,
  source_timestamp TEXT
);

CREATE INDEX IF NOT EXISTS idx_market_intelligence_runs_type_started
  ON market_intelligence_runs(data_type, started_at DESC);

CREATE TABLE IF NOT EXISTS economic_calendar_events (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  provider_event_id TEXT,
  event_time TEXT NOT NULL,
  country TEXT,
  category TEXT,
  event_name TEXT NOT NULL,
  importance INTEGER CHECK (importance IS NULL OR importance IN (1, 2, 3)),
  actual TEXT,
  previous TEXT,
  forecast TEXT,
  provider_forecast TEXT,
  source_name TEXT,
  source_url TEXT,
  provider_url TEXT,
  last_update TEXT,
  fetched_at TEXT NOT NULL,
  payload_json TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_calendar_provider_event
  ON economic_calendar_events(provider, provider_event_id);

CREATE INDEX IF NOT EXISTS idx_calendar_event_time_importance
  ON economic_calendar_events(event_time, importance DESC);

CREATE TABLE IF NOT EXISTS market_headlines (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  provider_item_id TEXT,
  published_at TEXT,
  title TEXT NOT NULL,
  publisher TEXT,
  url TEXT,
  symbol TEXT,
  fetched_at TEXT NOT NULL,
  payload_json TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_headline_provider_item
  ON market_headlines(provider, provider_item_id);

CREATE INDEX IF NOT EXISTS idx_headline_published
  ON market_headlines(published_at DESC, fetched_at DESC);
