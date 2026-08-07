# Discord Journal Capture Setup

## Purpose

Signal Bridge Journal Intelligence captures trade-journal content from Discord without running an always-on Mac bot or requesting the privileged Message Content gateway intent.

The hosted Worker exposes:

`POST https://signal-bridge-webhook.airy-iris.workers.dev/discord-interactions`

Discord interactions are verified with the application's Ed25519 public key before anything is written to D1.

Three capture/publish surfaces are registered for the configured server:

1. `/journal` — structured trade journaling directly in Discord. Private by default; server managers can set `publish:true` for a selected public entry.
2. `Capture to Journal` — a message context command that saves an existing trade-journal message privately into Signal Bridge.
3. `Publish to Journal` — a server-manager-only message context action that publishes a selected message to the website. If that message was already captured privately, Signal Bridge promotes the existing D1 record rather than duplicating it.

Normal Discord capture remains `PRIVATE` + `RAW` by default. The public website returns only entries explicitly marked `PUBLISHED`.

## Why interactions instead of a gateway listener

Discord supports HTTP-based outgoing interactions as an alternative to a connected gateway client. That lets the Cloudflare Worker receive slash commands and message context commands without keeping a process online.

A true automatic listener for every normal channel message would require a gateway connection and, depending on implementation and scale, Message Content intent considerations. Signal Bridge deliberately starts with interaction-based capture because it is lower-maintenance and has a smaller permission surface.

## Discord application values

Create or reuse the dedicated Signal Bridge application and keep these values in `.env.local` only:

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

Discord sends a signed PING during endpoint validation; the Worker returns PONG after verifying the signature.

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

The script uses guild-scoped command registration so command changes appear immediately in the configured server.

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
- optional `publish` boolean

With `publish` omitted/false, the Worker stores the entry privately and posts the normal structured receipt in Discord. When `publish:true` is requested by a server member with Administrator or Manage Server permission, the Worker stores the entry as `PUBLISHED` + `REVIEWED` and it becomes eligible for the public Journal feed.

### `Capture to Journal`

Write a normal short-form journal message in the configured Discord channel. Then use the message's Apps/context menu -> `Capture to Journal`.

The Worker stores the original message text, provenance, and first attachment URL as a private raw journal entry. The confirmation is ephemeral so the original message remains the visible Discord journal record.

### `Publish to Journal`

For a selected note/chart that should appear on the website, a server manager can use the message's Apps/context menu -> `Publish to Journal`.

- If the message was never captured, Signal Bridge creates a public reviewed journal record.
- If the same Discord message already exists privately, Signal Bridge updates that existing record to `PUBLISHED` + `REVIEWED` instead of creating a duplicate.
- The first attachment URL is kept as `image_url`, and the public Journal renders it with the entry while the URL remains valid.

The message ID and interaction ID remain uniquely indexed to prevent duplicate capture.

## Media boundary

Discord attachment URLs now support immediate published screenshot rendering, but they should not be treated as permanent archive storage. The member/auth phase should copy approved screenshots to durable object storage so public and private journal media remain available independently of Discord CDN URLs.

## Evidence boundary

Discord journal records are execution/process evidence. They improve the research dataset and the review loop, but historical/backtest/forward evidence classes remain separate inside Signal Bridge.
