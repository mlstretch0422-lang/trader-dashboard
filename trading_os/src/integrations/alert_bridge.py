import json
import os
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


def build_signal_payload(
    df: pd.DataFrame,
    side: str,
    entry_price: float,
    confidence: float,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a serializable research payload from market data."""
    if df.empty:
        raise ValueError("df must not be empty")

    latest = df.iloc[-1]
    return {
        "side": side,
        "entry_price": float(entry_price),
        "confidence": round(float(confidence), 3),
        "note": note or "ORB signal candidate",
        "market_snapshot": {
            "timestamp": str(latest["datetime"]),
            "latest_close": float(latest["close"]),
            "latest_high": float(latest["high"]),
            "latest_low": float(latest["low"]),
            "volume": int(latest.get("volume", 0)),
        },
    }


def build_discord_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a legacy research payload into a Discord webhook body."""
    message = (
        "RESEARCH SIGNAL CANDIDATE — NOT TRADE AUTHORIZATION\n"
        f"Side: {str(payload.get('side') or 'wait').upper()}\n"
        f"Entry: {payload.get('entry_price')}\n"
        f"Confidence: {payload.get('confidence')}\n"
        f"Note: {payload.get('note') or 'No note'}\n"
        f"Close: {(payload.get('market_snapshot') or {}).get('latest_close')}"
    )
    return {"content": message}


def build_tradingview_discord_message(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Render a normalized TradingView webhook event for Discord."""
    event = str(alert.get("event") or "alert").replace("_", " ").upper()
    side = str(alert.get("side") or "WAIT").upper()
    symbol = str(alert.get("symbol") or "MES").upper()
    price = alert.get("price")
    strategy = str(alert.get("strategy") or "TradingView")
    note = str(alert.get("note") or "TradingView alert")
    event_time = str(alert.get("time") or alert.get("received_at") or "")

    lines = [
        f"SIGNAL BRIDGE | {event}",
        f"{symbol} | {side}",
    ]
    if price is not None:
        lines.append(f"Price: {price}")
    lines.extend(
        [
            f"Strategy: {strategy}",
            f"Note: {note}",
        ]
    )
    if event_time:
        lines.append(f"Time: {event_time}")
    return {"content": "\n".join(lines)}


def post_discord_message(
    message: Dict[str, Any], webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Post a Discord webhook message without logging or returning the secret URL."""
    webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "skipped", "reason": "no_webhook_configured"}

    body = json.dumps(message).encode("utf-8")
    request = Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "SignalBridge/1.0"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            status = int(getattr(response, "status", 204))
        return {"status": "sent", "http_status": status}
    except HTTPError as exc:
        return {"status": "error", "reason": f"discord_http_{exc.code}"}
    except URLError as exc:
        return {"status": "error", "reason": f"discord_network_error: {exc.reason}"}
    except Exception as exc:
        return {"status": "error", "reason": f"discord_post_error: {type(exc).__name__}"}


def send_signal(payload: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Send a legacy research signal candidate to Discord when explicitly called."""
    result = post_discord_message(build_discord_message(payload), webhook_url=webhook_url)
    return {**result, "payload": payload}


def send_tradingview_alert(
    alert: Dict[str, Any], webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Forward a real normalized TradingView webhook event to Discord."""
    return post_discord_message(
        build_tradingview_discord_message(alert), webhook_url=webhook_url
    )
