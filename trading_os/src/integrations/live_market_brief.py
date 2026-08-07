import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.alert_bridge import build_signal_payload, send_signal
from src.integrations.data_provider import get_data_provider


def fetch_yahoo_quote(symbol: str = "ES=F") -> Dict[str, Any]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    data = response.json()
    result = data.get("chart", {}).get("result", [{}])[0]
    meta = result.get("meta", {})
    timestamps = result.get("timestamp", [])
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    last_close = closes[-1] if closes else meta.get("regularMarketPrice")
    return {
        "symbol": meta.get("symbol", symbol),
        "price": last_close,
        "high": meta.get("regularMarketDayHigh"),
        "low": meta.get("regularMarketDayLow"),
        "timestamp": timestamps[-1] if timestamps else None,
    }


def build_market_brief() -> Dict[str, Any]:
    provider = get_data_provider()
    df = provider.load()
    latest_bar = df.iloc[-1]
    fallback_price = float(latest_bar.get("close", 0.0))

    try:
        quote = fetch_yahoo_quote()
    except Exception:
        quote = {}

    payload = build_signal_payload(
        df,
        side="long",
        entry_price=float(quote.get("price", fallback_price)),
        confidence=0.85,
        note="Live market brief candidate",
    )
    payload["market_snapshot"]["live_price"] = float(quote.get("price", payload["market_snapshot"]["latest_close"]))
    payload["market_snapshot"]["live_high"] = quote.get("high")
    payload["market_snapshot"]["live_low"] = quote.get("low")
    return payload


def main():
    payload = build_market_brief()
    out_path = Path(__file__).resolve().parent / "latest_market_brief.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote market brief to {out_path}")
    result = send_signal(payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
