#!/usr/bin/env python3
"""
ORB V2 optimizer and component attribution harness.

Goals:
1. Optimize parameters on realistic bar-by-bar rules.
2. Decompose edge by enabling/disabling each confluence filter.
3. Evaluate funded-account style constraints for a 50k account.

Usage examples:
  python3 trading_os/experiments/orb_v2_optimizer.py
  python3 trading_os/experiments/orb_v2_optimizer.py --trials 120 --years 8
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


ES_MULTIPLIER = 50.0


@dataclass
class StrategyParams:
    orb_start_min: int = 480
    orb_end_min: int = 495
    trade_start_min: int = 570
    min_orb_range: float = 4.0
    max_orb_range: float = 20.0
    min_confluence: int = 3
    min_confluence_long: int = 0
    min_confluence_short: int = 0
    volume_mult: float = 1.5
    displacement_mult: float = 2.0
    retest_fraction: float = 0.5
    retest_tolerance_pts: float = 0.0
    tp_r: float = 2.0
    break_even_r: float = 0.0
    sl_buffer_pts: float = 0.0
    entry_end_min: int = 630  # 10:30 ET
    require_ema: bool = True
    require_vwap: bool = True
    use_volume: bool = True
    use_displacement: bool = True
    use_liquidity_sweep: bool = False
    use_bull_rejection: bool = False
    use_bull_engulfing: bool = False
    use_bull_mss: bool = False
    use_bull_fvg: bool = False
    use_bear_rejection: bool = False
    use_bear_engulfing: bool = False
    use_bear_mss: bool = False
    use_bear_fvg: bool = False
    sweep_tolerance_pts: float = 0.0
    sweep_lookback_bars: int = 9999
    rejection_wick_ratio: float = 1.5
    allow_short: bool = False
    max_trades_per_day: int = 1
    second_trade_only_after_loss: bool = False
    strategy_daily_loss_stop_usd: float = 0.0
    strategy_daily_profit_lock_usd: float = 0.0
    mss_lookback: int = 5
    min_daily_atr14: float = 0.0
    max_daily_atr14: float = 9999.0


def load_data(csv_path: Path, years: int | None = None) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    if years is not None:
        max_ts = df["datetime"].max()
        cutoff = max_ts - pd.DateOffset(years=years)
        df = df[df["datetime"] >= cutoff].copy()

    df["date"] = df["datetime"].dt.date
    df["time_min"] = df["datetime"].dt.hour * 60 + df["datetime"].dt.minute

    # Indicators
    df["body"] = (df["close"] - df["open"]).abs()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["avg_vol_20"] = df["volume"].rolling(20).mean()
    df["avg_body_20"] = df["body"].rolling(20).mean()

    # Previous bar references for candlestick/price-action features.
    df["prev_open"] = df["open"].shift(1)
    df["prev_close"] = df["close"].shift(1)
    df["prev_high"] = df["high"].shift(1)
    df["high_2"] = df["high"].shift(2)

    # Candlestick bias proxies.
    lower_wick = np.minimum(df["open"], df["close"]) - df["low"]
    upper_wick = df["high"] - np.maximum(df["open"], df["close"])
    body_safe = df["body"].replace(0.0, np.nan)
    df["lower_wick_ratio"] = (lower_wick / body_safe).fillna(0.0)
    df["upper_wick_ratio"] = (upper_wick / body_safe).fillna(0.0)
    # Default rejection labels at legacy threshold for compatibility/inspection.
    df["bull_rejection"] = (df["close"] > df["open"]) & (df["lower_wick_ratio"] >= 1.5)
    df["bear_rejection"] = (df["close"] < df["open"]) & (df["upper_wick_ratio"] >= 1.5)
    df["bull_engulfing"] = (
        (df["prev_close"] < df["prev_open"])
        & (df["close"] > df["open"])
        & (df["open"] <= df["prev_close"])
        & (df["close"] >= df["prev_open"])
    )
    df["bear_engulfing"] = (
        (df["prev_close"] > df["prev_open"])
        & (df["close"] < df["open"])
        & (df["open"] >= df["prev_close"])
        & (df["close"] <= df["prev_open"])
    )

    # ICT-style FVG proxy: current low above high two bars back (bullish imbalance).
    df["bull_fvg"] = df["low"] > df["high_2"]
    df["low_2"] = df["low"].shift(2)
    df["bear_fvg"] = df["high"] < df["low_2"]

    # Session VWAP reset each day to better match platform behavior.
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    df["pv"] = tp * df["volume"]
    df["vwap"] = df.groupby("date")["pv"].cumsum() / df.groupby("date")["volume"].cumsum()

    # Prior day levels for a simple HTF liquidity proxy.
    daily = df.groupby("date").agg(day_high=("high", "max"), day_low=("low", "min")).reset_index()
    daily["prev_day_high"] = daily["day_high"].shift(1)
    daily["prev_day_low"] = daily["day_low"].shift(1)
    day_level_map = daily.set_index("date")[["prev_day_high", "prev_day_low"]]

    df = df.join(day_level_map, on="date")
    df["day_low_so_far"] = df.groupby("date")["low"].cummin()
    df["day_high_so_far"] = df.groupby("date")["high"].cummax()

    # Daily ATR14 regime feature (mapped back to intraday rows).
    daily_ohlc = df.groupby("date").agg(
        day_high=("high", "max"),
        day_low=("low", "min"),
        day_close=("close", "last"),
    ).reset_index()
    prev_close = daily_ohlc["day_close"].shift(1)
    tr = pd.concat(
        [
            daily_ohlc["day_high"] - daily_ohlc["day_low"],
            (daily_ohlc["day_high"] - prev_close).abs(),
            (daily_ohlc["day_low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    daily_ohlc["daily_atr14"] = tr.rolling(14).mean()
    atr_map = daily_ohlc.set_index("date")["daily_atr14"]
    df = df.join(atr_map, on="date")

    return df


def build_orb_lookup(df: pd.DataFrame,
                     orb_start: int = 480,
                     orb_end: int = 495,
                     min_orb_range: float = 4.0,
                     max_orb_range: float = 20.0) -> Dict:
    lookup: Dict = {}
    for date, day in df.groupby("date", sort=False):
        orb = day[(day["time_min"] >= orb_start) & (day["time_min"] <= orb_end)]
        if orb.empty:
            continue
        orb_high = float(orb["high"].max())
        orb_low = float(orb["low"].min())
        orb_range = orb_high - orb_low
        if min_orb_range < orb_range < max_orb_range:
            lookup[date] = {
                "orb_high": orb_high,
                "orb_low": orb_low,
                "orb_mid": (orb_high + orb_low) / 2.0,
                "orb_range": orb_range,
            }
    return lookup


def funded_account_eval(trades: pd.DataFrame,
                        start_balance: float = 50000.0,
                        monthly_target: float = 3000.0,
                        monthly_stretch_target: float = 5000.0,
                        max_daily_loss: float = 2500.0,
                        trailing_max_drawdown: float = 2500.0,
                        static_max_drawdown: float = 2500.0) -> Dict:
    if trades.empty:
        return {
            "months_with_pass": 0,
            "months_with_stretch_pass": 0,
            "months_total": 0,
            "monthly_pass_rate": 0.0,
            "monthly_stretch_pass_rate": 0.0,
            "daily_loss_breaches": 0,
            "dd_breached": False,
            "trailing_dd_breached": False,
            "static_dd_breached": False,
            "max_dd_dollars": 0.0,
            "max_trailing_dd_dollars": 0.0,
            "max_static_dd_dollars": 0.0,
        }

    t = trades.copy()
    t["exit_date"] = pd.to_datetime(t["exit_time"]).dt.date
    t["exit_month"] = pd.to_datetime(t["exit_time"]).dt.to_period("M")

    daily = t.groupby("exit_date")["pnl_usd"].sum().sort_index()
    monthly = t.groupby("exit_month")["pnl_usd"].sum().sort_index()

    months_with_pass = int((monthly >= monthly_target).sum())
    months_with_stretch_pass = int((monthly >= monthly_stretch_target).sum())
    months_total = int(len(monthly))

    equity = start_balance + daily.cumsum()
    running_peak = equity.cummax()
    trailing_dd = running_peak - equity
    # Static drawdown should be non-negative distance below the initial balance.
    static_dd = (start_balance - equity).clip(lower=0.0)

    trailing_dd_breached = bool((trailing_dd > trailing_max_drawdown).any())
    static_dd_breached = bool((static_dd > static_max_drawdown).any())

    return {
        "months_with_pass": months_with_pass,
        "months_with_stretch_pass": months_with_stretch_pass,
        "months_total": months_total,
        "monthly_pass_rate": float(months_with_pass / months_total) if months_total else 0.0,
        "monthly_stretch_pass_rate": float(months_with_stretch_pass / months_total) if months_total else 0.0,
        "daily_loss_breaches": int((daily <= -abs(max_daily_loss)).sum()),
        "dd_breached": trailing_dd_breached or static_dd_breached,
        "trailing_dd_breached": trailing_dd_breached,
        "static_dd_breached": static_dd_breached,
        "max_dd_dollars": float(trailing_dd.max()) if len(trailing_dd) else 0.0,
        "max_trailing_dd_dollars": float(trailing_dd.max()) if len(trailing_dd) else 0.0,
        "max_static_dd_dollars": float(static_dd.max()) if len(static_dd) else 0.0,
    }


def backtest(df: pd.DataFrame,
             orb_lookup: Dict,
             params: StrategyParams,
             funded_monthly_target: float = 3000.0,
             funded_monthly_stretch_target: float = 5000.0,
             funded_daily_loss: float = 2500.0,
             funded_trailing_max_drawdown: float = 2500.0,
             funded_static_max_drawdown: float = 2500.0,
             point_value: float = ES_MULTIPLIER) -> Dict:
    trades: List[Dict] = []

    # Use day buckets for efficient date checks.
    for date, day in df.groupby("date", sort=False):
        if date not in orb_lookup:
            continue
        orb = orb_lookup[date]

        trades_today = 0
        last_exit_time = None
        day_realized_pnl = 0.0
        day_trade_pnls: List[float] = []

        while trades_today < max(1, int(params.max_trades_per_day)):
            if params.strategy_daily_loss_stop_usd > 0 and day_realized_pnl <= -abs(params.strategy_daily_loss_stop_usd):
                break
            if params.strategy_daily_profit_lock_usd > 0 and day_realized_pnl >= params.strategy_daily_profit_lock_usd:
                break
            if params.second_trade_only_after_loss and trades_today >= 1 and len(day_trade_pnls) >= 1 and day_trade_pnls[0] >= 0:
                break

            # Entry scan in user window.
            scan_start = max(params.trade_start_min, params.orb_end_min + 1)
            scan = day[(day["time_min"] >= scan_start) & (day["time_min"] <= params.entry_end_min)]
            if last_exit_time is not None:
                scan = scan[scan["datetime"] > last_exit_time]
            if scan.empty:
                break

            recent_swing_high = scan["high"].rolling(params.mss_lookback).max().shift(1)
            recent_swing_low = scan["low"].rolling(params.mss_lookback).min().shift(1)

            # Build sweep state from full day context so pre-entry sweeps can qualify later entries.
            day_low_window = day["low"].rolling(max(1, params.sweep_lookback_bars)).min()
            day_high_window = day["high"].rolling(max(1, params.sweep_lookback_bars)).max()
            day_long_sweep_event = (
                day["prev_day_low"].notna()
                & (day_low_window <= (day["prev_day_low"] + params.sweep_tolerance_pts))
            )
            day_short_sweep_event = (
                day["prev_day_high"].notna()
                & (day_high_window >= (day["prev_day_high"] - params.sweep_tolerance_pts))
            )
            day_long_sweep_state = day_long_sweep_event.cummax()
            day_short_sweep_state = day_short_sweep_event.cummax()

            long_sweep_state = day_long_sweep_state.reindex(scan.index, fill_value=False)
            short_sweep_state = day_short_sweep_state.reindex(scan.index, fill_value=False)

            in_position = False
            position_side = ""
            entry_price = 0.0
            entry_time = None
            sl_price = 0.0
            tp_price = 0.0
            be_trigger_price = 0.0
            be_armed = False
            confluence_at_entry = 0

            min_conf_long = params.min_confluence_long if params.min_confluence_long > 0 else params.min_confluence
            min_conf_short = params.min_confluence_short if params.min_confluence_short > 0 else params.min_confluence

            for row in scan.itertuples(index=True):
                if in_position:
                    break

                row_idx = row.Index

                ema_ok = (row.ema20 > row.ema50) and (row.ema50 > row.ema200)
                ema_short_ok = (row.ema20 < row.ema50) and (row.ema50 < row.ema200)
                vwap_ok = row.close > row.vwap
                vwap_short_ok = row.close < row.vwap
                vol_ok = row.volume > (row.avg_vol_20 * params.volume_mult) if pd.notna(row.avg_vol_20) else False
                disp_ok = row.body > (row.avg_body_20 * params.displacement_mult) if pd.notna(row.avg_body_20) else False

                liq_ok = True
                if params.use_liquidity_sweep:
                    sweep_seen = bool(long_sweep_state.loc[row_idx]) if row_idx in long_sweep_state.index else False
                    liq_ok = (
                        sweep_seen
                        and
                        pd.notna(row.prev_day_low)
                        and row.close >= (row.prev_day_low - params.sweep_tolerance_pts)
                    )

                liq_short_ok = True
                if params.use_liquidity_sweep:
                    sweep_seen_short = bool(short_sweep_state.loc[row_idx]) if row_idx in short_sweep_state.index else False
                    liq_short_ok = (
                        sweep_seen_short
                        and
                        pd.notna(row.prev_day_high)
                        and row.close <= (row.prev_day_high + params.sweep_tolerance_pts)
                    )

                atr_ok = True
                if pd.notna(row.daily_atr14):
                    atr_ok = params.min_daily_atr14 <= row.daily_atr14 <= params.max_daily_atr14

                bull_rejection_ok = bool((row.close > row.open) and (row.lower_wick_ratio >= params.rejection_wick_ratio))
                bull_engulfing_ok = bool(row.bull_engulfing)
                bear_rejection_ok = bool((row.close < row.open) and (row.upper_wick_ratio >= params.rejection_wick_ratio))
                bear_engulfing_ok = bool(row.bear_engulfing)

                use_rejection_short = params.use_bear_rejection or params.use_bull_rejection
                use_engulfing_short = params.use_bear_engulfing or params.use_bull_engulfing
                use_mss_short = params.use_bear_mss or params.use_bull_mss
                use_fvg_short = params.use_bear_fvg or params.use_bull_fvg

                bull_mss_ok = True
                bear_mss_ok = True
                if params.use_bull_mss:
                    if row_idx is None or row_idx not in recent_swing_high.index:
                        bull_mss_ok = False
                    else:
                        swing = recent_swing_high.loc[row_idx]
                        bull_mss_ok = pd.notna(swing) and (row.close > swing)

                if use_mss_short:
                    if row_idx is None or row_idx not in recent_swing_low.index:
                        bear_mss_ok = False
                    else:
                        swing_low = recent_swing_low.loc[row_idx]
                        bear_mss_ok = pd.notna(swing_low) and (row.close < swing_low)

                bull_fvg_ok = bool(row.bull_fvg)
                bear_fvg_ok = bool(row.bear_fvg)

                checks_long = [
                    ema_ok if params.require_ema else True,
                    vwap_ok if params.require_vwap else True,
                    vol_ok if params.use_volume else True,
                    disp_ok if params.use_displacement else True,
                    liq_ok,
                    atr_ok,
                    bull_rejection_ok if params.use_bull_rejection else True,
                    bull_engulfing_ok if params.use_bull_engulfing else True,
                    bull_mss_ok if params.use_bull_mss else True,
                    bull_fvg_ok if params.use_bull_fvg else True,
                ]
                checks_short = [
                    ema_short_ok if params.require_ema else True,
                    vwap_short_ok if params.require_vwap else True,
                    vol_ok if params.use_volume else True,
                    disp_ok if params.use_displacement else True,
                    liq_short_ok,
                    atr_ok,
                    bear_rejection_ok if use_rejection_short else True,
                    bear_engulfing_ok if use_engulfing_short else True,
                    bear_mss_ok if use_mss_short else True,
                    bear_fvg_ok if use_fvg_short else True,
                ]
                confluence_long = int(sum(checks_long))
                confluence_short = int(sum(checks_short))

                retest_level = orb["orb_low"] + (orb["orb_range"] * params.retest_fraction)
                retest_level += params.retest_tolerance_pts

                # Long breakout + flexible retest requirement.
                signal = (
                    row.close > orb["orb_high"]
                    and row.low <= retest_level
                    and confluence_long >= min_conf_long
                    and (ema_ok if params.require_ema else True)
                    and (vwap_ok if params.require_vwap else True)
                    and (liq_ok if params.use_liquidity_sweep else True)
                    and atr_ok
                    and (bull_rejection_ok if params.use_bull_rejection else True)
                    and (bull_engulfing_ok if params.use_bull_engulfing else True)
                    and (bull_mss_ok if params.use_bull_mss else True)
                    and (bull_fvg_ok if params.use_bull_fvg else True)
                )

                signal_short = (
                    params.allow_short
                    and row.close < orb["orb_low"]
                    and row.high >= (orb["orb_high"] - (orb["orb_range"] * params.retest_fraction) - params.retest_tolerance_pts)
                    and confluence_short >= min_conf_short
                    and (ema_short_ok if params.require_ema else True)
                    and (vwap_short_ok if params.require_vwap else True)
                    and (liq_short_ok if params.use_liquidity_sweep else True)
                    and atr_ok
                    and (bear_rejection_ok if use_rejection_short else True)
                    and (bear_engulfing_ok if use_engulfing_short else True)
                    and (bear_mss_ok if use_mss_short else True)
                    and (bear_fvg_ok if use_fvg_short else True)
                )

                if signal:
                    in_position = True
                    position_side = "LONG"
                    entry_price = float(row.close)
                    entry_time = row.datetime
                    confluence_at_entry = confluence_long

                    sl_price = orb["orb_low"] - params.sl_buffer_pts
                    risk = entry_price - sl_price
                    if risk <= 0:
                        in_position = False
                        continue
                    tp_price = entry_price + (risk * params.tp_r)
                    be_trigger_price = entry_price + (risk * params.break_even_r) if params.break_even_r > 0 else 0.0
                    be_armed = False
                elif signal_short:
                    in_position = True
                    position_side = "SHORT"
                    entry_price = float(row.close)
                    entry_time = row.datetime
                    confluence_at_entry = confluence_short

                    sl_price = orb["orb_high"] + params.sl_buffer_pts
                    risk = sl_price - entry_price
                    if risk <= 0:
                        in_position = False
                        continue
                    tp_price = entry_price - (risk * params.tp_r)
                    be_trigger_price = entry_price - (risk * params.break_even_r) if params.break_even_r > 0 else 0.0
                    be_armed = False

            # Exit on same day, realistic bar-by-bar.
            if not in_position:
                break

            post = day[day["datetime"] > entry_time]
            closed = False
            exit_time = None
            for row in post.itertuples(index=False):
                # Arm break-even stop after favorable excursion reaches configured R multiple.
                if position_side == "LONG":
                    if params.break_even_r > 0 and (not be_armed) and row.high >= be_trigger_price:
                        sl_price = max(sl_price, entry_price)
                        be_armed = True

                    if row.low <= sl_price:
                        trades.append({
                            "entry_time": entry_time,
                            "exit_time": row.datetime,
                            "entry_price": entry_price,
                            "exit_price": sl_price,
                            "pnl_usd": (sl_price - entry_price) * point_value,
                            "reason": "SL",
                            "confluence": confluence_at_entry,
                            "date": str(date),
                            "side": position_side,
                        })
                        closed = True
                        exit_time = row.datetime
                        break
                    if row.high >= tp_price:
                        trades.append({
                            "entry_time": entry_time,
                            "exit_time": row.datetime,
                            "entry_price": entry_price,
                            "exit_price": tp_price,
                            "pnl_usd": (tp_price - entry_price) * point_value,
                            "reason": "TP",
                            "confluence": confluence_at_entry,
                            "date": str(date),
                            "side": position_side,
                        })
                        closed = True
                        exit_time = row.datetime
                        break
                else:
                    if params.break_even_r > 0 and (not be_armed) and row.low <= be_trigger_price:
                        sl_price = min(sl_price, entry_price)
                        be_armed = True

                    if row.high >= sl_price:
                        trades.append({
                            "entry_time": entry_time,
                            "exit_time": row.datetime,
                            "entry_price": entry_price,
                            "exit_price": sl_price,
                            "pnl_usd": (entry_price - sl_price) * point_value,
                            "reason": "SL",
                            "confluence": confluence_at_entry,
                            "date": str(date),
                            "side": position_side,
                        })
                        closed = True
                        exit_time = row.datetime
                        break
                    if row.low <= tp_price:
                        trades.append({
                            "entry_time": entry_time,
                            "exit_time": row.datetime,
                            "entry_price": entry_price,
                            "exit_price": tp_price,
                            "pnl_usd": (entry_price - tp_price) * point_value,
                            "reason": "TP",
                            "confluence": confluence_at_entry,
                            "date": str(date),
                            "side": position_side,
                        })
                        closed = True
                        exit_time = row.datetime
                        break

            if not closed:
                last = day.iloc[-1]
                if position_side == "LONG":
                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": last["datetime"],
                        "entry_price": entry_price,
                        "exit_price": float(last["close"]),
                        "pnl_usd": (float(last["close"]) - entry_price) * point_value,
                        "reason": "EOD",
                        "confluence": confluence_at_entry,
                        "date": str(date),
                        "side": position_side,
                    })
                else:
                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": last["datetime"],
                        "entry_price": entry_price,
                        "exit_price": float(last["close"]),
                        "pnl_usd": (entry_price - float(last["close"])) * point_value,
                        "reason": "EOD",
                        "confluence": confluence_at_entry,
                        "date": str(date),
                        "side": position_side,
                    })
                exit_time = last["datetime"]

            trades_today += 1
            if trades:
                this_pnl = float(trades[-1]["pnl_usd"])
                day_realized_pnl += this_pnl
                day_trade_pnls.append(this_pnl)
            last_exit_time = exit_time

            if last_exit_time is None or last_exit_time >= day.iloc[-1]["datetime"]:
                break

    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        return {
            "status": "NO_TRADES",
            "trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_pnl": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0,
            "funded": funded_account_eval(
                trades_df,
                monthly_target=funded_monthly_target,
                monthly_stretch_target=funded_monthly_stretch_target,
                max_daily_loss=funded_daily_loss,
                trailing_max_drawdown=funded_trailing_max_drawdown,
                static_max_drawdown=funded_static_max_drawdown,
            ),
            "trades_df": trades_df,
        }

    wins = trades_df[trades_df["pnl_usd"] > 0]
    losses = trades_df[trades_df["pnl_usd"] < 0]
    total_pnl = float(trades_df["pnl_usd"].sum())
    win_rate = float(len(wins) / len(trades_df))
    gross_profit = float(wins["pnl_usd"].sum())
    gross_loss = float(abs(losses["pnl_usd"].sum()))
    pf = float(gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
    expectancy = float(trades_df["pnl_usd"].mean())

    eq = trades_df["pnl_usd"].cumsum()
    dd = eq - eq.cummax()
    max_dd = float(dd.min())

    return {
        "status": "SUCCESS",
        "trades": int(len(trades_df)),
        "win_rate": win_rate,
        "profit_factor": pf,
        "total_pnl": total_pnl,
        "expectancy": expectancy,
        "max_drawdown": max_dd,
        "funded": funded_account_eval(
            trades_df,
            monthly_target=funded_monthly_target,
            monthly_stretch_target=funded_monthly_stretch_target,
            max_daily_loss=funded_daily_loss,
            trailing_max_drawdown=funded_trailing_max_drawdown,
            static_max_drawdown=funded_static_max_drawdown,
        ),
        "trades_df": trades_df,
    }


def sample_param_space(rng: random.Random, trials: int, profile: str = "broad") -> List[StrategyParams]:
    out: List[StrategyParams] = []

    if profile == "funded_live_like":
        for _ in range(trials):
            out.append(
                StrategyParams(
                    orb_start_min=570,
                    orb_end_min=rng.choice([585, 600]),
                    trade_start_min=rng.choice([585, 600]),
                    min_orb_range=rng.choice([3.0, 4.0, 5.0]),
                    max_orb_range=rng.choice([16.0, 20.0, 24.0]),
                    min_confluence=rng.choice([2, 3]),
                    min_confluence_long=rng.choice([2, 3, 4]),
                    min_confluence_short=rng.choice([2, 3, 4]),
                    volume_mult=rng.choice([1.0, 1.25, 1.5]),
                    displacement_mult=rng.choice([1.0, 1.5]),
                    retest_fraction=rng.choice([0.5, 0.65]),
                    retest_tolerance_pts=rng.choice([0.0, 0.25, 0.5]),
                    tp_r=rng.choice([1.5, 2.0, 2.5]),
                    break_even_r=rng.choice([0.75, 1.0]),
                    sl_buffer_pts=rng.choice([0.0, 0.25, 0.5]),
                    entry_end_min=rng.choice([615, 630]),
                    require_ema=True,
                    require_vwap=True,
                    use_volume=rng.choice([True, False]),
                    use_displacement=rng.choice([True, True, False]),
                    use_liquidity_sweep=rng.choice([True, True, False]),
                    use_bull_rejection=rng.choice([True, False]),
                    use_bull_engulfing=rng.choice([False, True]),
                    use_bull_mss=rng.choice([True, False]),
                    use_bull_fvg=rng.choice([False, True]),
                    use_bear_rejection=rng.choice([False, True]),
                    use_bear_engulfing=rng.choice([False, True]),
                    use_bear_mss=rng.choice([False, True]),
                    use_bear_fvg=rng.choice([False, True]),
                    sweep_tolerance_pts=rng.choice([0.0, 0.25, 0.5, 0.75, 1.0]),
                    sweep_lookback_bars=rng.choice([3, 5, 8, 12, 20]),
                    rejection_wick_ratio=rng.choice([1.0, 1.25, 1.5, 1.75, 2.0]),
                    allow_short=True,
                    max_trades_per_day=rng.choice([1, 1, 2]),
                    second_trade_only_after_loss=True,
                    strategy_daily_loss_stop_usd=rng.choice([150.0, 200.0, 250.0]),
                    strategy_daily_profit_lock_usd=rng.choice([0.0, 300.0, 500.0]),
                    mss_lookback=rng.choice([3, 5, 8]),
                    min_daily_atr14=rng.choice([20.0, 30.0]),
                    max_daily_atr14=rng.choice([80.0, 100.0, 120.0]),
                )
            )
        return out

    for _ in range(trials):
        out.append(
            StrategyParams(
                orb_start_min=480,
                orb_end_min=rng.choice([490, 495, 500, 510]),
                trade_start_min=570,
                min_orb_range=rng.choice([3.0, 4.0, 5.0, 6.0]),
                max_orb_range=rng.choice([16.0, 20.0, 24.0]),
                min_confluence=rng.choice([2, 3, 4]),
                min_confluence_long=rng.choice([0, 2, 3, 4]),
                min_confluence_short=rng.choice([0, 2, 3, 4]),
                volume_mult=rng.choice([1.0, 1.25, 1.5, 1.75]),
                displacement_mult=rng.choice([1.0, 1.5, 2.0]),
                retest_fraction=rng.choice([0.35, 0.5, 0.65]),
                retest_tolerance_pts=rng.choice([0.0, 0.25, 0.5, 1.0]),
                tp_r=rng.choice([1.5, 2.0, 2.5, 3.0]),
                break_even_r=rng.choice([0.0, 0.75, 1.0, 1.25]),
                sl_buffer_pts=rng.choice([0.0, 0.25, 0.5, 1.0]),
                entry_end_min=rng.choice([600, 615, 630]),
                require_ema=True,
                require_vwap=True,
                use_volume=rng.choice([True, False]),
                use_displacement=rng.choice([True, False]),
                use_liquidity_sweep=rng.choice([True, False]),
                use_bull_rejection=rng.choice([True, False]),
                use_bull_engulfing=rng.choice([True, False]),
                use_bull_mss=rng.choice([True, False]),
                use_bull_fvg=rng.choice([True, False]),
                use_bear_rejection=rng.choice([True, False]),
                use_bear_engulfing=rng.choice([True, False]),
                use_bear_mss=rng.choice([True, False]),
                use_bear_fvg=rng.choice([True, False]),
                sweep_tolerance_pts=rng.choice([0.0, 0.25, 0.5, 0.75, 1.0]),
                sweep_lookback_bars=rng.choice([3, 5, 8, 12, 20]),
                rejection_wick_ratio=rng.choice([1.0, 1.25, 1.5, 1.75, 2.0]),
                allow_short=rng.choice([True, False]),
                max_trades_per_day=rng.choice([1, 2]),
                second_trade_only_after_loss=rng.choice([False, True]),
                strategy_daily_loss_stop_usd=rng.choice([0.0, 150.0, 200.0, 250.0]),
                strategy_daily_profit_lock_usd=rng.choice([0.0, 300.0, 500.0]),
                mss_lookback=rng.choice([3, 5, 8]),
                min_daily_atr14=rng.choice([0.0, 20.0, 30.0, 40.0]),
                max_daily_atr14=rng.choice([80.0, 100.0, 120.0, 9999.0]),
            )
        )
    return out


def score_result(result: Dict,
                 min_trades: int = 30,
                 min_months: int = 12,
                 profile: str = "balanced") -> float:
    # Reward profitability and funded pass behavior, penalize large DD and thin samples.
    if result["status"] != "SUCCESS":
        return -1e9

    funded = result["funded"]
    trades = result["trades"]
    months = funded["months_total"]

    # Hard penalties for statistically weak candidates.
    if trades < min_trades:
        return -5e8 + (trades * 100.0)
    if months < min_months:
        return -4e8 + (months * 100.0)

    score = 0.0
    pf_effective = min(result["profit_factor"], 3.0)

    if profile == "cadence":
        # Cadence-first profile: optimize for funded pass consistency first.
        score += funded["months_with_pass"] * 1200.0
        score += funded.get("months_with_stretch_pass", 0) * 500.0
        score += funded["monthly_pass_rate"] * 20000.0
        score += funded.get("monthly_stretch_pass_rate", 0.0) * 5000.0
        score += max(0.0, pf_effective - 1.0) * 1200.0
        score += result["expectancy"] * 10.0
        score += result["total_pnl"] * 0.2
        score += min(trades, 300) * 8.0
        score -= funded["daily_loss_breaches"] * 1200.0
        score -= 30000.0 if funded.get("trailing_dd_breached", funded["dd_breached"]) else 0.0
        score -= 10000.0 if funded.get("static_dd_breached", False) else 0.0
        if funded["monthly_pass_rate"] <= 0.0:
            score -= 5000.0
    else:
        score += result["total_pnl"]
        score += result["expectancy"] * 25.0
        score += max(0.0, pf_effective - 1.0) * 2000.0
        score += funded["months_with_pass"] * 500.0
        score += funded["monthly_pass_rate"] * 5000.0
        score -= funded["daily_loss_breaches"] * 500.0
        score -= 5000.0 if funded["dd_breached"] else 0.0
        score += min(trades, 300) * 10.0

    return score


def run_component_attribution(df: pd.DataFrame, orb_lookup: Dict, base: StrategyParams) -> pd.DataFrame:
    rows = []

    baseline = backtest(df, orb_lookup, base)
    rows.append({
        "variant": "baseline_all_filters",
        "profit_factor": baseline["profit_factor"],
        "win_rate": baseline["win_rate"],
        "expectancy": baseline["expectancy"],
        "total_pnl": baseline["total_pnl"],
        "trades": baseline["trades"],
        "monthly_pass_rate": baseline["funded"]["monthly_pass_rate"],
    })

    # Test both directions so attribution remains informative even when base already enables a filter.
    tests = [
        ("force_on_volume_filter", {"use_volume": True}),
        ("force_off_volume_filter", {"use_volume": False}),
        ("force_on_displacement_filter", {"use_displacement": True}),
        ("force_off_displacement_filter", {"use_displacement": False}),
        ("force_on_ema_requirement", {"require_ema": True}),
        ("force_off_ema_requirement", {"require_ema": False}),
        ("force_on_vwap_requirement", {"require_vwap": True}),
        ("force_off_vwap_requirement", {"require_vwap": False}),
        ("force_on_liquidity_sweep", {"use_liquidity_sweep": True}),
        ("force_off_liquidity_sweep", {"use_liquidity_sweep": False}),
        ("force_on_bull_rejection", {"use_bull_rejection": True}),
        ("force_off_bull_rejection", {"use_bull_rejection": False}),
        ("force_on_bull_engulfing", {"use_bull_engulfing": True}),
        ("force_off_bull_engulfing", {"use_bull_engulfing": False}),
        ("force_on_bull_mss", {"use_bull_mss": True}),
        ("force_off_bull_mss", {"use_bull_mss": False}),
        ("force_on_bull_fvg", {"use_bull_fvg": True}),
        ("force_off_bull_fvg", {"use_bull_fvg": False}),
        ("force_on_bear_rejection", {"use_bear_rejection": True}),
        ("force_off_bear_rejection", {"use_bear_rejection": False}),
        ("force_on_bear_engulfing", {"use_bear_engulfing": True}),
        ("force_off_bear_engulfing", {"use_bear_engulfing": False}),
        ("force_on_bear_mss", {"use_bear_mss": True}),
        ("force_off_bear_mss", {"use_bear_mss": False}),
        ("force_on_bear_fvg", {"use_bear_fvg": True}),
        ("force_off_bear_fvg", {"use_bear_fvg": False}),
    ]

    for name, patch in tests:
        p = StrategyParams(**asdict(base))
        for k, v in patch.items():
            setattr(p, k, v)
        res = backtest(df, orb_lookup, p)
        rows.append({
            "variant": name,
            "profit_factor": res["profit_factor"],
            "win_rate": res["win_rate"],
            "expectancy": res["expectancy"],
            "total_pnl": res["total_pnl"],
            "trades": res["trades"],
            "monthly_pass_rate": res["funded"]["monthly_pass_rate"],
        })

    out = pd.DataFrame(rows)
    base_row = out.iloc[0]
    out["delta_pf_vs_base"] = out["profit_factor"] - float(base_row["profit_factor"])
    out["delta_exp_vs_base"] = out["expectancy"] - float(base_row["expectancy"])
    out["delta_monthly_pass_vs_base"] = out["monthly_pass_rate"] - float(base_row["monthly_pass_rate"])
    return out


def walk_forward_eval(df: pd.DataFrame,
                      params: StrategyParams,
                      train_years: int = 4,
                      test_years: int = 1,
                      funded_monthly_target: float = 3000.0,
                      funded_monthly_stretch_target: float = 5000.0,
                      funded_daily_loss: float = 2500.0,
                      funded_trailing_max_drawdown: float = 2500.0,
                      funded_static_max_drawdown: float = 2500.0,
                      point_value: float = ES_MULTIPLIER) -> Dict:
    """Simple rolling walk-forward evaluation by calendar years."""
    min_dt = df["datetime"].min()
    max_dt = df["datetime"].max()
    start_year = min_dt.year
    end_year = max_dt.year

    folds = []
    for test_start_year in range(start_year + train_years, end_year - test_years + 2):
        train_start = pd.Timestamp(year=test_start_year - train_years, month=1, day=1)
        train_end = pd.Timestamp(year=test_start_year, month=1, day=1)
        test_end = pd.Timestamp(year=test_start_year + test_years, month=1, day=1)

        train_df = df[(df["datetime"] >= train_start) & (df["datetime"] < train_end)]
        test_df = df[(df["datetime"] >= train_end) & (df["datetime"] < test_end)]

        if train_df.empty or test_df.empty:
            continue

        train_orb = build_orb_lookup(
            train_df,
            orb_start=params.orb_start_min,
            orb_end=params.orb_end_min,
            min_orb_range=params.min_orb_range,
            max_orb_range=params.max_orb_range,
        )
        test_orb = build_orb_lookup(
            test_df,
            orb_start=params.orb_start_min,
            orb_end=params.orb_end_min,
            min_orb_range=params.min_orb_range,
            max_orb_range=params.max_orb_range,
        )

        test_res = backtest(
            test_df,
            test_orb,
            params,
            funded_monthly_target=funded_monthly_target,
            funded_monthly_stretch_target=funded_monthly_stretch_target,
            funded_daily_loss=funded_daily_loss,
            funded_trailing_max_drawdown=funded_trailing_max_drawdown,
            funded_static_max_drawdown=funded_static_max_drawdown,
            point_value=point_value,
        )

        folds.append({
            "train_start": str(train_start.date()),
            "train_end": str((train_end - pd.Timedelta(days=1)).date()),
            "test_start": str(train_end.date()),
            "test_end": str((test_end - pd.Timedelta(days=1)).date()),
            "status": test_res["status"],
            "trades": test_res["trades"],
            "profit_factor": test_res["profit_factor"],
            "expectancy": test_res["expectancy"],
            "total_pnl": test_res["total_pnl"],
            "max_drawdown": test_res["max_drawdown"],
            "monthly_pass_rate": test_res["funded"]["monthly_pass_rate"],
            "monthly_stretch_pass_rate": test_res["funded"]["monthly_stretch_pass_rate"],
            "dd_breached": test_res["funded"]["dd_breached"],
            "trailing_dd_breached": test_res["funded"]["trailing_dd_breached"],
            "static_dd_breached": test_res["funded"]["static_dd_breached"],
        })

    if not folds:
        return {"folds": [], "summary": {"count": 0}}

    fdf = pd.DataFrame(folds)
    summary = {
        "count": int(len(fdf)),
        "avg_pf": float(fdf["profit_factor"].mean()),
        "median_pf": float(fdf["profit_factor"].median()),
        "avg_expectancy": float(fdf["expectancy"].mean()),
        "avg_total_pnl": float(fdf["total_pnl"].mean()),
        "profitable_fold_rate": float((fdf["total_pnl"] > 0).mean()),
        "avg_monthly_pass_rate": float(fdf["monthly_pass_rate"].mean()),
        "avg_monthly_stretch_pass_rate": float(fdf["monthly_stretch_pass_rate"].mean()),
        "dd_breach_rate": float(fdf["dd_breached"].mean()),
        "trailing_dd_breach_rate": float(fdf["trailing_dd_breached"].mean()),
        "static_dd_breach_rate": float(fdf["static_dd_breached"].mean()),
    }
    return {"folds": folds, "summary": summary}


def run_gate_funnel_diagnostics(df: pd.DataFrame, orb_lookup: Dict, params: StrategyParams) -> pd.DataFrame:
    """Count days passing each sequential gate to expose signal choke points."""
    total_orb_days = 0
    stages = {
        "long_raw_breakout_retest": 0,
        "long_plus_ema": 0,
        "long_plus_vwap": 0,
        "long_plus_liquidity_sweep": 0,
        "long_plus_rejection": 0,
        "short_raw_breakout_retest": 0,
        "short_plus_ema": 0,
        "short_plus_vwap": 0,
        "short_plus_liquidity_sweep": 0,
        "short_plus_rejection": 0,
    }

    use_rejection_short = params.use_bear_rejection or params.use_bull_rejection

    for date, day in df.groupby("date", sort=False):
        if date not in orb_lookup:
            continue
        total_orb_days += 1
        orb = orb_lookup[date]

        scan_start = max(params.trade_start_min, params.orb_end_min + 1)
        scan = day[(day["time_min"] >= scan_start) & (day["time_min"] <= params.entry_end_min)]
        if scan.empty:
            continue

        day_low_window = day["low"].rolling(max(1, params.sweep_lookback_bars)).min()
        day_high_window = day["high"].rolling(max(1, params.sweep_lookback_bars)).max()
        day_long_sweep_state = (
            day["prev_day_low"].notna()
            & (day_low_window <= (day["prev_day_low"] + params.sweep_tolerance_pts))
        ).cummax()
        day_short_sweep_state = (
            day["prev_day_high"].notna()
            & (day_high_window >= (day["prev_day_high"] - params.sweep_tolerance_pts))
        ).cummax()
        scan_long_sweep_state = day_long_sweep_state.reindex(scan.index, fill_value=False)
        scan_short_sweep_state = day_short_sweep_state.reindex(scan.index, fill_value=False)

        retest_level_long = orb["orb_low"] + (orb["orb_range"] * params.retest_fraction) + params.retest_tolerance_pts
        retest_level_short = orb["orb_high"] - (orb["orb_range"] * params.retest_fraction) - params.retest_tolerance_pts

        raw_long = (scan["close"] > orb["orb_high"]) & (scan["low"] <= retest_level_long)
        ema_long = raw_long & ((scan["ema20"] > scan["ema50"]) & (scan["ema50"] > scan["ema200"]))
        vwap_long = ema_long & (scan["close"] > scan["vwap"])
        liq_long = vwap_long
        if params.use_liquidity_sweep:
            liq_long = liq_long & scan_long_sweep_state & scan["prev_day_low"].notna() & (scan["close"] >= (scan["prev_day_low"] - params.sweep_tolerance_pts))
        rej_long = liq_long
        if params.use_bull_rejection:
            rej_long = rej_long & (scan["close"] > scan["open"]) & (scan["lower_wick_ratio"] >= params.rejection_wick_ratio)

        raw_short = params.allow_short and ((scan["close"] < orb["orb_low"]) & (scan["high"] >= retest_level_short))
        ema_short = raw_short & ((scan["ema20"] < scan["ema50"]) & (scan["ema50"] < scan["ema200"]))
        vwap_short = ema_short & (scan["close"] < scan["vwap"])
        liq_short = vwap_short
        if params.use_liquidity_sweep:
            liq_short = liq_short & scan_short_sweep_state & scan["prev_day_high"].notna() & (scan["close"] <= (scan["prev_day_high"] + params.sweep_tolerance_pts))
        rej_short = liq_short
        if use_rejection_short:
            rej_short = rej_short & (scan["close"] < scan["open"]) & (scan["upper_wick_ratio"] >= params.rejection_wick_ratio)

        stages["long_raw_breakout_retest"] += int(bool(raw_long.any()))
        stages["long_plus_ema"] += int(bool(ema_long.any()))
        stages["long_plus_vwap"] += int(bool(vwap_long.any()))
        stages["long_plus_liquidity_sweep"] += int(bool(liq_long.any()))
        stages["long_plus_rejection"] += int(bool(rej_long.any()))

        stages["short_raw_breakout_retest"] += int(bool(pd.Series(raw_short).any()))
        stages["short_plus_ema"] += int(bool(pd.Series(ema_short).any()))
        stages["short_plus_vwap"] += int(bool(pd.Series(vwap_short).any()))
        stages["short_plus_liquidity_sweep"] += int(bool(pd.Series(liq_short).any()))
        stages["short_plus_rejection"] += int(bool(pd.Series(rej_short).any()))

    rows = []
    for stage, count in stages.items():
        rows.append({
            "stage": stage,
            "days_passed": int(count),
            "orb_days": int(total_orb_days),
            "pct_of_orb_days": float(count / total_orb_days) if total_orb_days else 0.0,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize ORB V2 with funded-account constraints")
    parser.add_argument("--data", default="ES_backtest_data.csv")
    parser.add_argument("--trials", type=int, default=80)
    parser.add_argument("--years", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--param-profile", choices=["broad", "funded_live_like"], default="broad")
    parser.add_argument("--min-trades", type=int, default=30)
    parser.add_argument("--min-months", type=int, default=12)
    parser.add_argument("--score-profile", choices=["balanced", "cadence"], default="balanced")
    parser.add_argument("--funded-monthly-target", type=float, default=3000.0)
    parser.add_argument("--funded-monthly-stretch-target", type=float, default=5000.0)
    parser.add_argument("--funded-daily-loss", type=float, default=2500.0)
    parser.add_argument("--funded-trailing-max-drawdown", type=float, default=2500.0)
    parser.add_argument("--funded-static-max-drawdown", type=float, default=2500.0)
    parser.add_argument("--point-value", type=float, default=50.0)
    parser.add_argument("--force-allow-short", action="store_true")
    parser.add_argument("--force-use-liquidity-sweep", action="store_true")
    parser.add_argument("--force-use-bull-rejection", action="store_true")
    parser.add_argument("--force-max-trades-per-day", type=int, choices=[1, 2], default=0)
    parser.add_argument("--force-second-trade-only-after-loss", action="store_true")
    parser.add_argument("--force-trade-start-min", type=int, default=-1)
    parser.add_argument("--force-entry-end-min", type=int, default=-1)
    parser.add_argument("--force-strategy-daily-loss-stop-usd", type=float, default=-1.0)
    parser.add_argument("--force-sweep-tolerance-pts", type=float, default=-1.0)
    parser.add_argument("--force-sweep-lookback-bars", type=int, default=-1)
    parser.add_argument("--force-rejection-wick-ratio", type=float, default=-1.0)
    parser.add_argument("--outdir", default="trading_os/experiments/outputs")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Loading and preparing data...")
    df = load_data(Path(args.data), years=args.years)
    # Cache ORB lookup by ORB definition so trials can vary ORB without repeated recomputation.
    orb_cache: Dict[Tuple[int, int, float, float], Dict] = {}

    def get_orb_lookup_for_params(p: StrategyParams) -> Dict:
        key = (p.orb_start_min, p.orb_end_min, p.min_orb_range, p.max_orb_range)
        if key not in orb_cache:
            orb_cache[key] = build_orb_lookup(
                df,
                orb_start=p.orb_start_min,
                orb_end=p.orb_end_min,
                min_orb_range=p.min_orb_range,
                max_orb_range=p.max_orb_range,
            )
        return orb_cache[key]

    baseline_orb_lookup = get_orb_lookup_for_params(StrategyParams())

    print(f"Bars: {len(df):,} | Baseline days with valid ORB: {len(baseline_orb_lookup):,}")
    print(f"Date range: {df['datetime'].min()} -> {df['datetime'].max()}")

    baseline_params = StrategyParams()
    baseline = backtest(
        df,
        baseline_orb_lookup,
        baseline_params,
        funded_monthly_target=args.funded_monthly_target,
        funded_monthly_stretch_target=args.funded_monthly_stretch_target,
        funded_daily_loss=args.funded_daily_loss,
        funded_trailing_max_drawdown=args.funded_trailing_max_drawdown,
        funded_static_max_drawdown=args.funded_static_max_drawdown,
        point_value=args.point_value,
    )

    print("Running optimization sweep...")
    rng = random.Random(args.seed)
    grid = sample_param_space(rng, args.trials, profile=args.param_profile)

    ranked: List[Dict] = []
    for i, p in enumerate(grid, start=1):
        if args.force_allow_short:
            p.allow_short = True
        if args.force_use_liquidity_sweep:
            p.use_liquidity_sweep = True
        if args.force_use_bull_rejection:
            p.use_bull_rejection = True
        if args.force_max_trades_per_day in (1, 2):
            p.max_trades_per_day = args.force_max_trades_per_day
        if args.force_second_trade_only_after_loss:
            p.second_trade_only_after_loss = True
        if args.force_trade_start_min >= 0:
            p.trade_start_min = args.force_trade_start_min
        if args.force_entry_end_min >= 0:
            p.entry_end_min = args.force_entry_end_min
        if args.force_strategy_daily_loss_stop_usd >= 0:
            p.strategy_daily_loss_stop_usd = args.force_strategy_daily_loss_stop_usd
        if args.force_sweep_tolerance_pts >= 0:
            p.sweep_tolerance_pts = args.force_sweep_tolerance_pts
        if args.force_sweep_lookback_bars > 0:
            p.sweep_lookback_bars = args.force_sweep_lookback_bars
        if args.force_rejection_wick_ratio >= 0:
            p.rejection_wick_ratio = args.force_rejection_wick_ratio

        trial_orb_lookup = get_orb_lookup_for_params(p)
        res = backtest(
            df,
            trial_orb_lookup,
            p,
            funded_monthly_target=args.funded_monthly_target,
            funded_monthly_stretch_target=args.funded_monthly_stretch_target,
            funded_daily_loss=args.funded_daily_loss,
            funded_trailing_max_drawdown=args.funded_trailing_max_drawdown,
            funded_static_max_drawdown=args.funded_static_max_drawdown,
            point_value=args.point_value,
        )
        score = score_result(
            res,
            min_trades=args.min_trades,
            min_months=args.min_months,
            profile=args.score_profile,
        )
        ranked.append({
            "trial": i,
            "score": score,
            "params": asdict(p),
            "status": res["status"],
            "trades": res["trades"],
            "win_rate": res["win_rate"],
            "profit_factor": res["profit_factor"],
            "expectancy": res["expectancy"],
            "total_pnl": res["total_pnl"],
            "max_drawdown": res["max_drawdown"],
            "funded": res["funded"],
        })

        if i % 10 == 0:
            print(f"Completed {i}/{len(grid)} trials...", flush=True)

    ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)
    top = ranked[:10]

    best_params = StrategyParams(**top[0]["params"])
    best_orb_lookup = get_orb_lookup_for_params(best_params)
    attribution = run_component_attribution(df, best_orb_lookup, best_params)
    wf = walk_forward_eval(
        df,
        best_params,
        train_years=4,
        test_years=1,
        funded_monthly_target=args.funded_monthly_target,
        funded_monthly_stretch_target=args.funded_monthly_stretch_target,
        funded_daily_loss=args.funded_daily_loss,
        funded_trailing_max_drawdown=args.funded_trailing_max_drawdown,
        funded_static_max_drawdown=args.funded_static_max_drawdown,
        point_value=args.point_value,
    )
    gate_funnel = run_gate_funnel_diagnostics(df, best_orb_lookup, best_params)

    pd.DataFrame(top).to_json(outdir / "orb_v2_optimizer_top10.json", orient="records", indent=2)
    pd.DataFrame(ranked).head(50).to_csv(outdir / "orb_v2_optimizer_top50.csv", index=False)
    attribution.to_csv(outdir / "orb_v2_component_attribution.csv", index=False)
    pd.DataFrame(wf.get("folds", [])).to_csv(outdir / "orb_v2_walkforward_folds.csv", index=False)
    gate_funnel.to_csv(outdir / "orb_v2_gate_funnel.csv", index=False)

    summary = {
        "dataset": {
            "bars": int(len(df)),
            "valid_orb_days": int(len(baseline_orb_lookup)),
            "start": str(df["datetime"].min()),
            "end": str(df["datetime"].max()),
            "years": args.years,
            "score_profile": args.score_profile,
            "param_profile": args.param_profile,
            "point_value": args.point_value,
        },
        "baseline": {
            "params": asdict(baseline_params),
            "status": baseline["status"],
            "trades": baseline["trades"],
            "win_rate": baseline["win_rate"],
            "profit_factor": baseline["profit_factor"],
            "expectancy": baseline["expectancy"],
            "total_pnl": baseline["total_pnl"],
            "max_drawdown": baseline["max_drawdown"],
            "funded": baseline["funded"],
        },
        "best_trial": top[0],
        "walk_forward": wf,
        "artifacts": {
            "top10_json": str(outdir / "orb_v2_optimizer_top10.json"),
            "top50_csv": str(outdir / "orb_v2_optimizer_top50.csv"),
            "component_csv": str(outdir / "orb_v2_component_attribution.csv"),
            "walkforward_csv": str(outdir / "orb_v2_walkforward_folds.csv"),
            "gate_funnel_csv": str(outdir / "orb_v2_gate_funnel.csv"),
        },
    }

    with open(outdir / "orb_v2_optimizer_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Optimization complete.")
    print("Baseline:", baseline["trades"], "trades | PF", round(baseline["profit_factor"], 3), "| PnL", round(baseline["total_pnl"], 2))
    print("Best:", top[0]["trades"], "trades | PF", round(top[0]["profit_factor"], 3), "| PnL", round(top[0]["total_pnl"], 2))
    print("Best funded monthly pass rate:", round(top[0]["funded"]["monthly_pass_rate"], 3))


if __name__ == "__main__":
    main()
