CREATE TABLE IF NOT EXISTS member_entitlements (
  discord_user_id TEXT PRIMARY KEY,
  discord_guild_id TEXT,
  tier TEXT NOT NULL DEFAULT 'BETA',
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  source TEXT NOT NULL DEFAULT 'DISCORD_BETA',
  granted_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  expires_at TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_member_entitlements_status_tier
  ON member_entitlements(status, tier, updated_at DESC);
