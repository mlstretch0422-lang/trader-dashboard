# Shareable Dashboard Snapshot

This folder contains a standalone snapshot of the premium dashboard for sharing feedback.

## Files
- `signal_bridge_premium_shareable.html`: standalone dashboard with embedded report data
- `signal_bridge_report.json`: raw snapshot data used in the shared page

## How to regenerate
From workspace root:

```bash
/Users/masonstretch/Desktop/Trader Dashboard/.venv/bin/python trading_os/src/integrations/generate_dashboard_report.py
/Users/masonstretch/Desktop/Trader Dashboard/.venv/bin/python trading_os/src/integrations/export_shareable_dashboard.py
```

## Sharing
Send `signal_bridge_premium_shareable.html` directly.
Anyone can open it in a browser without running a local server.
