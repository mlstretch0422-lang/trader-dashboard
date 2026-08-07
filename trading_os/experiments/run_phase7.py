"""Phase 7 experiments runner.

This script orchestrates basic, reproducible tests described in PHASE7_TEST_PLAN.md.

Usage:
  python run_phase7.py [--price-csv PATH_TO_OHLC_CSV]

If no price CSV is provided, a small synthetic dataset is generated for a quick smoke test.
"""
import argparse
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import itertools
import re
import json

# Make local strat backtest importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "strat", "src"))
from strat.backtest import run_orb_midpoint_backtest
from typing import Optional


def run_orb_midpoint_backtest_param(prices: pd.DataFrame, orb_start_min: int = 570, orb_end_min: int = 585, stop_pts: Optional[float] = None, tp_pts: Optional[float] = None, sizing_mode: str = "fixed") -> pd.DataFrame:
    """Parameterized midpoint retest backtest.

    orb_start_min / orb_end_min are minutes-since-midnight markers (e.g., 480=8:00, 570=9:30).
    stop_pts and tp_pts are point distances for stop and take-profit (None means no stop/tp).
    sizing_mode: 'fixed' | 'double_after_loss' | 'pyramid_on_win'
    """
    df = prices.copy()
    if "datetime" in df.columns:
        df = df.rename(columns={"datetime": "datetime"})
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    rows = []
    orb_high = None
    orb_low = None
    orb_mid = None
    orb_done = False
    breakout_long = False
    breakout_short = False
    entry_pending = False
    entry_dir = 0
    entry_price = None
    entry_time = None
    current_day = None
    prev_result = None
    qty = 1

    for _, row in df.iterrows():
        ts = row["datetime"]
        hour = ts.hour
        minute = ts.minute
        time_mins = hour * 60 + minute
        day_key = ts.date()

        if current_day is None or day_key != current_day:
            current_day = day_key
            orb_high = None
            orb_low = None
            orb_mid = None
            orb_done = False
            breakout_long = False
            breakout_short = False
            entry_pending = False
            entry_dir = 0
            entry_price = None
            entry_time = None

        if time_mins >= orb_start_min and time_mins < orb_end_min:
            if not orb_done:
                if orb_high is None:
                    orb_high = row["high"]
                    orb_low = row["low"]
                else:
                    orb_high = max(orb_high, row["high"])
                    orb_low = min(orb_low, row["low"])
        elif not orb_done and orb_high is not None:
            orb_mid = (orb_high + orb_low) / 2.0
            orb_done = True

        if orb_done and not breakout_long and not breakout_short:
            if row["close"] > orb_high:
                breakout_long = True
            elif row["close"] < orb_low:
                breakout_short = True

        if orb_done and not entry_pending and breakout_long and time_mins >= orb_end_min and time_mins < 1100:
            if row["low"] <= orb_mid and row["close"] >= orb_mid:
                entry_pending = True
                entry_dir = 1
                entry_price = row["close"]
                entry_time = ts
                # sizing
                if sizing_mode == "fixed":
                    qty = 1
                elif sizing_mode == "double_after_loss":
                    qty = 2 if prev_result is not None and prev_result < 0 else 1
                elif sizing_mode == "pyramid_on_win":
                    qty = 2 if prev_result is not None and prev_result > 0 else 1
        elif orb_done and not entry_pending and breakout_short and time_mins >= orb_end_min and time_mins < 1100:
            if row["high"] >= orb_mid and row["close"] <= orb_mid:
                entry_pending = True
                entry_dir = -1
                entry_price = row["close"]
                entry_time = ts
                if sizing_mode == "fixed":
                    qty = 1
                elif sizing_mode == "double_after_loss":
                    qty = 2 if prev_result is not None and prev_result < 0 else 1
                elif sizing_mode == "pyramid_on_win":
                    qty = 2 if prev_result is not None and prev_result > 0 else 1

        # Management: check for stop/TP hits first, then regular exit condition
        if entry_pending and entry_dir == 1 and time_mins >= orb_end_min and time_mins < 1100:
            # If stop/TP provided, check if hit on this bar
            hit = False
            if tp_pts is not None and row["high"] >= entry_price + tp_pts:
                pnl = (tp_pts) * 50 * qty
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "long", "entry_price": entry_price, "exit_price": entry_price + tp_pts, "pnl_points": tp_pts, "pnl_usd": pnl, "qty": qty})
                prev_result = pnl
                entry_pending = False
                hit = True
            elif stop_pts is not None and row["low"] <= entry_price - stop_pts:
                pnl = (-stop_pts) * 50 * qty
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "long", "entry_price": entry_price, "exit_price": entry_price - stop_pts, "pnl_points": -stop_pts, "pnl_usd": pnl, "qty": qty})
                prev_result = pnl
                entry_pending = False
                hit = True

            if not hit and row["low"] <= orb_mid and row["close"] >= orb_mid:
                # original exit (same-bar close at midpoint)
                pnl = (row["close"] - entry_price) * 50 * qty
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "long", "entry_price": entry_price, "exit_price": row["close"], "pnl_points": row["close"] - entry_price, "pnl_usd": pnl, "qty": qty})
                prev_result = pnl
                entry_pending = False

        elif entry_pending and entry_dir == -1 and time_mins >= orb_end_min and time_mins < 1100:
            hit = False
            if tp_pts is not None and row["low"] <= entry_price - tp_pts:
                pnl = (tp_pts) * 50 * qty
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "short", "entry_price": entry_price, "exit_price": entry_price - tp_pts, "pnl_points": tp_pts, "pnl_usd": pnl, "qty": qty})
                prev_result = pnl
                entry_pending = False
                hit = True
            elif stop_pts is not None and row["high"] >= entry_price + stop_pts:
                pnl = (-stop_pts) * 50 * qty
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "short", "entry_price": entry_price, "exit_price": entry_price + stop_pts, "pnl_points": -stop_pts, "pnl_usd": pnl, "qty": qty})
                prev_result = pnl
                entry_pending = False
                hit = True

            if not hit and row["high"] >= orb_mid and row["close"] <= orb_mid:
                pnl = (entry_price - row["close"]) * 50 * qty
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "short", "entry_price": entry_price, "exit_price": row["close"], "pnl_points": entry_price - row["close"], "pnl_usd": pnl, "qty": qty})
                prev_result = pnl
                entry_pending = False

    return pd.DataFrame(rows)


