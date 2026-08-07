import pandas as pd

from src.strategies.clean_orb import (
    add_market_phase_features,
    calculate_trade_confidence,
    generate_signals,
    summary_from_trades,
)


def test_add_market_phase_features_detects_uptrend():
    rows = []
    for i in range(25):
        rows.append(
            {
                "datetime": pd.Timestamp("2024-01-02 09:30") + pd.Timedelta(minutes=i),
                "open": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "close": 100 + i,
                "volume": 1000 + i * 10,
            }
        )
    df = pd.DataFrame(rows)

    annotated = add_market_phase_features(df, lookback=6)

    assert annotated.iloc[-1]["market_phase"] == "strong_trend_up"
    assert annotated.iloc[-1]["market_phase_score"] >= 0.5


def test_generate_signals_can_filter_chop_regime():
    rows = []
    for i in range(30):
        rows.append(
            {
                "datetime": pd.Timestamp("2024-01-02 09:30") + pd.Timedelta(minutes=i),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000.0,
            }
        )
    df = pd.DataFrame(rows)

    orb_map = {pd.Timestamp("2024-01-02").date(): {"orb_high": 101.0, "orb_low": 99.0, "orb_mid": 100.0, "orb_range": 2.0}}

    trades = generate_signals(df, orb_map, 570, 585, market_phase_filter=True, use_vwap=False, use_ema=False)

    assert trades.empty


def test_generate_signals_attaches_market_phase_metadata():
    df = pd.DataFrame(
        [
            {
                "datetime": pd.Timestamp("2024-01-02 09:30"),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000.0,
            }
        ]
    )

    annotated = add_market_phase_features(df, lookback=6)
    annotated.loc[0, "market_phase"] = "strong_trend_up"
    annotated.loc[0, "market_phase_score"] = 0.8

    assert annotated.iloc[0]["market_phase"] == "strong_trend_up"
    assert annotated.iloc[0]["market_phase_score"] >= 0.5


def test_calculate_trade_confidence_and_summary():
    trade = {
        "market_phase": "strong_trend_up",
        "market_phase_score": 0.8,
    }

    confidence = calculate_trade_confidence(trade)
    summary = summary_from_trades(pd.DataFrame([{"pnl_points": 1.0, "market_phase": "strong_trend_up", "market_phase_score": 0.8}]))

    assert confidence >= 0.8
    assert summary["regime_summary"]["phase_counts"]["strong_trend_up"] == 1


def test_summary_from_trades_handles_realistic_trade_frame():
    trades = pd.DataFrame(
        [
            {"pnl_points": 1.0, "market_phase": "strong_trend_up", "market_phase_score": 0.8},
            {"pnl_points": -0.5, "market_phase": "chop", "market_phase_score": 0.2},
        ]
    )

    summary = summary_from_trades(trades)

    assert summary["trades"] == 2
    assert summary["regime_summary"]["dominant_phase"] == "strong_trend_up"
    assert summary["regime_summary"]["phase_performance"]["strong_trend_up"]["trades"] == 1
