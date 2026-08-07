import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.alert_bridge import post_discord_message
from src.integrations.live_market_brief import build_market_brief


def build_daily_brief() -> Dict[str, Any]:
    market_payload = build_market_brief()
    mode = (os.getenv("RUN_MODE") or "daily").lower()
    if mode == "pre":
        reason = "Pre-market price/structure context; monitor the opening sequence."
    elif mode == "open":
        reason = "Opening drive context is being monitored around the opening range."
    elif mode == "midday":
        reason = "Midday context check into the NY AM close."
    else:
        reason = "Market context snapshot generated from the configured live-price provider."

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
        "context": {
            "direction": "long"
            if market_payload["market_snapshot"]["live_price"]
            >= market_payload["market_snapshot"]["latest_close"]
            else "short",
            "reason": reason,
        },
        "disclaimer": "Research market brief only. Not trade authorization.",
    }
    return payload


def main():
    payload = build_daily_brief()
    out_path = Path(__file__).resolve().parent / "latest_daily_brief.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote daily brief to {out_path}")

    message = {
        "content": (
            f"SIGNAL BRIDGE MARKET BRIEF [{payload['mode'].upper()}]\n"
            "RESEARCH CONTEXT — NOT A TRADE ALERT\n"
            f"Context: {payload['context']['direction'].upper()}\n"
            f"Live price: {payload['market_snapshot']['live_price']}\n"
            f"Reference close: {payload['market_snapshot']['latest_close']}\n"
            f"Reason: {payload['context']['reason']}"
        )
    }
    result = post_discord_message(message)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