def load_price_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Basic mapping expectations: datetime, open, high, low, close, volume (optional)
    cols = {c.lower(): c for c in df.columns}
    mapping = {}
    for key in ["datetime", "time", "timestamp"]:
        if key in cols:
            mapping[cols[key]] = "datetime"
            break
    for key in ["open", "high", "low", "close", "volume"]:
        for c in df.columns:
            if c.lower() == key:
                mapping[c] = key
    df = df.rename(columns=mapping)
    return df


def synthetic_prices(days: int = 3, freq: str = "1T") -> pd.DataFrame:
    """Generate tiny synthetic OHLCV for smoke-testing the harness."""
    rng = pd.date_range("2026-06-01 07:00", periods=24 * 60 * days, freq=freq)
    prices = 1000 + np.cumsum(np.random.randn(len(rng)) * 0.5)
    df = pd.DataFrame({"datetime": rng, "open": prices, "high": prices + np.random.rand(len(rng)) * 0.5, "low": prices - np.random.rand(len(rng)) * 0.5, "close": prices + np.random.randn(len(rng)) * 0.1, "volume": np.random.randint(1, 100, size=len(rng))})
    return df


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    cum_vol_tp = (tp * df.get("volume", 1)).cumsum()
    cum_vol = df.get("volume", pd.Series(1, index=df.index)).cumsum()
    return cum_vol_tp / cum_vol


def compute_ema(df: pd.DataFrame, length: int = 50) -> pd.Series:
    return df["close"].ewm(span=length, adjust=False).mean()


