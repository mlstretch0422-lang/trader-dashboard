#!/usr/bin/env python3
"""
Stop-Loss Alternative Tester
Purpose: Test different SL placements against reconstructed trades to find the optimal exit strategy.

Once OHLC data is available, run this to compare:
- SL at ORB_HIGH/LOW (current)
- SL at ORB_MID (tighter)
- SL at Entry ± 1 ATR (dynamic)
- SL at Entry ± fixed pts (fixed)
- Time-based SL (exit after N minutes)

Usage:
    python3 test_sl_alternatives.py --ohlc <path> --trades <path> --output <dir>
"""

import sys
from pathlib import Path
import pandas as pd
import json
from typing import List, Tuple

# Import existing metrics
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'strat' / 'src'))
from strat.metrics import compute_metrics


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute ATR(period) from OHLC DataFrame."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def compute_orb(df: pd.DataFrame, orb_start_min: int, orb_end_min: int) -> dict:
    """Compute ORB for the date."""
    if 'mins' in df.columns:
        orb_section = df[(df['mins'] >= orb_start_min) & (df['mins'] < orb_end_min)]
    else:
        # Fallback: use first 15 minutes of data
        orb_section = df.iloc[:15]
    
    if orb_section.empty:
        return None
    
    return {
        'orb_high': orb_section['high'].max(),
        'orb_low': orb_section['low'].min(),
        'orb_mid': (orb_section['high'].max() + orb_section['low'].min()) / 2.0,
        'orb_range': orb_section['high'].max() - orb_section['low'].min(),
    }


def test_sl_variant(
    trades: pd.DataFrame,
    ohlc: pd.DataFrame,
    variant_name: str,
    sl_calc_func,
) -> dict:
    """
    Test a specific SL placement variant.
    
    Args:
        trades: Reconstructed trades with entry_time, entry_price, exit_price, direction, qty, etc.
        ohlc: OHLC data with datetime index or 'datetime' column.
        variant_name: Name of the variant (e.g., "SL_ORB_LOW", "SL_MID").
        sl_calc_func: Function(trade_row, ohlc_on_day) -> (stop_price).
    
    Returns:
        dict with metrics for this variant.
    """
    
    # Ensure datetime columns exist
    trades_copy = trades.copy()
    if not pd.api.types.is_datetime64_any_dtype(trades_copy['entry_time']):
        trades_copy['entry_time'] = pd.to_datetime(trades_copy['entry_time'])
    if not pd.api.types.is_datetime64_any_dtype(trades_copy['exit_time']):
        trades_copy['exit_time'] = pd.to_datetime(trades_copy['exit_time'])
    
    if not pd.api.types.is_datetime64_any_dtype(ohlc.index):
        if 'datetime' in ohlc.columns:
            ohlc = ohlc.set_index(pd.to_datetime(ohlc['datetime']))
        else:
            ohlc.index = pd.to_datetime(ohlc.index)
    
    # For each trade, compute the new exit price based on SL variant
    new_exit_prices = []
    new_pnls = []
    
    for _, trade in trades_copy.iterrows():
        entry_date = trade['entry_time'].date()
        
        # Get OHLC for entry date
        day_ohlc = ohlc[ohlc.index.date == entry_date]
        if day_ohlc.empty:
            # Use existing exit if no OHLC available
            new_exit_prices.append(trade['exit_price'])
            new_pnls.append(trade.get('realized_pnl_usd', 0))
            continue
        
        # Compute SL for this trade
        try:
            stop_price = sl_calc_func(trade, day_ohlc)
        except Exception as e:
            # Fallback to original
            new_exit_prices.append(trade['exit_price'])
            new_pnls.append(trade.get('realized_pnl_usd', 0))
            continue
        
        # Assume trade was hit at stop if it would have been
        # (simplified: if actual low/high reached, use stop; else use actual exit)
        entry_price = trade['entry_price']
        direction = trade.get('direction', 'Long')
        qty = trade.get('qty', 1)
        multiplier = trade.get('contract_multiplier', 50)
        
        # For now, assume trade got hit at stop or at original exit, whichever is worse for the strategy
        if direction == 'Long':
            # Long: stop is below; if price went below stop, exit at stop
            low_price = day_ohlc['low'].min()
            if low_price <= stop_price:
                exit_price = stop_price
            else:
                exit_price = trade['exit_price']
            pnl_points = (exit_price - entry_price) * qty
        else:
            # Short: stop is above; if price went above stop, exit at stop
            high_price = day_ohlc['high'].max()
            if high_price >= stop_price:
                exit_price = stop_price
            else:
                exit_price = trade['exit_price']
            pnl_points = (entry_price - exit_price) * qty
        
        pnl_usd = pnl_points * multiplier
        new_exit_prices.append(exit_price)
        new_pnls.append(pnl_usd)
    
    # Create modified trades DataFrame
    modified_trades = trades_copy.copy()
    modified_trades['exit_price'] = new_exit_prices
    modified_trades['realized_pnl_usd'] = new_pnls
    
    # Compute metrics
    metrics = compute_metrics(modified_trades)
    metrics['variant_name'] = variant_name
    
    return metrics


