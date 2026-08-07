# Integration setup

This project now supports a simple provider abstraction for market data.

## Local CSV data
Set:

```bash
export DATA_PROVIDER=csv
export DATA_CSV_PATH=/path/to/your.csv
```

## Alpaca data (future live/historical feed)
Set:

```bash
export DATA_PROVIDER=alpaca
export ALPACA_API_KEY=your_key
export ALPACA_SECRET_KEY=your_secret
```

## TradingView connection
TradingView itself is not directly accessible from this environment, but the project is now structured so it can be extended with a TradingView or broker connector without changing the strategy logic.

## TradingView webhook bridge (recommended alternative)

Use this when you want your TradingView alerts and indicator events reflected in replay/dashboard without direct account linking.

1. Start dashboard server:

```bash
cd /Users/masonstretch/Desktop/Trader\ Dashboard
/Users/masonstretch/Desktop/Trader\ Dashboard/.venv/bin/python trading_os/src/integrations/serve_dashboard.py
```

2. Configure TradingView alert webhook URL:

```text
http://127.0.0.1:8000/tv-alert
```

If you need TradingView cloud to reach your machine, expose this port with a secure tunnel (for example Cloudflare Tunnel) and use the HTTPS tunnel URL instead.

3. Use JSON alert message body in TradingView:

```json
{
	"symbol": "MES",
	"side": "LONG",
	"event": "orb_breakout",
	"price": 6123.25,
	"note": "Breakout confirmed above ORB high",
	"strategy": "ES_ORB_v1",
	"time": "{{timenow}}"
}
```

4. Regenerate report so replay snapshots ingest the alerts:

```bash
cd /Users/masonstretch/Desktop/Trader\ Dashboard
/Users/masonstretch/Desktop/Trader\ Dashboard/.venv/bin/python trading_os/src/integrations/generate_dashboard_report.py
```

Captured alerts are stored at:

```text
trading_os/src/integrations/tv_alerts.jsonl
```

You can inspect recent captured alerts at:

```text
http://127.0.0.1:8000/tv-alerts
```