def raw_orb_backtest(prices: pd.DataFrame) -> pd.DataFrame:
    """Simpler backtest: enter immediately on breakout, exit on opposite breakout or close of day."""
    df = prices.copy()
    if "datetime" in df.columns:
        df = df.rename(columns={"datetime": "datetime"})
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    rows = []
    orb_high = None
    orb_low = None
    orb_done = False
    current_day = None

    for _, row in df.iterrows():
        ts = row["datetime"]
        day_key = ts.date()
        hour = ts.hour
        minute = ts.minute
        time_mins = hour * 60 + minute

        if current_day is None or day_key != current_day:
            current_day = day_key
            orb_high = None
            orb_low = None
            orb_done = False
            in_trade = False
            entry_price = None
            entry_time = None
            side = None

        if time_mins >= 570 and time_mins < 585:
            if orb_high is None:
                orb_high = row["high"]
                orb_low = row["low"]
            else:
                orb_high = max(orb_high, row["high"])
                orb_low = min(orb_low, row["low"])
        elif not orb_done and orb_high is not None:
            orb_done = True

        if orb_done and not in_trade:
            if row["close"] > orb_high:
                # enter long at close
                in_trade = True
                side = "long"
                entry_price = row["close"]
                entry_time = ts
            elif row["close"] < orb_low:
                in_trade = True
                side = "short"
                entry_price = row["close"]
                entry_time = ts
        elif orb_done and in_trade:
            # exit on opposite breakout
            if side == "long" and row["close"] < orb_low:
                pnl = (row["close"] - entry_price) * 50
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "long", "entry_price": entry_price, "exit_price": row["close"], "pnl_usd": pnl})
                in_trade = False
            elif side == "short" and row["close"] > orb_high:
                pnl = (entry_price - row["close"]) * 50
                rows.append({"entry_time": entry_time, "exit_time": ts, "side": "short", "entry_price": entry_price, "exit_price": row["close"], "pnl_usd": pnl})
                in_trade = False

    return pd.DataFrame(rows)


def apply_vwap_filter(trades: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    vwap = compute_vwap(prices)
    prices = prices.copy()
    prices["vwap"] = vwap
    prices = prices.set_index(pd.to_datetime(prices["datetime"]))

    def ok(row):
        ts = pd.to_datetime(row["entry_time"])
        try:
            v = prices.loc[ts, "vwap"]
        except Exception:
            # fallback: nearest
            v = prices["vwap"].asof(ts)
        if row["side"] == "long":
            return row["entry_price"] >= v
        else:
            return row["entry_price"] <= v

    mask = trades.apply(ok, axis=1)
    return trades[mask]


def apply_ema_filter(trades: pd.DataFrame, prices: pd.DataFrame, ema_len: int = 50) -> pd.DataFrame:
    if trades.empty:
        return trades
    prices = prices.copy()
    prices["ema"] = compute_ema(prices, ema_len)
    prices = prices.set_index(pd.to_datetime(prices["datetime"]))

    def ok(row):
        ts = pd.to_datetime(row["entry_time"])
        try:
            e = prices.loc[ts, "ema"]
        except Exception:
            e = prices["ema"].asof(ts)
        if row["side"] == "long":
            return row["entry_price"] >= e
        else:
            return row["entry_price"] <= e

    mask = trades.apply(ok, axis=1)
    return trades[mask]


def atr_for_day(df: pd.DataFrame, atr_len: int = 14) -> pd.Series:
    h_l = df["high"] - df["low"]
    h_pc = (df["high"] - df["close"].shift(1)).abs()
    l_pc = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_len, min_periods=1).mean()
    return atr


