# Signal Bridge hosted webhook worker

This Worker removes the Mac/quick-tunnel dependency from production alert delivery.

Production path:

`TradingView -> Cloudflare Worker -> Discord`

The existing local Signal Bridge server remains useful for local dashboard/testing, but Discord alert delivery no longer depends on the Mac staying awake once this Worker is deployed.

## Security model

- `DISCORD_WEBHOOK_URL` is stored only as an encrypted Cloudflare Worker secret.
- TradingView `/tv-alert` requests are accepted only from TradingView's published webhook source IP addresses.
- TradingView alert JSON contains no password or webhook credential.
- `/test` is separate and requires the `SIGNAL_BRIDGE_TEST_TOKEN` bearer token.
- Request bodies are JSON-only and capped at 16 KiB.
- Side/event values are validated and text fields are length-limited.
- Discord delivery runs asynchronously so TradingView receives a response quickly.

Published TradingView webhook IPs used by the Worker:

- `52.89.214.238`
- `34.212.75.30`
- `54.218.53.128`
- `52.32.178.7`

Re-check TradingView's current webhook documentation before changing this allowlist.

## Deploy from the repository

From the repository root, after Cloudflare authentication:

```bash
set -a
source .env.local
set +a
TMP_SECRETS="$(mktemp)"
chmod 600 "$TMP_SECRETS"
printf 'DISCORD_WEBHOOK_URL=%s\nSIGNAL_BRIDGE_TEST_TOKEN=%s\n' \
  "$DISCORD_WEBHOOK_URL" "$TV_WEBHOOK_SECRET" > "$TMP_SECRETS"
npx wrangler deploy \
  --config cloudflare/signal-bridge-worker/wrangler.toml \
  --secrets-file "$TMP_SECRETS"
rm -f "$TMP_SECRETS"
```

The initial deployment uses the stable Cloudflare `workers.dev` route assigned to the Worker. A custom domain should replace `workers.dev` before Signal Bridge is treated as business-critical production infrastructure.

## Health check

```text
GET https://<worker-host>/health
```

Expected response:

```json
{"ok":true,"service":"signal-bridge-worker","version":"1.0.0"}
```

## Authenticated manual test

Use the local `TV_WEBHOOK_SECRET` only as the private `/test` bearer token. It is not placed in a TradingView message.

```bash
set -a
source .env.local
set +a
curl -sS -X POST "https://<worker-host>/test" \
  -H "Authorization: Bearer $TV_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"MES","side":"LONG","event":"TEST","price":"6000","strategy":"Signal Bridge","note":"Hosted Worker test"}'
```

## TradingView payload

Long:

```json
{"symbol":"{{ticker}}","side":"LONG","event":"entry","price":"{{close}}","strategy":"ES/MES ORB v1.1","note":"Long Setup Ready","time":"{{timenow}}"}
```

Short:

```json
{"symbol":"{{ticker}}","side":"SHORT","event":"entry","price":"{{close}}","strategy":"ES/MES ORB v1.1","note":"Short Setup Ready","time":"{{timenow}}"}
```

Webhook URL:

```text
https://<worker-host>/tv-alert
```

The current ORB v1.1 alert logic is an integration source, not a claim that the strategy components are statistically validated.
