"""Minimal core utilities for the trading OS scaffold."""
from typing import Dict, List, Sequence


def classify_market_phase(
    closes: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    volumes: Sequence[float],
    lookback: int = 20,
) -> Dict[str, float]:
    """Classify the current market state into a simple trading-phase label."""
    if len(closes) < lookback + 2:
        return {"label": "insufficient_data", "score": 0.0}

    closes = list(closes)
    highs = list(highs)
    lows = list(lows)
    volumes = list(volumes)

    recent = closes[-lookback:]
    prior = closes[-lookback * 2 : -lookback] if len(closes) >= lookback * 2 else closes[:-1]
    if not prior:
        prior = closes[:-1]

    recent_avg = sum(recent) / len(recent)
    prior_avg = sum(prior) / len(prior)
    trend_strength = (recent_avg - prior_avg) / max(abs(prior_avg), 1e-9)

    recent_ranges = [h - l for h, l in zip(highs[-lookback:], lows[-lookback:])]
    avg_range = sum(recent_ranges) / len(recent_ranges)
    prev_range = (
        sum(recent_ranges[:-2]) / max(1, len(recent_ranges) - 2)
        if len(recent_ranges) > 2
        else avg_range
    )
    range_expansion = (avg_range - prev_range) / max(prev_range, 1e-9)

    recent_vol = volumes[-lookback:]
    prev_vol = volumes[-lookback * 2 : -lookback] if len(volumes) >= lookback * 2 else volumes[:-lookback]
    if not prev_vol:
        prev_vol = recent_vol
    avg_recent_vol = sum(recent_vol) / len(recent_vol)
    avg_prev_vol = sum(prev_vol) / len(prev_vol)
    vol_confidence = (avg_recent_vol - avg_prev_vol) / max(avg_prev_vol, 1e-9)

    last_close = closes[-1]
    first_close = recent[0]
    short_term_move = (last_close - first_close) / max(abs(first_close), 1e-9)

    score_up = 0.0
    score_down = 0.0

    if trend_strength > 0.01:
        score_up += 0.55
    elif trend_strength < -0.01:
        score_down += 0.55

    if short_term_move > 0.01:
        score_up += 0.2
    elif short_term_move < -0.01:
        score_down += 0.2

    if vol_confidence > 0.1:
        score_up += 0.1
        score_down += 0.1

    if range_expansion > 0.1:
        score_up += 0.1
        score_down += 0.1

    if abs(trend_strength) < 0.003 and abs(short_term_move) < 0.003:
        label = "chop"
        score = 0.8
    else:
        if score_up > score_down + 0.15:
            label = "strong_trend_up"
            score = score_up
        elif score_down > score_up + 0.15:
            label = "strong_trend_down"
            score = score_down
        elif score_up > 0.4 and score_down > 0.4:
            label = "reversal_candidate"
            score = min(score_up, score_down)
        else:
            label = "mean_reversion"
            score = max(score_up, score_down)

    return {
        "label": label,
        "score": round(score, 3),
        "trend_strength": round(trend_strength, 6),
        "range_expansion": round(range_expansion, 6),
        "vol_confidence": round(vol_confidence, 6),
    }


def get_version() -> str:
    """Return scaffold version."""
    return "0.1.0"


def describe() -> Dict[str, str]:
    """Return a minimal description of the system."""
    return {
        "name": "trading_os",
        "version": get_version(),
        "description": "Research-first trading operating system scaffold",
    }


def backtest_stub() -> Dict[str, float]:
    """A tiny placeholder backtest result so CI/tests can exercise the code.

    Replace with real backtest logic in `src/strategies`.
    """
    return {"net_profit": 0.0, "trades": 0}
