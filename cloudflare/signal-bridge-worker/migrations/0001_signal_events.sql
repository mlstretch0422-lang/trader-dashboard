CREATE TABLE IF NOT EXISTS signal_events (
  id TEXT PRIMARY KEY,
  received_at TEXT NOT NULL,
  alert_time TEXT,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT', 'WAIT')),
  event TEXT NOT NULL CHECK (event IN ('ENTRY', 'EXIT', 'STOP', 'TARGET', 'ALERT', 'TEST')),
  price TEXT,
  strategy TEXT NOT NULL,
  note TEXT NOT NULL,
  source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signal_events_received_at
  ON signal_events(received_at DESC);

CREATE INDEX IF NOT EXISTS idx_signal_events_symbol_received_at
  ON signal_events(symbol, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_signal_events_side_received_at
  ON signal_events(side, received_at DESC);