def atr_regime_filter(trades: pd.DataFrame, prices: pd.DataFrame, atr_len: int = 14, max_mult: float = 2.0) -> pd.DataFrame:
    """Drop trades occurring on days where ORB range > max_mult * ATR for that day."""
    if trades.empty:
        return trades
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["datetime"]).dt.date
    # compute daily ATR at close of day
    prices["atr"] = atr_for_day(prices, atr_len)
    prices["date_orb_high"] = prices.groupby("date")["high"].transform("max")
    prices["date_orb_low"] = prices.groupby("date")["low"].transform("min")
    # map trade dates to day's ATR and orb range
    trades = trades.copy()
    trades["date"] = pd.to_datetime(trades["entry_time"]).dt.date
    def keep(row):
        d = row["date"]
        day_prices = prices[prices["date"] == d]
        if day_prices.empty:
            return True
        atr = day_prices["atr"].iloc[-1]
        orb_range = day_prices["date_orb_high"].iloc[-1] - day_prices["date_orb_low"].iloc[-1]
        return orb_range <= max_mult * atr

    mask = trades.apply(keep, axis=1)
    return trades[mask]


def summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"trades": 0, "net": 0.0, "win_rate": None}
    net = df.get("pnl_usd", df.get("pnl_points", 0)).sum()
    wins = df[df.get("pnl_usd", df.get("pnl_points", 0)) > 0]
    return {"trades": len(df), "net": float(net), "win_rate": len(wins) / len(df) if len(df) else None}


def run_all(price_df: pd.DataFrame):
    print("Running baseline (midpoint retest @9:30-9:45)...")
    baseline_930 = run_orb_midpoint_backtest(price_df)
    print("Baseline 9:30 summary:", summary(baseline_930))

    print("Running baseline (midpoint retest @8:00-8:15)...")
    baseline_8 = run_orb_midpoint_backtest_param(price_df, orb_start_min=480, orb_end_min=495)
    print("Baseline 8:00 summary:", summary(baseline_8))

    print("Running raw ORB-only test...")
    raw = raw_orb_backtest(price_df)
    print("Raw ORB summary:", summary(raw))

    print("Applying VWAP confirmation to baseline (9:30) trades...")
    v_baseline = apply_vwap_filter(baseline_930, price_df)
    print("Baseline+VWAP summary:", summary(v_baseline))

    print("Applying EMA(50) confirmation to baseline (9:30) trades...")
    e_baseline = apply_ema_filter(baseline_930, price_df, ema_len=50)
    print("Baseline+EMA summary:", summary(e_baseline))

    print("Applying ATR regime skip (max_mult=2.0) to baseline (9:30)...")
    atr_filtered = atr_regime_filter(baseline_930, price_df, atr_len=14, max_mult=2.0)
    print("ATR-filtered baseline summary:", summary(atr_filtered))

    print("Running stop/TP variant (example stop=2.5 pts, tp=5.0 pts)...")
    stop_tp = run_orb_midpoint_backtest_param(price_df, orb_start_min=570, orb_end_min=585, stop_pts=2.5, tp_pts=5.0)
    print("Stop/TP summary:", summary(stop_tp))

    print("Running adaptive sizing: double after loss")
    adapt_double = run_orb_midpoint_backtest_param(price_df, orb_start_min=570, orb_end_min=585, sizing_mode="double_after_loss")
    print("Adaptive double-after-loss summary:", summary(adapt_double))

    print("Running adaptive sizing: pyramid on win")
    adapt_pyramid = run_orb_midpoint_backtest_param(price_df, orb_start_min=570, orb_end_min=585, sizing_mode="pyramid_on_win")
    print("Adaptive pyramid-on-win summary:", summary(adapt_pyramid))

    print("Finished Phase 7 quick suite. For deeper regime/session sweeps, pass a real price CSV and we can iterate on parameters.")


