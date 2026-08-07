import json
import os
from typing import Any, Dict, Optional

import pandas as pd


def build_signal_payload(df: pd.DataFrame, side: str, entry_price: float, confidence: float, note: Optional[str] = None) -> Dict[str, Any]:
    """Build a serializable payload for a TradingView/Discord/alert bridge."""
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
    """Convert a structured payload into the Discord webhook body format."""
    message = (
        f"ORB Signal\n"
        f"Side: {payload['side'].upper()}\n"
        f"Entry: {payload['entry_price']}\n"
        f"Confidence: {payload['confidence']}\n"
        f"Note: {payload['note']}\n"
        f"Close: {payload['market_snapshot']['latest_close']}"
    )
    return {"content": message}


def send_signal(payload: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Emit a signal payload to a webhook if configured."""
    if not webhook_url:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "skipped", "reason": "no_webhook_configured", "payload": payload}

    try:
        import requests
    except ImportError as exc:
        return {"status": "error", "reason": f"requests_not_installed: {exc}", "payload": payload}

    message = build_discord_message(payload)
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        return {"status": "sent", "payload": payload, "http_status": response.status_code}
    except Exception as exc:
        return {"status": "error", "reason": str(exc), "payload": payload}
