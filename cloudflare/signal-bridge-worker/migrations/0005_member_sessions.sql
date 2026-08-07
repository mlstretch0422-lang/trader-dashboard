CREATE TABLE IF NOT EXISTS member_login_tokens (
  token_hash TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  discord_user_id TEXT NOT NULL,
  discord_guild_id TEXT,
  can_manage_journal INTEGER NOT NULL DEFAULT 0,
  used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_member_login_tokens_user_created
  ON member_login_tokens(discord_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_member_login_tokens_expires
  ON member_login_tokens(expires_at);

CREATE TABLE IF NOT EXISTS member_sessions (
  session_hash TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  discord_user_id TEXT NOT NULL,
  discord_guild_id TEXT,
  can_manage_journal INTEGER NOT NULL DEFAULT 0,
  revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_member_sessions_user_created
  ON member_sessions(discord_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_member_sessions_expires
  ON member_sessions(expires_at);

CREATE TABLE IF NOT EXISTS discord_interaction_log (
  id TEXT PRIMARY KEY,
  received_at TEXT NOT NULL,
  completed_at TEXT,
  command_name TEXT NOT NULL,
  discord_user_id TEXT,
  discord_channel_id TEXT,
  status TEXT NOT NULL,
  error_code TEXT,
  duration_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_discord_interaction_log_received
  ON discord_interaction_log(received_at DESC);

CREATE INDEX IF NOT EXISTS idx_discord_interaction_log_command_received
  ON discord_interaction_log(command_name, received_at DESC);
