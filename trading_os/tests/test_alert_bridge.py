import pandas as pd

from src.integrations.alert_bridge import (
    build_discord_message,
    build_signal_payload,
    build_tradingview_discord_message,
    post_discord_message,
)


def test_build_signal_payload_includes_entry_candidate():
    df = pd.DataFrame(
        [
            {
                "datetime": pd.Timestamp("2024-01-02 09:30"),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1200,
            },
            {
                "datetime": pd.Timestamp("2024-01-02 09:31"),
                "open": 100.5,
                "high": 102.0,
                "low": 100.0,
                "close": 101.5,
                "volume": 1400,
            },
        ]
    )

    payload = build_signal_payload(df, side="long", entry_price=101.5, confidence=0.8)
    discord_message = build_discord_message(payload)

    assert payload["side"] == "long"
    assert payload["entry_price"] == 101.5
    assert payload["confidence"] >= 0.75
    assert payload["market_snapshot"]["latest_close"] == 101.5
    assert "NOT TRADE AUTHORIZATION" in discord_message["content"]


def test_tradingview_message_preserves_real_event_fields():
    alert = {
        "symbol": "MES",
        "side": "LONG",
        "event": "entry",
        "price": 6123.25,
        "strategy": "SignalBridge",
        "note": "Validated strategy event",
        "time": "2026-08-07T13:30:00Z",
    }
    message = build_tradingview_discord_message(alert)["content"]
    assert "SIGNAL BRIDGE | ENTRY" in message
    assert "MES | LONG" in message
    assert "6123.25" in message
    assert "Validated strategy event" in message


def test_discord_post_skips_without_webhook(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    result = post_discord_message({"content": "test"})
    assert result == {"status": "skipped", "reason": "no_webhook_configured"}