def run_parameter_sweep(price_df: pd.DataFrame, out_dir: Path):
    """Run a small grid sweep over key parameters and save per-test trades and a summary CSV."""
    grid = {
        "orb_window": [(570, 585), (480, 495)],
        "use_vwap": [False, True],
        "use_ema": [False, True],
        "atr_mult": [1.5, 2.0],
        "stop_pts": [None, 2.5],
        "tp_pts": [None, 5.0],
        "sizing": ["fixed", "double_after_loss"],
    }

    keys = list(grid.keys())
    rows = []
    combo_index = 0
    for combo in itertools.product(*(grid[k] for k in keys)):
        combo_index += 1
        params = dict(zip(keys, combo))
        orb_start, orb_end = params["orb_window"]
        trades = run_orb_midpoint_backtest_param(price_df, orb_start_min=orb_start, orb_end_min=orb_end, stop_pts=params["stop_pts"], tp_pts=params["tp_pts"], sizing_mode=params["sizing"])

        # apply confirmation filters if requested
        if params["use_vwap"]:
            trades = apply_vwap_filter(trades, price_df)
        if params["use_ema"]:
            trades = apply_ema_filter(trades, price_df, ema_len=50)

        # apply ATR regime skip
        trades = atr_regime_filter(trades, price_df, atr_len=14, max_mult=params["atr_mult"])

        s = summary(trades)
        row = {**params, **s}
        row["combo_index"] = combo_index
        rows.append(row)

        # write trades for this combo
        out_file = out_dir / f"trades_combo_{combo_index}.csv"
        if not trades.empty:
            trades.to_csv(out_file, index=False)
        else:
            # create empty file to indicate no trades
            pd.DataFrame().to_csv(out_file)

    results_df = pd.DataFrame(rows)
    results_df.to_csv(out_dir / "phase7_sweep_summary.csv", index=False)
    print(f"Wrote sweep summary to {out_dir / 'phase7_sweep_summary.csv'}")


def parse_strategy_defaults() -> dict:
    """Parse key defaults from existing Pine script strategy files.

    Returns a dict of canonical parameters (orb start/end in minutes, use_vwap, use_ema, ema_len, atr_len, retest_mode).
    """
    candidates = [
        Path("strat/ES_ORB_Strategy_v1_1_FIXED.txt"),
        Path("strat/ES_ORB_Strategy_v1.0.txt"),
        Path("strat/ES_ORB_Strategy_v1_0.txt"),
    ]
    params = {
        "orb_start_min": 570,
        "orb_end_min": 585,
        "use_vwap": True,
        "use_ema": False,
        "ema_len": 50,
        "atr_len": 14,
        "retest_mode": "Midpoint",
    }
    for c in candidates:
        if not c.exists():
            continue
        text = c.read_text()
        # orb start/end
        m = re.search(r'i_orbStart\s*=\s*input.string\("(\d{4})"', text)
        if m:
            hhmm = m.group(1)
            hh = int(hhmm[:2])
            mm = int(hhmm[2:])
            params["orb_start_min"] = hh * 60 + mm
        m = re.search(r'i_orbEnd\s*=\s*input.string\("(\d{4})"', text)
        if m:
            hhmm = m.group(1)
            hh = int(hhmm[:2])
            mm = int(hhmm[2:])
            params["orb_end_min"] = hh * 60 + mm
        # VWAP, EMA
        m = re.search(r'i_useVWAP\s*=\s*input.bool\((true|false)', text, re.IGNORECASE)
        if m:
            params["use_vwap"] = m.group(1).lower() == "true"
        m = re.search(r'i_useEMA\s*=\s*input.bool\((true|false)', text, re.IGNORECASE)
        if m:
            params["use_ema"] = m.group(1).lower() == "true"
        m = re.search(r'i_emaLen\s*=\s*input.int\((\d+)', text)
        if m:
            params["ema_len"] = int(m.group(1))
        m = re.search(r'i_atrLen\s*=\s*input.int\((\d+)', text)
        if m:
            params["atr_len"] = int(m.group(1))
        m = re.search(r'i_retestMode\s*=\s*input.string\("(\w+)"', text)
        if m:
            params["retest_mode"] = m.group(1)
        # stop once we've read one file
        break
    return params


