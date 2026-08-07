CREATE TABLE IF NOT EXISTS session_events (
  id TEXT PRIMARY KEY,
  received_at TEXT NOT NULL,
  event_time TEXT,
  session_date TEXT NOT NULL,
  symbol TEXT NOT NULL,
  stage TEXT NOT NULL CHECK (stage IN (
    'PREMARKET',
    'ORB_FORMED',
    'PREOPEN',
    'OPEN_SNAPSHOT',
    'SETUP',
    'WAIT',
    'SESSION_CLOSE',
    'TEST'
  )),
  side TEXT CHECK (side IS NULL OR side IN ('LONG', 'SHORT', 'WAIT')),
  price REAL,
  strategy TEXT NOT NULL,
  note TEXT NOT NULL,
  timeframe TEXT,
  orb_high REAL,
  orb_low REAL,
  orb_mid REAL,
  range_points REAL,
  bias TEXT,
  setup TEXT,
  target TEXT,
  outcome TEXT,
  payload_json TEXT,
  source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_events_date_symbol_received
  ON session_events(session_date, symbol, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_events_stage_received
  ON session_events(stage, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_events_symbol_stage_received
  ON session_events(symbol, stage, received_at DESC);
