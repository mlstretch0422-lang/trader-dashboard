import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.alert_bridge import post_discord_message
from src.integrations.live_market_brief import build_market_brief


def fetch_news_headlines(symbol: str = "SPY") -> List[Dict[str, Any]]:
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={quote(symbol)}&quotesCount=0&newsCount=5"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    news = []
    for item in data.get("news", [])[:5]:
        news.append(
            {
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "provider": item.get("provider"),
            }
        )
    return news


def build_news_calendar_brief() -> Dict[str, Any]:
    market_payload = build_market_brief()
    try:
        headlines = fetch_news_headlines("SPY")
        news_status = "ok"
    except Exception as exc:
        headlines = []
        news_status = f"unavailable:{type(exc).__name__}"

    mode = (os.getenv("RUN_MODE") or "news").lower()
    context_direction = (
        "long"
        if market_payload["market_snapshot"]["live_price"]
        >= market_payload["market_snapshot"]["latest_close"]
        else "short"
    )
    return {
        "type": "news_calendar_brief",
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market_snapshot": market_payload["market_snapshot"],
        "headline_summary": {
            "status": news_status,
            "count": len(headlines),
            "items": headlines,
        },
        "context": {
            "direction": context_direction,
            "note": "Price context only; headline count is informational and is not an economic-calendar filter.",
        },
        "disclaimer": "Research context only. Not trade authorization or a red-news filter.",
    }


def main():
    payload = build_news_calendar_brief()
    out_path = Path(__file__).resolve().parent / "latest_news_calendar_brief.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote news/calendar brief to {out_path}")

    message = {
        "content": (
            f"SIGNAL BRIDGE NEWS BRIEF [{payload['mode'].upper()}]\n"
            "RESEARCH CONTEXT — NOT A TRADE ALERT / NOT A RED-NEWS FILTER\n"
            f"Price context: {payload['context']['direction'].upper()}\n"
            f"Live price: {payload['market_snapshot']['live_price']}\n"
            f"Headlines retrieved: {payload['headline_summary']['count']}"
        )
    }
    result = post_discord_message(message)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
