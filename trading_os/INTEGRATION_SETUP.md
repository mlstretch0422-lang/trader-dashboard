# Signal Bridge integration setup

The production-safe integration path is:

`TradingView alert -> authenticated Signal Bridge webhook -> alert history -> Discord webhook`

Scheduled market/news briefs are separate research-context messages and are never treated as trade authorization.

## 1. Local runtime config

From the repository root:

```bash
cp .env.example .env.local
```

Edit `.env.local` locally and set:

```text
DISCORD_WEBHOOK_URL=<new Discord webhook URL>
TV_WEBHOOK_SECRET=<a long random secret>
DASHBOARD_PORT=8000
SIGNAL_BRIDGE_MODE=webhook
```

`.env.local` is ignored by git. Never put webhook URLs or tokens in source files, commits, screenshots, or chat messages.

## 2. Start the dashboard + TradingView bridge

```bash
cd "$HOME/.copilot/repos/trader-dashboard"
set -a
source .env.local
set +a
python3 trading_os/src/integrations/serve_signal_bridge.py
```

Local dashboard:

```text
http://127.0.0.1:8000/index.html
```

Local TradingView endpoint:

```text
http://127.0.0.1:8000/tv-alert
```

TradingView cannot call localhost from the cloud. For real alerts, expose only this local service through a secure HTTPS tunnel and use the tunnel's HTTPS `/tv-alert` URL.

## 3. TradingView alert JSON

Every production TradingView alert must include the same `TV_WEBHOOK_SECRET` stored locally:

```json
{
  "secret": "YOUR_LOCAL_TV_WEBHOOK_SECRET",
  "symbol": "MES",
  "side": "LONG",
  "event": "entry",
  "price": 6123.25,
  "note": "Validated strategy event",
  "strategy": "SignalBridge",
  "time": "{{timenow}}"
}
```

The server checks the secret with constant-time comparison and removes it before writing alert history.

Recent accepted TradingView alerts:

```text
http://127.0.0.1:8000/tv-alerts
```

## 4. Scheduled Discord briefs on macOS

The launch agent no longer contains a Discord credential and no longer points at the old Desktop copy of the project.

Install/update it with:

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp "$HOME/.copilot/repos/trader-dashboard/trading_os/src/integrations/launchd_plist.plist" \
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
- Real Discord event alerts originate from accepted TradingView webhook events.

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
