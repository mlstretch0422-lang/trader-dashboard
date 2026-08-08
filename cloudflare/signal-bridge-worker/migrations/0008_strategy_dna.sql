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

-- v1.2 predates the generic strategy_version_id field in its TradingView payload.
-- Link that exact named integration automatically so Monday forward session events
-- immediately become Strategy DNA observations without changing the v1.2 signal rules.
CREATE TRIGGER IF NOT EXISTS trg_session_mason_orb_v12_dna
AFTER INSERT ON session_events
WHEN NEW.strategy = 'ES/MES ORB Indicator v1.2 Session Bridge'
BEGIN
  UPDATE session_events
  SET strategy_version_id = COALESCE(NEW.strategy_version_id, 'mason-orb-v1.2-session-bridge'),
      indicator_version = COALESCE(NEW.indicator_version, '1.2-session-bridge')
  WHERE id = NEW.id;

  INSERT OR IGNORE INTO strategy_observations (
    id, created_at, strategy_version_id, observation_type,
    session_event_id, signal_event_id, journal_entry_id,
    outcome, note, metadata_json
  ) VALUES (
    'session:' || NEW.id,
    NEW.received_at,
    'mason-orb-v1.2-session-bridge',
    NEW.stage,
    NEW.id,
    NULL,
    NULL,
    NEW.outcome,
    NEW.note,
    '{}'
  );
END;
