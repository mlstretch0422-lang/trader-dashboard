CREATE TABLE IF NOT EXISTS strategy_profiles (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  owner_type TEXT NOT NULL DEFAULT 'SYSTEM',
  owner_discord_id TEXT,
  slug TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_profile_owner_slug
  ON strategy_profiles(owner_type, COALESCE(owner_discord_id, ''), slug);

CREATE TABLE IF NOT EXISTS strategy_versions (
  id TEXT PRIMARY KEY,
  strategy_id TEXT NOT NULL,
  version_label TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'STAGED',
  evidence_stage TEXT NOT NULL DEFAULT 'IMPLEMENTED',
  parent_version_id TEXT,
  rules_json TEXT NOT NULL DEFAULT '{}',
  indicator_name TEXT,
  indicator_version TEXT,
  indicator_config_json TEXT NOT NULL DEFAULT '{}',
  change_note TEXT,
  is_current INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (strategy_id) REFERENCES strategy_profiles(id)
);

CREATE INDEX IF NOT EXISTS idx_strategy_versions_strategy
  ON strategy_versions(strategy_id, created_at DESC);

CREATE TABLE IF NOT EXISTS strategy_observations (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  strategy_version_id TEXT NOT NULL,
  observation_type TEXT NOT NULL,
  session_event_id TEXT,
  signal_event_id TEXT,
  journal_entry_id TEXT,
  outcome TEXT,
  note TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY (strategy_version_id) REFERENCES strategy_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_strategy_observations_version
  ON strategy_observations(strategy_version_id, created_at DESC);

ALTER TABLE session_events ADD COLUMN strategy_version_id TEXT;
ALTER TABLE session_events ADD COLUMN indicator_version TEXT;
ALTER TABLE signal_events ADD COLUMN strategy_version_id TEXT;
ALTER TABLE journal_entries ADD COLUMN strategy_version_id TEXT;

INSERT OR IGNORE INTO strategy_profiles (
  id, created_at, updated_at, owner_type, owner_discord_id, slug, name, description, status
) VALUES (
  'strategy-mason-orb',
  '2026-08-07T00:00:00.000Z',
  '2026-08-07T00:00:00.000Z',
  'SYSTEM',
  NULL,
  'mason-orb',
  'Mason ORB',
  'Flagship MES/ES opening-range and liquidity framework inside Signal Bridge.',
  'ACTIVE'
);

INSERT OR IGNORE INTO strategy_versions (
  id, strategy_id, version_label, created_at, status, evidence_stage,
  parent_version_id, rules_json, indicator_name, indicator_version,
  indicator_config_json, change_note, is_current
) VALUES (
  'mason-orb-v1.2-session-bridge',
  'strategy-mason-orb',
  'v1.2 Session Bridge',
  '2026-08-07T00:00:00.000Z',
  'STAGED',
  'IMPLEMENTED',
  NULL,
  '{"orb_start":"0800","orb_end":"0815","trade_start":"0930","trade_end":"1100","retest_mode_default":"Midpoint","range_min":5,"range_max":50,"vwap_default":true,"ema_default":false,"max_signals_per_day":1}',
  'ES/MES ORB Retest Indicator',
  '1.2-session-bridge',
  '{"premarket_snapshot":"0755","preopen_snapshot":"0915","session_lifecycle":true}',
  'Adds durable Signal Bridge session lifecycle events while preserving v1.1 signal logic.',
  1
);
