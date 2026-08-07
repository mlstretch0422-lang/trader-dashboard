"""Clean, modular implementation of the ORB retest strategy (Version 1.0).

This module exposes functions to compute ORB, filters, detect retest, and generate trades.
Use this as the canonical Python implementation to run tests and produce reproducible results.
"""
from typing import Dict, List
import pandas as pd

from src.system.core import classify_market_phase


def add_market_phase_features(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Annotate a price frame with a simple market-phase classification."""
    df = df.copy()
    df = df.sort_values("datetime").reset_index(drop=True)

    phase_labels = []
    phase_scores = []
    trend_strengths = []
    range_expansions = []
    vol_confidences = []

    for idx in range(len(df)):
        window = df.iloc[max(0, idx - lookback - 1):idx + 1]
        if len(window) < lookback + 2:
            phase_labels.append("insufficient_data")
            phase_scores.append(0.0)
            trend_strengths.append(0.0)
            range_expansions.append(0.0)
            vol_confidences.append(0.0)
            continue

        result = classify_market_phase(
            closes=window["close"],
            highs=window["high"],
            lows=window["low"],
            volumes=window["volume"],
            lookback=min(lookback, len(window) - 1),
        )
        phase_labels.append(result["label"])
        phase_scores.append(result["score"])
        trend_strengths.append(result.get("trend_strength", 0.0))
        range_expansions.append(result.get("range_expansion", 0.0))
        vol_confidences.append(result.get("vol_confidence", 0.0))

    df["market_phase"] = phase_labels
    df["market_phase_score"] = phase_scores
    df["market_phase_trend_strength"] = trend_strengths
    df["market_phase_range_expansion"] = range_expansions
    df["market_phase_vol_confidence"] = vol_confidences
    return df


def compute_orb(df: pd.DataFrame, orb_start_min: int, orb_end_min: int) -> Dict[pd.Timestamp, Dict]:
    """Compute ORB (high, low, mid) for each date in df.

    Returns a dict keyed by date -> {'orb_high', 'orb_low', 'orb_mid', 'orb_range'}
    """
    df = df.copy()
    df['dt'] = pd.to_datetime(df['datetime'])
    df['date'] = df['dt'].dt.date
    df['mins'] = df['dt'].dt.hour * 60 + df['dt'].dt.minute
    orb_map = {}
    for d, g in df.groupby('date'):
        seg = g[(g['mins'] >= orb_start_min) & (g['mins'] < orb_end_min)]
        if seg.empty:
            continue
        high = seg['high'].max()
        low = seg['low'].min()
        orb_map[d] = {'orb_high': float(high), 'orb_low': float(low), 'orb_mid': float((high+low)/2.0), 'orb_range': float(high-low)}
    return orb_map


def apply_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df['high'] + df['low'] + df['close']) / 3.0
    cum = (tp * df.get('volume', 1)).cumsum()
    v = cum / df.get('volume', pd.Series(1, index=df.index)).cumsum()
    return v


def generate_signals(
    df: pd.DataFrame,
    orb_map: Dict,
    orb_start_min: int,
    orb_end_min: int,
    use_vwap: bool = True,
    use_ema: bool = False,
    ema_len: int = 50,
    retest_mode: str = 'Midpoint',
    market_phase_filter: bool = False,
    market_phase_threshold: float = 0.0,
) -> pd.DataFrame:
    df = df.copy()
    df['dt'] = pd.to_datetime(df['datetime'])
    df['date'] = df['dt'].dt.date
    df['mins'] = df['dt'].dt.hour * 60 + df['dt'].dt.minute

    if use_vwap:
        df['vwap'] = apply_vwap(df)
    if use_ema:
        df['ema'] = df['close'].ewm(span=ema_len, adjust=False).mean()

    df = add_market_phase_features(df, lookback=6)

    trades = []
    # iterate days
    for d, g in df.groupby('date'):
        orb = orb_map.get(d)
        if not orb:
            continue
        orb_high = orb['orb_high']
        orb_low = orb['orb_low']
        orb_mid = orb['orb_mid']
        orb_done = True
        breakout_long = False
        breakout_short = False
        entry_pending = False
        entry_price = None
        entry_time = None

        # scan bars
        for _, row in g.iterrows():
            mins = row['mins']
            if orb_done and not breakout_long and not breakout_short:
                if row['close'] > orb_high:
                    breakout_long = True
                elif row['close'] < orb_low:
                    breakout_short = True

            if market_phase_filter:
                phase = row.get('market_phase')
                phase_score = row.get('market_phase_score', 0.0)
                if phase == 'chop' or (phase_score < market_phase_threshold and phase != 'strong_trend_up' and phase != 'strong_trend_down'):
                    continue

            # allow entries after orb_end_min
            if orb_done and mins >= orb_end_min:
                if breakout_long and not entry_pending:
                    # retest midpoint
                    if retest_mode == 'Midpoint':
                        if row['low'] <= orb_mid and row['close'] >= orb_mid:
                            entry_pending = True
                            entry_price = float(row['close'])
                            entry_time = row['dt']
                    else:
                        if row['close'] > orb_high:
                            entry_pending = True
                            entry_price = float(row['close'])
                            entry_time = row['dt']
                elif breakout_short and not entry_pending:
                    if retest_mode == 'Midpoint':
                        if row['high'] >= orb_mid and row['close'] <= orb_mid:
                            entry_pending = True
                            entry_price = float(row['close'])
                            entry_time = row['dt']
                    else:
                        if row['close'] < orb_low:
                            entry_pending = True
                            entry_price = float(row['close'])
                            entry_time = row['dt']

            # simple exit: close of next bar crossing midpoint again
            if entry_pending and entry_price is not None:
                if entry_price >= orb_mid:
                    # long
                    if row['low'] <= orb_mid and row['close'] >= orb_mid:
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': row['dt'],
                            'side': 'long',
                            'entry_price': entry_price,
                            'exit_price': float(row['close']),
                            'pnl_points': float(row['close'])-entry_price,
                            'market_phase': row.get('market_phase', 'unknown'),
                            'market_phase_score': float(row.get('market_phase_score', 0.0)),
                        })
                        entry_pending = False
                        entry_price = None
                else:
                    if row['high'] >= orb_mid and row['close'] <= orb_mid:
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': row['dt'],
                            'side': 'short',
                            'entry_price': entry_price,
                            'exit_price': float(row['close']),
                            'pnl_points': entry_price-float(row['close']),
                            'market_phase': row.get('market_phase', 'unknown'),
                            'market_phase_score': float(row.get('market_phase_score', 0.0)),
                        })
                        entry_pending = False
                        entry_price = None

    return pd.DataFrame(trades)


def calculate_trade_confidence(row: Dict) -> float:
    """Translate the market-phase score into a simple trade-confidence score."""
    phase = row.get('market_phase', 'unknown')
    score = float(row.get('market_phase_score', 0.0))

    if phase == 'strong_trend_up' or phase == 'strong_trend_down':
        return round(min(1.0, 0.6 + score / 2.0), 3)
    if phase == 'mean_reversion':
        return round(min(1.0, 0.55 + score / 4.0), 3)
    if phase == 'reversal_candidate':
        return round(min(1.0, 0.5 + score / 3.0), 3)
    return round(max(0.0, min(1.0, 0.3 + score / 10.0)), 3)


def summarize_regimes(trades: pd.DataFrame) -> Dict:
    """Summarize regime composition of the generated trades."""
    if isinstance(trades, list):
        trades = pd.DataFrame(trades)

    if trades.empty:
        return {'phase_counts': {}, 'avg_confidence': 0.0, 'phase_performance': {}}

    phase_counts = trades['market_phase'].fillna('unknown').value_counts().to_dict()
    avg_confidence = float(trades['trade_confidence'].mean()) if 'trade_confidence' in trades.columns else 0.0

    phase_performance = {}
    for phase, group in trades.groupby('market_phase'):
        pnl = float(group['pnl_points'].sum()) if 'pnl_points' in group.columns else 0.0
        wins = int((group['pnl_points'] > 0).sum()) if 'pnl_points' in group.columns else 0
        total = int(len(group))
        phase_performance[phase] = {
            'trades': total,
            'pnl': round(pnl, 3),
            'win_rate': round(wins / total, 3) if total else 0.0,
        }

    return {
        'phase_counts': phase_counts,
        'avg_confidence': round(avg_confidence, 3),
        'dominant_phase': max(phase_counts.items(), key=lambda item: item[1])[0] if phase_counts else 'none',
        'phase_performance': phase_performance,
    }


def summary_from_trades(trades) -> Dict:
    if isinstance(trades, list):
        trades = pd.DataFrame(trades)

    if trades.empty:
        return {'trades': 0, 'net': 0.0, 'win_rate': None, 'regime_summary': summarize_regimes(trades)}
    net = trades['pnl_points'].sum()
    wins = trades[trades['pnl_points']>0]
    if 'trade_confidence' not in trades.columns:
        trades = trades.copy()
        trades['trade_confidence'] = trades.apply(calculate_trade_confidence, axis=1)
    return {
        'trades': len(trades),
        'net': float(net),
        'win_rate': len(wins)/len(trades),
        'regime_summary': summarize_regimes(trades),
    }
