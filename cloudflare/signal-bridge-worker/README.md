# Signal Bridge hosted webhook worker

This Worker removes the Mac/quick-tunnel dependency from production alert delivery and now hosts the first durable data APIs used by the Premium OS.

Current paths:

`TradingView -> Cloudflare Worker -> Discord + D1 signal ledger`

`Discord / future capture tools -> authenticated journal ingest -> D1 private journal ledger -> reviewed Premium OS entries`

The existing local Signal Bridge server remains useful for local dashboard/testing, but Discord alert delivery no longer depends on the Mac staying awake once this Worker is deployed.

## Security model

- `DISCORD_WEBHOOK_URL` is stored only as an encrypted Cloudflare Worker secret.
- TradingView `/tv-alert` requests are accepted only from TradingView's published webhook source IP addresses.
- TradingView alert JSON contains no password or webhook credential.
- `/test` is separate and requires the `SIGNAL_BRIDGE_TEST_TOKEN` bearer token.
- Journal `POST /journal` requires a separate `JOURNAL_INGEST_TOKEN` bearer token.
- Journal entries default to `PRIVATE`; public `GET /journal` returns only rows explicitly marked `PUBLISHED`.
- Request bodies are JSON-only and capped at 16 KiB.
- Side/event/result values are validated and text fields are length-limited.
- Discord delivery runs asynchronously so TradingView receives a response quickly.

Published TradingView webhook IPs used by the Worker:

- `52.89.214.238`
- `34.212.75.30`
- `54.218.53.128`
- `52.32.178.7`

Re-check TradingView's current webhook documentation before changing this allowlist.

## Deploy from the repository

From the repository root, after Cloudflare authentication and after loading `.env.local`:

```bash
set -a
source .env.local
set +a
TMP_SECRETS="$(mktemp)"
chmod 600 "$TMP_SECRETS"
printf 'DISCORD_WEBHOOK_URL=%s\nSIGNAL_BRIDGE_TEST_TOKEN=%s\nJOURNAL_INGEST_TOKEN=%s\n' \
  "$DISCORD_WEBHOOK_URL" "$TV_WEBHOOK_SECRET" "$JOURNAL_INGEST_TOKEN" > "$TMP_SECRETS"
npx wrangler deploy \
  --config cloudflare/signal-bridge-worker/wrangler.toml \
  --secrets-file "$TMP_SECRETS"
npx wrangler d1 migrations apply DB \
  --remote \
  --config cloudflare/signal-bridge-worker/wrangler.toml
rm -f "$TMP_SECRETS"
```

The initial deployment uses the stable Cloudflare `workers.dev` route assigned to the Worker. A custom domain should replace `workers.dev` before Signal Bridge is treated as business-critical production infrastructure.

## Health check

```text
GET https://<worker-host>/health
```

Worker v1.2 reports the alert-history binding plus journal storage and whether the private ingest token is configured.

## Signal endpoints

- `POST /tv-alert` — TradingView-only production alert receiver.
- `POST /test` — authenticated infrastructure test.
- `GET /events` — public normalized production event history; TEST events hidden by default.

## Journal endpoints

- `GET /journal?limit=25` — public published journal entries only.
- `GET /journal?symbol=MES` — filter published entries by symbol.
- `GET /journal?result=WIN` — filter published entries by result.
- `GET /journal?setup=ORB%20retest` — filter published entries by exact normalized setup label.
- `POST /journal` — authenticated journal ingestion. Defaults to `visibility=PRIVATE` and `review_status=RAW`.

Example private journal ingest:

```bash
curl -sS -X POST "https://<worker-host>/journal" \
  -H "Authorization: Bearer $JOURNAL_INGEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source":"discord",
    "symbol":"MES",
    "side":"LONG",
    "strategy":"Mason ORB",
    "setup":"ORB retest",
    "result":"OPEN",
    "raw_text":"Short-form journal note preserved exactly as written.",
    "tags":["retest","morning"],
    "visibility":"PRIVATE"
  }'
```

The API intentionally keeps `source_ref` private. Public journal responses expose only published normalized content, not Discord message links or private source references.

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
