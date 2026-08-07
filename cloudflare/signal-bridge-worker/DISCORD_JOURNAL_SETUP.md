# Discord Journal Capture Setup

## Purpose

Signal Bridge Journal Intelligence can capture trade-journal content from Discord without running an always-on Mac bot or requesting the privileged Message Content gateway intent.

The hosted Worker exposes:

`POST https://signal-bridge-webhook.airy-iris.workers.dev/discord-interactions`

Discord interactions are verified with the application's Ed25519 public key before anything is written to D1.

Two capture surfaces are registered for the configured server:

1. `/journal` — structured trade journaling directly in Discord.
2. `Capture to Journal` — a message context command that saves an existing trade-journal message privately into Signal Bridge.

Every Discord-captured entry is stored as `PRIVATE` + `RAW` by default. The public website continues to return only entries explicitly marked `PUBLISHED`.

## Why interactions instead of a gateway listener

Discord supports HTTP-based outgoing interactions as an alternative to a connected gateway client. That lets the Cloudflare Worker receive slash commands and message context commands without keeping a process online.

A true automatic listener for every normal channel message would require a gateway connection and, depending on implementation and scale, Message Content intent considerations. Signal Bridge deliberately starts with interaction-based capture because it is lower-maintenance and has a smaller permission surface.

## Discord application values

Create or reuse a dedicated Discord application for Signal Bridge and keep these values in `.env.local` only:

```text
DISCORD_BOT_TOKEN=
DISCORD_PUBLIC_KEY=
DISCORD_APPLICATION_ID=
DISCORD_GUILD_ID=
DISCORD_JOURNAL_CHANNEL_ID=
```

- `DISCORD_BOT_TOKEN` is used only from the local machine to register commands. Do not deploy it to Cloudflare.
- `DISCORD_PUBLIC_KEY` is used by the Worker to verify Discord interaction signatures.
- `DISCORD_APPLICATION_ID` identifies the Signal Bridge Discord application.
- `DISCORD_GUILD_ID` restricts journal capture to the intended server.
- `DISCORD_JOURNAL_CHANNEL_ID` restricts journal capture to the intended trade-journal channel.

## Discord Developer Portal

1. Create a Discord application named `Signal Bridge` if a dedicated app does not already exist.
2. Copy the Application ID and Public Key from the application's General Information page.
3. Create/reset the Bot token from the Bot page and place it only in `.env.local`.
4. Install the application to the intended Discord server with `bot` and `applications.commands` scopes. The journal interaction flow does not require broad bot permissions.
5. Set the application's Interactions Endpoint URL to:

```text
https://signal-bridge-webhook.airy-iris.workers.dev/discord-interactions
```

Discord will send a signed PING during endpoint validation; the Worker returns PONG after verifying the signature.

## IDs

With Discord Developer Mode enabled:

- Copy Server ID -> `DISCORD_GUILD_ID`
- Copy the `trade-journal` channel ID -> `DISCORD_JOURNAL_CHANNEL_ID`

Do not commit `.env.local`.

## Deploy Worker secrets

When deploying, the secrets file should include the existing Signal Bridge secrets plus:

```text
DISCORD_PUBLIC_KEY
DISCORD_APPLICATION_ID
DISCORD_GUILD_ID
DISCORD_JOURNAL_CHANNEL_ID
```

`DISCORD_BOT_TOKEN` must not be included in the Worker secrets file.

After deploy, apply D1 migrations so `0003_discord_journal_metadata.sql` is active.

## Register commands

From the repository root after loading `.env.local`:

```bash
node cloudflare/signal-bridge-worker/register_discord_commands.mjs
```

The script uses guild-scoped command registration so the test commands update immediately in the configured server.

## Capture behavior

### `/journal`

The command accepts:

- required note
- optional symbol
- optional side (`LONG`, `SHORT`, `WAIT`)
- optional result (`WIN`, `LOSS`, `BE`, `OPEN`, `PASS`, `NA`)
- optional setup
- optional strategy/version
- optional dollar P&L
- optional R multiple
- optional chart attachment

The Worker stores the entry privately and posts a structured receipt in the Discord channel for accountability.

### `Capture to Journal`

Write a normal short-form journal message in the configured Discord channel. Then use the message's Apps/context menu -> `Capture to Journal`.

The Worker stores the original message text, provenance, and first attachment URL as a private raw journal entry. The capture confirmation is ephemeral so the original message remains the visible journal record.

The message ID and interaction ID are uniquely indexed to prevent duplicate capture.

## Media boundary

Discord attachment URLs are useful source references but should not be treated as permanent archive storage. A later Signal Bridge media phase should copy approved screenshots to durable object storage before relying on them for long-term website display.

## Evidence boundary

Discord journal records are execution/process evidence. Capturing more notes improves the research dataset, but journal observations alone do not prove strategy edge or validate a Pine component.
