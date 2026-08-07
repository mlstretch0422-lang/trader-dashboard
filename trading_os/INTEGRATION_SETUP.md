# Signal Bridge integration setup

The preferred hosted alert path is:

`TradingView alert -> Cloudflare Worker -> Discord webhook`

The local Mac bridge remains available for development and local dashboard work:

`TradingView/curl -> local Signal Bridge server -> Discord webhook`

Scheduled market/news briefs are separate research-context messages and are never treated as trade authorization.

## 1. Local runtime config

From the repository root:

```bash
cp .env.example .env.local
```

Edit `.env.local` locally and set:

```text
DISCORD_WEBHOOK_URL=<new Discord webhook URL>
TV_WEBHOOK_SECRET=<a long random local test token>
DASHBOARD_PORT=8000
SIGNAL_BRIDGE_MODE=webhook
```

`.env.local` is ignored by git. Never put webhook URLs or tokens in source files, commits, screenshots, or chat messages.

## 2. Hosted production receiver

The hosted receiver lives in:

```text
cloudflare/signal-bridge-worker/
```

It is designed so live alert delivery does not depend on the Mac staying awake or a temporary `trycloudflare.com` tunnel remaining open.

Security behavior:

- Discord webhook URL is a Cloudflare Worker secret.
- `/tv-alert` accepts requests only from TradingView's published webhook source IPs.
- TradingView alert JSON contains no password or webhook credential.
- `/test` requires a private bearer token for manual end-to-end tests.
- request body size, content type, side/event values, and field lengths are validated.
- Discord forwarding is asynchronous so TradingView receives an acknowledgement quickly.

See `cloudflare/signal-bridge-worker/README.md` for deployment commands and the current TradingView JSON payloads.

The initial stable route can use Cloudflare `workers.dev`. A custom domain should replace it before Signal Bridge is treated as business-critical production infrastructure.

## 3. TradingView alert JSON

Hosted LONG payload:

```json
{"symbol":"{{ticker}}","side":"LONG","event":"entry","price":"{{close}}","strategy":"ES/MES ORB v1.1","note":"Long Setup Ready","time":"{{timenow}}"}
```

Hosted SHORT payload:

```json
{"symbol":"{{ticker}}","side":"SHORT","event":"entry","price":"{{close}}","strategy":"ES/MES ORB v1.1","note":"Short Setup Ready","time":"{{timenow}}"}
```

Hosted webhook URL:

```text
https://<worker-host>/tv-alert
```

The current ORB v1.1 alert logic is an integration source only; this setup does not promote its strategy components to statistically verified status.

## 4. Local development bridge

Start the local dashboard + bridge:

```bash
set -a
source .env.local
set +a
PYTHON=".venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"
PYTHONPATH=trading_os "$PYTHON" trading_os/src/integrations/serve_signal_bridge.py
```

Local dashboard:

```text
http://127.0.0.1:8000/index.html
```

Local webhook:

```text
http://127.0.0.1:8000/tv-alert
```

TradingView cannot call localhost directly. A quick Cloudflare tunnel is acceptable for temporary integration tests only; its random URL changes when the process restarts and should not be treated as the production receiver.

## 5. Scheduled Discord briefs on macOS

The launch agent contains no Discord credential and resolves the repository dynamically.

Install/update it with:

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp "$(pwd)/trading_os/src/integrations/launchd_plist.plist" \
   "$HOME/Library/LaunchAgents/com.signalbridge.dailybrief.plist"
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.signalbridge.dailybrief.plist" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.signalbridge.dailybrief.plist"
launchctl kickstart -k "gui/$(id -u)/com.signalbridge.dailybrief"
```

Logs:

```text
/tmp/signal-bridge-launchd.out.log
/tmp/signal-bridge-launchd.err.log
```

## Safety behavior

- `run_signal_bridge.py` defaults to webhook mode and generates no synthetic LONG/SHORT signal.
- Demo signal generation requires `SIGNAL_BRIDGE_MODE=demo`.
- Demo delivery to Discord additionally requires `ALLOW_DEMO_DISCORD=true`.
- Scheduled daily/news messages are labeled research context, not trade alerts.
- Hosted real Discord event alerts originate from accepted TradingView webhook events.

## Data providers

Local CSV:

```bash
export DATA_PROVIDER=csv
export DATA_CSV_PATH=/path/to/your.csv
```

Alpaca remains an optional future provider:

```bash
export DATA_PROVIDER=alpaca
export ALPACA_API_KEY=your_key
export ALPACA_SECRET_KEY=your_secret
```
