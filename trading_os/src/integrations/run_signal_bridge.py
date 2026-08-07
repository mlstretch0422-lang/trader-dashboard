import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.alert_bridge import build_signal_payload, send_signal
from src.integrations.data_provider import get_data_provider


def main():
    mode = (os.getenv("SIGNAL_BRIDGE_MODE") or "webhook").strip().lower()

    # Production-safe default: do not manufacture a LONG/SHORT candidate on a timer.
    # Real alert delivery is handled by serve_signal_bridge.py when TradingView posts
    # an authenticated /tv-alert event.
    if mode != "demo":
        print(
            "Signal Bridge is in webhook mode. No synthetic signal generated. "
            "Run serve_signal_bridge.py to receive TradingView events."
        )
        return

    provider = get_data_provider()
    df = provider.load()
    if df.empty:
        raise RuntimeError("No data available for demo signal generation")

    latest = df.iloc[-1]
    payload = build_signal_payload(
        df,
        side="long",
        entry_price=float(latest.get("close", 0.0)),
        confidence=0.8,
        note="DEMO ONLY — synthetic ORB signal candidate",
    )

    output_path = Path(__file__).resolve().parent / "latest_signal.json"
    output_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote demo signal payload to {output_path}")

    if (os.getenv("ALLOW_DEMO_DISCORD") or "false").lower() not in {"1", "true", "yes"}:
        print("Demo Discord delivery blocked. Set ALLOW_DEMO_DISCORD=true explicitly to send it.")
        return

    result = send_signal(payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
