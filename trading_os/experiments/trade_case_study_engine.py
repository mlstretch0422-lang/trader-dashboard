#!/usr/bin/env python3
"""Generate per-trade case studies for the control strategy.

Purpose:
- Move from pattern ranking to trade-level intelligence.
- Explain likely reasons each trade worked or failed.
- Isolate near-miss trades where most conditions aligned but final outcome failed.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

import pandas as pd

from orb_v2_optimizer import StrategyParams, backtest, build_orb_lookup, load_data

BASELINE_SUMMARY_PATH = Path(
    "trading_os/experiments/outputs/opt_funded_recovery_260_retryD/orb_v2_optimizer_summary.json"
)
SESSION_CONTEXT_PATH = Path("trading_os/experiments/outputs/session_context_features.csv")
OUTDIR = Path("trading_os/experiments/outputs/trade_case_study_2026-07-08")


def _load_control_params() -> StrategyParams:
    summary = json.loads(BASELINE_SUMMARY_PATH.read_text(encoding="utf-8"))
    p = StrategyParams(**summary["best_trial"]["params"])
    p.max_trades_per_day = 1
    p.trade_start_min = 570
    p.entry_end_min = 630
    p.strategy_daily_loss_stop_usd = 200.0
    return p


def _compute_trade_excursions(df: pd.DataFrame, trades: pd.DataFrame, point_value: float = 50.0) -> pd.DataFrame:
    if trades.empty:
        return trades

    bars = df.copy().set_index("datetime", drop=False)
    t = trades.copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"])
    t["exit_time"] = pd.to_datetime(t["exit_time"])

    mfe_pts: List[float] = []
    mae_pts: List[float] = []

    for row in t.itertuples(index=False):
        seg = bars[(bars.index >= row.entry_time) & (bars.index <= row.exit_time)]
        if seg.empty:
            mfe_pts.append(0.0)
            mae_pts.append(0.0)
            continue

        if row.side == "LONG":
            mfe = float(seg["high"].max() - row.entry_price)
            mae = float(row.entry_price - seg["low"].min())
        else:
            mfe = float(row.entry_price - seg["low"].min())
            mae = float(seg["high"].max() - row.entry_price)

        mfe_pts.append(max(mfe, 0.0))
        mae_pts.append(max(mae, 0.0))

    t["mfe_pts"] = mfe_pts
    t["mae_pts"] = mae_pts
    t["mfe_usd"] = t["mfe_pts"] * point_value
    t["mae_usd"] = t["mae_pts"] * point_value
    return t


def _enrich_with_entry_features(df: pd.DataFrame, trades: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    bars = df.copy().set_index("datetime", drop=False)

    swing_high = bars["high"].rolling(params.mss_lookback).max().shift(1)
    swing_low = bars["low"].rolling(params.mss_lookback).min().shift(1)
    bars["bull_mss_now"] = swing_high.notna() & (bars["close"] > swing_high)
    bars["bear_mss_now"] = swing_low.notna() & (bars["close"] < swing_low)

    entry_cols = [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "ema20",
        "ema50",
        "ema200",
        "vwap",
        "avg_vol_20",
        "avg_body_20",
        "body",
        "lower_wick_ratio",
        "upper_wick_ratio",
        "bull_rejection",
        "bear_rejection",
        "bull_engulfing",
        "bear_engulfing",
        "bull_mss_now",
        "bear_mss_now",
        "prev_day_high",
        "prev_day_low",
        "daily_atr14",
    ]

    entry_bars = bars[entry_cols].rename(columns={"datetime": "entry_time"}).reset_index(drop=True)

    t = trades.copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"])
    t["exit_time"] = pd.to_datetime(t["exit_time"])
    t["date"] = t["entry_time"].dt.date
    t["entry_time_min"] = t["entry_time"].dt.hour * 60 + t["entry_time"].dt.minute
    t["minutes_from_ny_open"] = t["entry_time_min"] - (9 * 60 + 30)
    t["entry_year"] = t["entry_time"].dt.year
    t["is_win"] = t["pnl_usd"] > 0
    t["is_loss"] = t["pnl_usd"] < 0

    out = t.merge(entry_bars, on="entry_time", how="left")

    out["ema_stack_bull"] = (out["ema20"] > out["ema50"]) & (out["ema50"] > out["ema200"])
    out["ema_stack_bear"] = (out["ema20"] < out["ema50"]) & (out["ema50"] < out["ema200"])
    out["vwap_bull"] = out["close"] > out["vwap"]
    out["vwap_bear"] = out["close"] < out["vwap"]
    out["vol_ratio_20"] = out["volume"] / out["avg_vol_20"]
    out["body_ratio_20"] = out["body"] / out["avg_body_20"]

    return out


def _add_session_context(features: pd.DataFrame) -> pd.DataFrame:
    if not SESSION_CONTEXT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {SESSION_CONTEXT_PATH}; run build_session_context_features.py first."
        )

    ctx = pd.read_csv(SESSION_CONTEXT_PATH)
    ctx["date"] = pd.to_datetime(ctx["date"]).dt.date

    keep_cols = [
        "date",
        "asia_high",
        "asia_low",
        "london_high",
        "london_low",
        "overnight_range",
        "ny_open",
        "ny_open_pos_in_asia_range",
        "ny_open_pos_in_london_range",
        "swept_asia_low_preopen",
        "swept_asia_high_preopen",
        "swept_london_low_preopen",
        "swept_london_high_preopen",
        "dist_ny_open_to_nearest_pool",
    ]

    return features.merge(ctx[keep_cols], on="date", how="left")


def _trade_narrative_row(row: pd.Series) -> Dict:
    side = str(row["side"])
    if side == "LONG":
        htf_bias = "Bullish" if bool(row.get("ema_stack_bull", False)) else "Mixed/Not Bull Stack"
        expectation = "Sweep downside liquidity then reclaim and rotate higher"
        sweep_observed = bool(row.get("swept_asia_low_preopen", False) or row.get("swept_london_low_preopen", False))
        response_confirmed = bool(row.get("bull_rejection", False) or row.get("bull_engulfing", False) or row.get("bull_mss_now", False))
        vwap_align = bool(row.get("vwap_bull", False))
        ema_align = bool(row.get("ema_stack_bull", False))
        target = f"Prior day high {row.get('prev_day_high', float('nan')):.2f}" if pd.notna(row.get("prev_day_high")) else "Prior day high"
    else:
        htf_bias = "Bearish" if bool(row.get("ema_stack_bear", False)) else "Mixed/Not Bear Stack"
        expectation = "Sweep upside liquidity then reclaim down and rotate lower"
        sweep_observed = bool(row.get("swept_asia_high_preopen", False) or row.get("swept_london_high_preopen", False))
        response_confirmed = bool(row.get("bear_rejection", False) or row.get("bear_engulfing", False) or row.get("bear_mss_now", False))
        vwap_align = bool(row.get("vwap_bear", False))
        ema_align = bool(row.get("ema_stack_bear", False))
        target = f"Prior day low {row.get('prev_day_low', float('nan')):.2f}" if pd.notna(row.get("prev_day_low")) else "Prior day low"

    checklist = {
        "sweep_context": sweep_observed,
        "response_confirmed": response_confirmed,
        "vwap_aligned": vwap_align,
        "ema_aligned": ema_align,
        "room_to_liquidity": bool(pd.notna(row.get("dist_ny_open_to_nearest_pool")) and row.get("dist_ny_open_to_nearest_pool") >= 3.0),
        "volatility_ok": bool(pd.notna(row.get("daily_atr14")) and 30.0 <= row.get("daily_atr14") <= 80.0),
    }
    checklist_score = int(sum(checklist.values()))

    if row.get("pnl_usd", 0.0) > 0:
        likely_why = "Expectation-response sequence held with sufficient alignment and follow-through."
    else:
        likely_why = "One or more alignment/response conditions failed to produce sustained continuation."

    narrative_path = (
        f"{('Downside' if side == 'LONG' else 'Upside')} liquidity interaction"
        f" -> response {'confirmed' if response_confirmed else 'weak/absent'}"
        f" -> {'alignment present' if (vwap_align and ema_align) else 'alignment mixed'}"
        f" -> result {'positive' if row.get('pnl_usd', 0.0) > 0 else 'negative/non-winning'}"
    )

    return {
        "trade_id": None,
        "entry_time": row.get("entry_time"),
        "exit_time": row.get("exit_time"),
        "date": row.get("date"),
        "side": side,
        "htf_bias_label": htf_bias,
        "expectation_label": expectation,
        "sweep_observed": sweep_observed,
        "response_confirmed": response_confirmed,
        "mss_confirmed": bool(row.get("bull_mss_now", False) or row.get("bear_mss_now", False)),
        "vwap_aligned": vwap_align,
        "ema_aligned": ema_align,
        "liquidity_target_label": target,
        "result_pnl_usd": float(row.get("pnl_usd", 0.0)),
        "mfe_pts": float(row.get("mfe_pts", 0.0)),
        "mae_pts": float(row.get("mae_pts", 0.0)),
        "minutes_from_ny_open": int(row.get("minutes_from_ny_open", 0)),
        "dist_ny_open_to_nearest_pool": float(row.get("dist_ny_open_to_nearest_pool", float("nan"))),
        "checklist_score": checklist_score,
        "checklist_sweep_context": checklist["sweep_context"],
        "checklist_response_confirmed": checklist["response_confirmed"],
        "checklist_vwap_aligned": checklist["vwap_aligned"],
        "checklist_ema_aligned": checklist["ema_aligned"],
        "checklist_room_to_liquidity": checklist["room_to_liquidity"],
        "checklist_volatility_ok": checklist["volatility_ok"],
        "narrative_path": narrative_path,
        "why_likely_worked_or_failed": likely_why,
    }


def _build_case_studies(features: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict] = []
    for i, row in enumerate(features.to_dict(orient="records"), start=1):
        enriched = _trade_narrative_row(pd.Series(row))
        enriched["trade_id"] = i
        rows.append(enriched)

    out = pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)

    # Near miss: high checklist and positive excursion but final non-winning outcome.
    out["is_near_miss"] = (
        (out["result_pnl_usd"] <= 0)
        & (out["checklist_score"] >= 4)
        & (out["mfe_pts"] >= 6.0)
    )

    out["grade_label"] = "Skip"
    out.loc[(out["checklist_score"] >= 5) & (out["result_pnl_usd"] > 0), "grade_label"] = "A+"
    out.loc[(out["checklist_score"] >= 4) & (out["result_pnl_usd"] > 0), "grade_label"] = "A"
    out.loc[(out["checklist_score"] >= 3), "grade_label"] = out.loc[(out["checklist_score"] >= 3), "grade_label"].replace("Skip", "B")

    return out


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    p = _load_control_params()
    df = load_data(Path("ES_backtest_data.csv"), years=8)

    orb = build_orb_lookup(df, p.orb_start_min, p.orb_end_min, p.min_orb_range, p.max_orb_range)
    res = backtest(
        df,
        orb,
        p,
        funded_monthly_target=3000.0,
        funded_monthly_stretch_target=5000.0,
        funded_daily_loss=2000.0,
        funded_trailing_max_drawdown=2500.0,
        funded_static_max_drawdown=3000.0,
        point_value=50.0,
    )

    trades = _compute_trade_excursions(df, res["trades_df"].copy(), point_value=50.0)
    if trades.empty:
        raise RuntimeError("No trades found for control configuration.")

    features = _enrich_with_entry_features(df, trades, p)
    features = _add_session_context(features)

    studies = _build_case_studies(features)

    winners = studies[studies["result_pnl_usd"] > 0].copy().sort_values("result_pnl_usd", ascending=False)
    losers = studies[studies["result_pnl_usd"] < 0].copy().sort_values("result_pnl_usd", ascending=True)
    near_miss = studies[studies["is_near_miss"]].copy().sort_values(["checklist_score", "mfe_pts"], ascending=[False, False])

    studies.to_csv(OUTDIR / "trade_case_studies_all.csv", index=False)
    winners.to_csv(OUTDIR / "trade_case_studies_winners.csv", index=False)
    losers.to_csv(OUTDIR / "trade_case_studies_losers.csv", index=False)
    near_miss.to_csv(OUTDIR / "trade_case_studies_near_misses.csv", index=False)

    summary = {
        "control_metrics": {
            "trades": int(res["trades"]),
            "profit_factor": float(res["profit_factor"]),
            "expectancy": float(res["expectancy"]),
            "total_pnl": float(res["total_pnl"]),
        },
        "case_study_counts": {
            "all": int(len(studies)),
            "winners": int(len(winners)),
            "losers": int(len(losers)),
            "near_misses": int(len(near_miss)),
        },
        "notes": [
            "This is a trade intelligence artifact, not an optimization run.",
            "Near misses are non-winning trades with high alignment score and meaningful MFE.",
            "If sample count is below requested targets (e.g., 100 winners), use all available trades.",
        ],
        "artifacts": {
            "all_csv": str(OUTDIR / "trade_case_studies_all.csv"),
            "winners_csv": str(OUTDIR / "trade_case_studies_winners.csv"),
            "losers_csv": str(OUTDIR / "trade_case_studies_losers.csv"),
            "near_misses_csv": str(OUTDIR / "trade_case_studies_near_misses.csv"),
        },
        "params": asdict(p),
    }

    (OUTDIR / "trade_case_study_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("WROTE", OUTDIR / "trade_case_study_summary.json")
    print(
        "Counts | all:",
        len(studies),
        "winners:",
        len(winners),
        "losers:",
        len(losers),
        "near_misses:",
        len(near_miss),
    )
    print("Top 5 winners:")
    print(winners[["trade_id", "entry_time", "side", "result_pnl_usd", "mfe_pts", "checklist_score", "narrative_path"]].head(5).to_string(index=False))
    print("Top 5 near misses:")
    print(near_miss[["trade_id", "entry_time", "side", "result_pnl_usd", "mfe_pts", "checklist_score", "narrative_path"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
