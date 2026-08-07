CREATE TABLE IF NOT EXISTS bot_dispatch_log (
  dispatch_key TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  session_date TEXT NOT NULL,
  scheduled_for TEXT,
  attempted_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL,
  error_code TEXT,
  payload_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_bot_dispatch_session_kind
  ON bot_dispatch_log(session_date, kind, status);
