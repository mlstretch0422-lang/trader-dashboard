# Signal Bridge Live History Setup

This document covers the durable TradingView event history layer for the hosted Signal Bridge Worker.

## Architecture

TradingView alert → hosted Worker `/tv-alert` → Discord + D1 event ledger → Premium OS `/signals.html`

The Discord webhook secret remains a Cloudflare Worker secret. It is never returned by the history API and must never be committed to GitHub.

## Storage

The Worker expects a Cloudflare D1 binding named `DB`.

`wrangler.toml` declares the binding without an account-specific resource ID. Wrangler 4.45+ supports automatic provisioning of D1 resources on deployment. The account-specific ID may be written into the local Wrangler config after provisioning; it does not need to be committed.

Schema migrations live in `migrations/`.

## Production deployment

From the repository root, after loading the existing local `.env.local` secrets:

```bash
TMP_SECRETS="$(mktemp)" && chmod 600 "$TMP_SECRETS"
printf 'DISCORD_WEBHOOK_URL=%s\nSIGNAL_BRIDGE_TEST_TOKEN=%s\n' \
  "$DISCORD_WEBHOOK_URL" "$TV_WEBHOOK_SECRET" > "$TMP_SECRETS"

npx -y wrangler@latest deploy \
  --config cloudflare/signal-bridge-worker/wrangler.toml \
  --secrets-file "$TMP_SECRETS"

npx -y wrangler@latest d1 migrations apply DB \
  --remote \
  --config cloudflare/signal-bridge-worker/wrangler.toml

rm -f "$TMP_SECRETS"
```

If Wrangler asks to provision the missing `DB` binding, approve it. If the Worker is already linked to a D1 database, Wrangler should reuse the binding.

## Endpoints

- `GET /health` — Worker version and whether D1 is bound.
- `GET /events?limit=25` — latest non-TEST events.
- `GET /events?side=LONG` — filter by side.
- `GET /events?event=ENTRY` — filter by event type.
- `GET /events?include_tests=1` — include authenticated test events.
- `POST /tv-alert` — TradingView-only production alert receiver.
- `POST /test` — authenticated infrastructure test receiver.

The public history API returns normalized event data only. It never returns secrets.

## Evidence boundary

A stored event proves that Signal Bridge received and normalized an alert and wrote it to the event ledger. It does **not** validate a strategy edge, profitability, or the isolated contribution of any strategy component.
