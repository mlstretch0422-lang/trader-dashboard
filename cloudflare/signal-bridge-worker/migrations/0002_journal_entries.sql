CREATE TABLE IF NOT EXISTS journal_entries (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  journal_time TEXT,
  symbol TEXT,
  side TEXT CHECK (side IS NULL OR side IN ('LONG', 'SHORT', 'WAIT')),
  setup TEXT,
  strategy TEXT,
  title TEXT,
  raw_text TEXT NOT NULL,
  summary TEXT,
  result TEXT NOT NULL DEFAULT 'NA' CHECK (result IN ('WIN', 'LOSS', 'BE', 'OPEN', 'PASS', 'NA')),
  pnl REAL,
  rr REAL,
  tags TEXT,
  source TEXT NOT NULL,
  source_ref TEXT,
  signal_event_id TEXT,
  image_url TEXT,
  visibility TEXT NOT NULL DEFAULT 'PRIVATE' CHECK (visibility IN ('PRIVATE', 'PUBLISHED')),
  review_status TEXT NOT NULL DEFAULT 'RAW' CHECK (review_status IN ('RAW', 'NORMALIZED', 'REVIEWED'))
);

CREATE INDEX IF NOT EXISTS idx_journal_entries_created_at
  ON journal_entries(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_journal_entries_symbol_created_at
  ON journal_entries(symbol, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_journal_entries_result_created_at
  ON journal_entries(result, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_journal_entries_visibility_created_at
  ON journal_entries(visibility, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_journal_entries_signal_event_id
  ON journal_entries(signal_event_id);
