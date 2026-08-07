import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.alert_bridge import send_signal
from src.integrations.live_market_brief import build_market_brief


def build_daily_brief() -> Dict[str, Any]:
    market_payload = build_market_brief()
    mode = (os.getenv("RUN_MODE") or "daily").lower()
    if mode == "pre":
        reason = "Pre-market bias based on live price and structure; monitor for the first breakout.",
    elif mode == "open":
        reason = "Opening drive is being evaluated for continuation or fade around the opening range.",
    elif mode == "midday":
        reason = "Midday session check: watch for trend continuation or reversal into the NY AM close.",
    else:
        reason = "Momentum and live price are holding above the prior close; monitor breakout continuation.",

    payload = {
        "type": "daily_brief",
        "mode": mode,
        "summary": {
            "side": market_payload["side"],
            "entry_price": market_payload["entry_price"],
            "confidence": market_payload["confidence"],
            "note": market_payload["note"],
        },
        "market_snapshot": market_payload["market_snapshot"],
        "trade_idea": {
            "bias": "long" if market_payload["market_snapshot"]["live_price"] >= market_payload["market_snapshot"]["latest_close"] else "short",
            "reason": reason,
        },
        "economic_context": {
            "source": "Yahoo Finance live quote",
            "note": "Economic calendar and news can be layered in next once live calendar access is available.",
        },
    }
    return payload


def main():
    payload = build_daily_brief()
    out_path = Path(__file__).resolve().parent / "latest_daily_brief.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote daily brief to {out_path}")

    message = {
        "content": (
            f"Daily Brief [{payload['mode'].upper()}]\n"
            f"Bias: {payload['trade_idea']['bias'].upper()}\n"
            f"Entry: {payload['summary']['entry_price']}\n"
            f"Confidence: {payload['summary']['confidence']}\n"
            f"Live price: {payload['market_snapshot']['live_price']}\n"
            f"Reason: {payload['trade_idea']['reason']}"
        )
    }
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        try:
            requests.post(webhook_url, json=message, timeout=10)
        except Exception as exc:
            print(f"Discord post failed: {exc}")
    else:
        print("No webhook configured; daily brief saved locally only")


if __name__ == "__main__":
    main()
