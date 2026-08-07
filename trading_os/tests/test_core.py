from src.system.core import get_version, backtest_stub, classify_market_phase


def test_get_version():
    v = get_version()
    assert isinstance(v, str)


def test_backtest_stub():
    r = backtest_stub()
    assert isinstance(r, dict)
    assert "net_profit" in r and "trades" in r


def test_classify_market_phase_detects_uptrend():
    closes = [100 + i for i in range(12)]
    highs = [c + 1 for c in closes]
    lows = [c - 1 for c in closes]
    volumes = [1000 + i * 50 for i in range(12)]

    result = classify_market_phase(closes, highs, lows, volumes, lookback=6)

    assert result["label"] == "strong_trend_up"
    assert result["score"] >= 0.5


def test_classify_market_phase_detects_chop():
    closes = [100] * 20
    highs = [101] * 20
    lows = [99] * 20
    volumes = [1000] * 20

    result = classify_market_phase(closes, highs, lows, volumes, lookback=6)

    assert result["label"] == "chop"
    assert result["score"] >= 0.7