def run_component_tests(price_df: pd.DataFrame, out_dir: Path, defaults: dict):
    """Run focused tests that toggle each component individually using the strategy defaults.

    Produces a JSON summary and per-test CSVs.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []

    # Baseline: midpoint retest with defaults
    baseline = run_orb_midpoint_backtest_param(price_df, orb_start_min=defaults["orb_start_min"], orb_end_min=defaults["orb_end_min"], stop_pts=None, tp_pts=None, sizing_mode="fixed")
    results.append({"test": "baseline_midpoint", **summary(baseline)})
    baseline.to_csv(out_dir / "trades_baseline_midpoint.csv", index=False)

    # Raw ORB-only
    raw = raw_orb_backtest(price_df)
    results.append({"test": "raw_orb", **summary(raw)})
    raw.to_csv(out_dir / "trades_raw_orb.csv", index=False)

    # VWAP confirmation
    v = apply_vwap_filter(baseline, price_df)
    results.append({"test": "baseline_plus_vwap", **summary(v)})
    v.to_csv(out_dir / "trades_baseline_vwap.csv", index=False)

    # EMA confirmation
    e = apply_ema_filter(baseline, price_df, ema_len=defaults.get("ema_len", 50))
    results.append({"test": "baseline_plus_ema", **summary(e)})
    e.to_csv(out_dir / "trades_baseline_ema.csv", index=False)

    # ATR regime skip
    atrf = atr_regime_filter(baseline, price_df, atr_len=defaults.get("atr_len", 14), max_mult=2.0)
    results.append({"test": "baseline_atr_skip", **summary(atrf)})
    atrf.to_csv(out_dir / "trades_baseline_atr_skip.csv", index=False)

    # Stop / TP variations (example values)
    st = run_orb_midpoint_backtest_param(price_df, orb_start_min=defaults["orb_start_min"], orb_end_min=defaults["orb_end_min"], stop_pts=2.5, tp_pts=5.0)
    results.append({"test": "stop_tp_example", **summary(st)})
    st.to_csv(out_dir / "trades_stop_tp.csv", index=False)

    # Adaptive sizing tests
    ad1 = run_orb_midpoint_backtest_param(price_df, orb_start_min=defaults["orb_start_min"], orb_end_min=defaults["orb_end_min"], sizing_mode="double_after_loss")
    results.append({"test": "sizing_double_after_loss", **summary(ad1)})
    ad1.to_csv(out_dir / "trades_sizing_double.csv", index=False)

    ad2 = run_orb_midpoint_backtest_param(price_df, orb_start_min=defaults["orb_start_min"], orb_end_min=defaults["orb_end_min"], sizing_mode="pyramid_on_win")
    results.append({"test": "sizing_pyramid_on_win", **summary(ad2)})
    ad2.to_csv(out_dir / "trades_sizing_pyramid.csv", index=False)

    # Save JSON summary
    (out_dir / "component_summary.json").write_text(json.dumps(results, indent=2))
    print(f"Wrote component test outputs to {out_dir}")
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--price-csv", type=Path, help="Path to OHLC CSV to run experiments on")
    p.add_argument("--sweep", action="store_true", help="Run a small parameter sweep and export CSV results")
    p.add_argument("--out-dir", type=Path, default=Path("trading_os/experiments/outputs"), help="Directory to write CSV outputs")
    args = p.parse_args()

    if args.price_csv and args.price_csv.exists():
        df = load_price_csv(args.price_csv)
    else:
        print("No price CSV provided or file not found — using synthetic data for a smoke test.")
        df = synthetic_prices()

    # Run the standard Phase 7 quick suite
    run_all(df)

    # If a real price CSV was provided, parse your strategy defaults and run component-focused tests
    if args.price_csv and args.price_csv.exists():
        defaults = parse_strategy_defaults()
        comp_out = Path("trading_os/experiments/outputs/component_tests")
        run_component_tests(df, comp_out, defaults)

    if args.sweep:
        out_dir = args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Running parameter sweep and writing outputs to {out_dir}")
        run_parameter_sweep(df, out_dir)


if __name__ == "__main__":
    main()
