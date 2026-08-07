ALTER TABLE journal_entries ADD COLUMN discord_guild_id TEXT;
ALTER TABLE journal_entries ADD COLUMN discord_channel_id TEXT;
ALTER TABLE journal_entries ADD COLUMN discord_message_id TEXT;
ALTER TABLE journal_entries ADD COLUMN discord_author_id TEXT;
ALTER TABLE journal_entries ADD COLUMN discord_interaction_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_journal_discord_message_id
  ON journal_entries(discord_message_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_journal_discord_interaction_id
  ON journal_entries(discord_interaction_id);

CREATE INDEX IF NOT EXISTS idx_journal_discord_channel_created_at
  ON journal_entries(discord_channel_id, created_at DESC);
