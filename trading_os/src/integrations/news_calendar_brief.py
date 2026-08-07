import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.live_market_brief import build_market_brief


def fetch_news_headlines(symbol: str = "SPY") -> List[Dict[str, Any]]:
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&quotesCount=0&newsCount=5"
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    data = response.json()
    news = []
    for item in data.get("news", [])[:5]:
        news.append({
            "title": item.get("title"),
            "publisher": item.get("publisher"),
            "link": item.get("link"),
            "provider": item.get("provider"),
        })
    return news


def build_news_calendar_brief() -> Dict[str, Any]:
    market_payload = build_market_brief()
    headlines = fetch_news_headlines("SPY")
    mode = (os.getenv("RUN_MODE") or "news").lower()
    return {
        "type": "news_calendar_brief",
        "mode": mode,
        "generated_at": datetime.utcnow().isoformat(),
        "market_snapshot": market_payload["market_snapshot"],
        "headline_summary": {
            "count": len(headlines),
            "items": headlines,
        },
        "trade_idea": {
            "bias": "long" if market_payload["market_snapshot"]["live_price"] >= market_payload["market_snapshot"]["latest_close"] else "short",
            "reason": "Momentum remains above the prior close and headline flow is being monitored for continuation or reversal.",
        },
        "economic_context": {
            "note": "Live economic calendar support can be added next using a dedicated calendar source or API.",
        },
    }


def main():
    payload = build_news_calendar_brief()
    out_path = Path(__file__).resolve().parent / "latest_news_calendar_brief.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote news/calendar brief to {out_path}")

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook_url:
        message = {
            "content": (
                f"News + Calendar Brief [{payload['mode'].upper()}]\n"
                f"Bias: {payload['trade_idea']['bias'].upper()}\n"
                f"Live price: {payload['market_snapshot']['live_price']}\n"
                f"Headlines: {payload['headline_summary']['count']}"
            )
        }
        try:
            requests.post(webhook_url, json=message, timeout=10)
        except Exception as exc:
            print(f"Discord post failed: {exc}")


if __name__ == "__main__":
    main()