def sl_orb_low(trade, ohlc_day):
    """SL at ORB_LOW for longs, ORB_HIGH for shorts."""
    orb = compute_orb(ohlc_day, 480, 495)
    if not orb:
        raise ValueError("Cannot compute ORB")
    
    direction = trade.get('direction', 'Long')
    if direction == 'Long':
        return orb['orb_low']
    else:
        return orb['orb_high']


def sl_orb_mid(trade, ohlc_day):
    """SL at ORB_MID (tighter)."""
    orb = compute_orb(ohlc_day, 480, 495)
    if not orb:
        raise ValueError("Cannot compute ORB")
    
    direction = trade.get('direction', 'Long')
    if direction == 'Long':
        return orb['orb_mid']
    else:
        return orb['orb_mid']


def sl_fixed_points(trade, ohlc_day, points: float = 5.0):
    """SL at Entry ± fixed points."""
    entry = trade['entry_price']
    direction = trade.get('direction', 'Long')
    if direction == 'Long':
        return entry - points
    else:
        return entry + points


def sl_atr_multiple(trade, ohlc_day, atr_mult: float = 1.0):
    """SL at Entry ± ATR(14) × multiple."""
    entry = trade['entry_price']
    direction = trade.get('direction', 'Long')
    
    atr = compute_atr(ohlc_day, period=14)
    atr_val = atr.iloc[-1]
    if pd.isna(atr_val) or atr_val == 0:
        atr_val = 5.0  # Fallback
    
    if direction == 'Long':
        return entry - (atr_val * atr_mult)
    else:
        return entry + (atr_val * atr_mult)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test alternative SL placements against reconstructed trades.'
    )
    parser.add_argument('--ohlc', type=Path, required=True, help='OHLC CSV file.')
    parser.add_argument('--trades', type=Path, required=True, help='Reconstructed trades CSV.')
    parser.add_argument('--output', type=Path, default=Path('outputs'),
                        help='Output directory.')
    
    args = parser.parse_args()
    
    # Load data
    ohlc = pd.read_csv(args.ohlc)
    trades = pd.read_csv(args.trades, parse_dates=['entry_time', 'exit_time'])
    
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Define SL variants to test
    variants = [
        ('SL_ORB_EDGE', lambda t, o: sl_orb_low(t, o)),
        ('SL_ORB_MID', lambda t, o: sl_orb_mid(t, o)),
        ('SL_FIXED_5PTS', lambda t, o: sl_fixed_points(t, o, points=5.0)),
        ('SL_FIXED_10PTS', lambda t, o: sl_fixed_points(t, o, points=10.0)),
        ('SL_ATR1X', lambda t, o: sl_atr_multiple(t, o, atr_mult=1.0)),
        ('SL_ATR2X', lambda t, o: sl_atr_multiple(t, o, atr_mult=2.0)),
    ]
    
    # Test each variant
    results = []
    for name, func in variants:
        print(f"Testing {name}...")
        try:
            metrics = test_sl_variant(trades, ohlc, name, func)
            results.append(metrics)
            print(f"  Trades: {metrics.get('total_trades')}, PF: {metrics.get('profit_factor')}, Exp: {metrics.get('expectancy'):.2f}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Save results
    output_json = args.output / 'sl_alternatives_results.json'
    output_json.write_text(json.dumps(results, indent=2))
    print(f"Saved results to {output_json}")
    
    # Print summary table
    if results:
        print("\n=== SL VARIANT COMPARISON ===")
        print(f"{'Variant':<15} {'Trades':<10} {'Net P&L':<12} {'PF':<8} {'Expectancy':<12}")
        print("-" * 60)
        for r in sorted(results, key=lambda x: x.get('expectancy', 0), reverse=True):
            print(
                f"{r['variant_name']:<15} "
                f"{r.get('total_trades', 0):<10} "
                f"${r.get('total_pnl', 0):<11.2f} "
                f"{r.get('profit_factor', 0):<8.2f} "
                f"${r.get('expectancy', 0):<11.2f}"
            )
