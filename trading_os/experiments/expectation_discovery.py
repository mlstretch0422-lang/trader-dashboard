#!/usr/bin/env python3
"""Discover expectation signals from control trades.

This module is intentionally discovery-only:
- No optimizer sweeps
- No strategy logic changes
- No parameter tuning

It extracts recurring characteristics across multiple cohorts so future
hypotheses originate from evidence instead of brainstorming.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from orb_v2_optimizer import StrategyParams, backtest, build_orb_lookup, load_data


BASELINE_SUMMARY_PATH = Path(
    "trading_os/experiments/outputs/opt_funded_recovery_260_retryD/orb_v2_optimizer_summary.json"
)
SESSION_CONTEXT_PATH = Path("trading_os/experiments/outputs/session_context_features.csv")
OUTDIR = Path("trading_os/experiments/outputs/expectation_discovery_2026-07-08")


def _load_control_params() -> StrategyParams:
    summary = json.loads(BASELINE_SUMMARY_PATH.read_text(encoding="utf-8"))
    p = StrategyParams(**summary["best_trial"]["params"])
    # Freeze known project constraints for comparability.
    p.max_trades_per_day = 1
    p.trade_start_min = 570
    p.entry_end_min = 630
    p.strategy_daily_loss_stop_usd = 200.0
    return p


def _entry_feature_frame(df: pd.DataFrame, trades: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    bars = df.copy().set_index("datetime", drop=False)

    swing_high = bars["high"].rolling(params.mss_lookback).max().shift(1)
    swing_low = bars["low"].rolling(params.mss_lookback).min().shift(1)
    bars["bull_mss_now"] = swing_high.notna() & (bars["close"] > swing_high)
    bars["bear_mss_now"] = swing_low.notna() & (bars["close"] < swing_low)

    t = trades.copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"])
    t["exit_time"] = pd.to_datetime(t["exit_time"])
    t["date"] = t["entry_time"].dt.date
    t["entry_time_min"] = t["entry_time"].dt.hour * 60 + t["entry_time"].dt.minute
    t["minutes_from_ny_open"] = t["entry_time_min"] - (9 * 60 + 30)
    t["is_win"] = t["pnl_usd"] > 0

    cols = [
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
        "bull_fvg",
        "bear_fvg",
        "bull_mss_now",
        "bear_mss_now",
        "daily_atr14",
    ]
    entry_bars = bars[cols].rename(columns={"datetime": "entry_time"}).reset_index(drop=True)

    merged = t.merge(entry_bars, on="entry_time", how="left")

    merged["ema_stack_bull"] = (merged["ema20"] > merged["ema50"]) & (merged["ema50"] > merged["ema200"])
    merged["ema_stack_bear"] = (merged["ema20"] < merged["ema50"]) & (merged["ema50"] < merged["ema200"])
    merged["vwap_bull"] = merged["close"] > merged["vwap"]
    merged["vwap_bear"] = merged["close"] < merged["vwap"]
    merged["vol_ratio_20"] = np.where(merged["avg_vol_20"] > 0, merged["volume"] / merged["avg_vol_20"], np.nan)
    merged["body_ratio_20"] = np.where(merged["avg_body_20"] > 0, merged["body"] / merged["avg_body_20"], np.nan)
    merged["vwap_dist_pts"] = (merged["close"] - merged["vwap"]).abs()
    merged["entry_year"] = merged["entry_time"].dt.year
    merged["is_loss"] = merged["pnl_usd"] < 0
    merged["is_non_winner"] = merged["pnl_usd"] <= 0
    merged["is_breakeven"] = merged["pnl_usd"] == 0

    return merged


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
            mfe = float((seg["high"].max() - row.entry_price))
            mae = float((row.entry_price - seg["low"].min()))
        else:
            mfe = float((row.entry_price - seg["low"].min()))
            mae = float((seg["high"].max() - row.entry_price))

        mfe_pts.append(max(mfe, 0.0))
        mae_pts.append(max(mae, 0.0))

    t["mfe_pts"] = mfe_pts
    t["mae_pts"] = mae_pts
    t["mfe_usd"] = t["mfe_pts"] * point_value
    t["mae_usd"] = t["mae_pts"] * point_value
    return t


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
        "overnight_high",
        "overnight_low",
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

    out = features.merge(ctx[keep_cols], on="date", how="left")
    return out


def _bool_pattern_table(df_all: pd.DataFrame, df_focus: pd.DataFrame, bool_cols: List[str]) -> pd.DataFrame:
    rows = []
    for col in bool_cols:
        base = float(df_all[col].fillna(False).mean()) if len(df_all) else 0.0
        focus = float(df_focus[col].fillna(False).mean()) if len(df_focus) else 0.0
        rows.append(
            {
                "feature": col,
                "focus_support": focus,
                "all_support": base,
                "support_uplift": focus - base,
                "focus_count": int(df_focus[col].fillna(False).sum()) if len(df_focus) else 0,
                "all_count": int(df_all[col].fillna(False).sum()) if len(df_all) else 0,
            }
        )

    out = pd.DataFrame(rows).sort_values(["support_uplift", "focus_support"], ascending=[False, False])
    return out


def _numeric_pattern_table(df_all: pd.DataFrame, df_focus: pd.DataFrame, num_cols: List[str]) -> pd.DataFrame:
    rows = []
    for col in num_cols:
        s_all = pd.to_numeric(df_all[col], errors="coerce").dropna()
        s_focus = pd.to_numeric(df_focus[col], errors="coerce").dropna()
        if s_all.empty or s_focus.empty:
            continue

        rows.append(
            {
                "feature": col,
                "focus_mean": float(s_focus.mean()),
                "all_mean": float(s_all.mean()),
                "mean_delta": float(s_focus.mean() - s_all.mean()),
                "focus_median": float(s_focus.median()),
                "all_median": float(s_all.median()),
                "median_delta": float(s_focus.median() - s_all.median()),
                "focus_q25": float(s_focus.quantile(0.25)),
                "focus_q75": float(s_focus.quantile(0.75)),
                "focus_count": int(len(s_focus)),
                "all_count": int(len(s_all)),
            }
        )

    out = pd.DataFrame(rows).sort_values(["median_delta", "mean_delta"], ascending=[False, False])
    return out


def _pattern_stability_matrix(features: pd.DataFrame, bool_cols: List[str]) -> pd.DataFrame:
    wins = features[features["is_win"]]
    losses = features[features["is_loss"]]
    non_winners = features[features["is_non_winner"]]

    top_win_threshold = float(wins["pnl_usd"].quantile(0.75)) if len(wins) else np.nan
    top_wins = wins[wins["pnl_usd"] >= top_win_threshold] if len(wins) else wins

    high_mfe_threshold = float(features["mfe_pts"].quantile(0.75))
    high_mfe = features[features["mfe_pts"] >= high_mfe_threshold]

    rows = []
    for col in bool_cols:
        s_all = features[col].fillna(False)
        s_w = wins[col].fillna(False) if len(wins) else pd.Series(dtype=bool)
        s_l = losses[col].fillna(False) if len(losses) else pd.Series(dtype=bool)
        s_nw = non_winners[col].fillna(False) if len(non_winners) else pd.Series(dtype=bool)
        s_tw = top_wins[col].fillna(False) if len(top_wins) else pd.Series(dtype=bool)
        s_mfe = high_mfe[col].fillna(False) if len(high_mfe) else pd.Series(dtype=bool)

        support_all = float(s_all.mean()) if len(s_all) else 0.0
        support_w = float(s_w.mean()) if len(s_w) else 0.0
        support_l = float(s_l.mean()) if len(s_l) else 0.0
        support_nw = float(s_nw.mean()) if len(s_nw) else 0.0
        support_tw = float(s_tw.mean()) if len(s_tw) else 0.0
        support_mfe = float(s_mfe.mean()) if len(s_mfe) else 0.0

        rows.append(
            {
                "feature": col,
                "support_all": support_all,
                "support_wins": support_w,
                "support_losses": support_l,
                "support_non_winners": support_nw,
                "support_top_wins": support_tw,
                "support_high_mfe": support_mfe,
                "uplift_win_vs_loss": support_w - support_l,
                "uplift_win_vs_non_winner": support_w - support_nw,
                "uplift_high_mfe_vs_all": support_mfe - support_all,
                "appears_in_all_winners": bool(np.isclose(support_w, 1.0)),
                "appears_in_losses_too": bool(support_l > 0.5),
                "separates_mfe_more_than_pnl": bool((support_mfe - support_all) > (support_w - support_nw)),
                "wins_count": int(len(wins)),
                "losses_count": int(len(losses)),
                "top_wins_count": int(len(top_wins)),
                "high_mfe_count": int(len(high_mfe)),
            }
        )

    return pd.DataFrame(rows).sort_values(["uplift_win_vs_non_winner", "uplift_win_vs_loss"], ascending=[False, False])


def _year_and_fold_stability(features: pd.DataFrame, bool_cols: List[str]) -> pd.DataFrame:
    # Simple temporal folds to check stability beyond single-year noise.
    tmp = features.copy()
    tmp["fold_id"] = ((tmp["entry_year"] - tmp["entry_year"].min()) // 2) + 1

    rows = []
    for col in bool_cols:
        w = tmp[tmp["is_win"]]
        if w.empty:
            continue

        by_year = w.groupby("entry_year")[col].mean()
        by_fold = w.groupby("fold_id")[col].mean()
        rows.append(
            {
                "feature": col,
                "winner_support_overall": float(w[col].mean()),
                "winner_support_year_min": float(by_year.min()) if len(by_year) else np.nan,
                "winner_support_year_max": float(by_year.max()) if len(by_year) else np.nan,
                "winner_support_year_std": float(by_year.std(ddof=0)) if len(by_year) else np.nan,
                "winner_year_groups": int(len(by_year)),
                "winner_support_fold_min": float(by_fold.min()) if len(by_fold) else np.nan,
                "winner_support_fold_max": float(by_fold.max()) if len(by_fold) else np.nan,
                "winner_support_fold_std": float(by_fold.std(ddof=0)) if len(by_fold) else np.nan,
                "winner_fold_groups": int(len(by_fold)),
                "stable_by_year_flag": bool(len(by_year) >= 2 and (by_year.std(ddof=0) <= 0.25)),
                "stable_by_fold_flag": bool(len(by_fold) >= 2 and (by_fold.std(ddof=0) <= 0.2)),
            }
        )

    return pd.DataFrame(rows).sort_values(["stable_by_year_flag", "winner_support_overall"], ascending=[False, False])


def _loser_overlap_with_winner_profile(features: pd.DataFrame, bool_stability: pd.DataFrame) -> pd.DataFrame:
    wins = features[features["is_win"]]
    losses = features[features["is_loss"]]
    if wins.empty or losses.empty or bool_stability.empty:
        pd.DataFrame(columns=[
            "group", "trades", "full_match_count", "full_match_rate", "avg_match_count", "core_features"
        ]).to_csv(OUTDIR / "loser_overlap_winner_profile.csv", index=False)
        pd.DataFrame().to_csv(OUTDIR / "losing_trades_matching_winner_profile.csv", index=False)
        return pd.DataFrame()

    # Winner profile = strongest winner-vs-non-winner lifts with broad winner support.
    core = bool_stability[
        (bool_stability["support_wins"] >= 0.65)
        & (bool_stability["uplift_win_vs_non_winner"] >= 0.15)
    ]["feature"].head(4).tolist()

    if not core:
        pd.DataFrame(columns=[
            "group", "trades", "full_match_count", "full_match_rate", "avg_match_count", "core_features"
        ]).to_csv(OUTDIR / "loser_overlap_winner_profile.csv", index=False)
        pd.DataFrame().to_csv(OUTDIR / "losing_trades_matching_winner_profile.csv", index=False)
        return pd.DataFrame()

    out = features.copy()
    for c in core:
        out[c] = out[c].fillna(False)

    out["winner_profile_match_count"] = out[core].sum(axis=1)
    out["winner_profile_full_match"] = out["winner_profile_match_count"] == len(core)

    rows = []
    for grp_name, grp in [("wins", wins), ("losses", losses)]:
        idx = out.loc[grp.index]
        rows.append(
            {
                "group": grp_name,
                "trades": int(len(idx)),
                "full_match_count": int(idx["winner_profile_full_match"].sum()),
                "full_match_rate": float(idx["winner_profile_full_match"].mean()) if len(idx) else 0.0,
                "avg_match_count": float(idx["winner_profile_match_count"].mean()) if len(idx) else 0.0,
                "core_features": ",".join(core),
            }
        )

    # Add specific list of losing trades that matched winner profile.
    losing_matches = out[(out["is_loss"]) & (out["winner_profile_full_match"])]
    if not losing_matches.empty:
        losing_matches[[
            "entry_time", "exit_time", "side", "pnl_usd", "mfe_pts", "mae_pts", "winner_profile_match_count"
        ] + core].to_csv(OUTDIR / "losing_trades_matching_winner_profile.csv", index=False)
    else:
        pd.DataFrame(columns=[
            "entry_time", "exit_time", "side", "pnl_usd", "mfe_pts", "mae_pts", "winner_profile_match_count"
        ] + core).to_csv(OUTDIR / "losing_trades_matching_winner_profile.csv", index=False)

    out = pd.DataFrame(rows)
    out.to_csv(OUTDIR / "loser_overlap_winner_profile.csv", index=False)
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
        raise RuntimeError("Control backtest returned zero trades; cannot run discovery.")

    features = _entry_feature_frame(df, trades, p)
    features = _add_session_context(features)

    wins = features[features["is_win"]].copy()
    if wins.empty:
        raise RuntimeError("No winning trades in control set; cannot run discovery.")

    win_pnl_threshold = float(wins["pnl_usd"].quantile(0.75))
    top_wins = wins[wins["pnl_usd"] >= win_pnl_threshold].copy()
    non_winners = features[features["is_non_winner"]].copy()
    losses = features[features["is_loss"]].copy()
    high_mfe_threshold = float(features["mfe_pts"].quantile(0.75))
    high_mfe = features[features["mfe_pts"] >= high_mfe_threshold].copy()

    bool_cols = [
        "ema_stack_bull",
        "ema_stack_bear",
        "vwap_bull",
        "vwap_bear",
        "bull_rejection",
        "bear_rejection",
        "bull_engulfing",
        "bear_engulfing",
        "bull_fvg",
        "bear_fvg",
        "bull_mss_now",
        "bear_mss_now",
        "swept_asia_low_preopen",
        "swept_asia_high_preopen",
        "swept_london_low_preopen",
        "swept_london_high_preopen",
    ]
    num_cols = [
        "minutes_from_ny_open",
        "confluence",
        "vol_ratio_20",
        "body_ratio_20",
        "vwap_dist_pts",
        "lower_wick_ratio",
        "upper_wick_ratio",
        "daily_atr14",
        "overnight_range",
        "ny_open_pos_in_asia_range",
        "ny_open_pos_in_london_range",
        "dist_ny_open_to_nearest_pool",
        "mfe_pts",
        "mae_pts",
    ]

    bool_wins = _bool_pattern_table(features, wins, bool_cols)
    bool_top = _bool_pattern_table(features, top_wins, bool_cols)
    bool_wins_vs_losses = _bool_pattern_table(losses, wins, bool_cols)
    bool_wins_vs_non_winners = _bool_pattern_table(non_winners, wins, bool_cols)
    bool_high_mfe = _bool_pattern_table(features, high_mfe, bool_cols)

    num_wins = _numeric_pattern_table(features, wins, num_cols)
    num_top = _numeric_pattern_table(features, top_wins, num_cols)
    num_wins_vs_losses = _numeric_pattern_table(losses, wins, num_cols)
    num_wins_vs_non_winners = _numeric_pattern_table(non_winners, wins, num_cols)
    num_high_mfe = _numeric_pattern_table(features, high_mfe, num_cols)

    stability_bool = _pattern_stability_matrix(features, bool_cols)
    stability_year_fold = _year_and_fold_stability(features, bool_cols)
    loser_overlap = _loser_overlap_with_winner_profile(features, stability_bool)

    features.to_csv(OUTDIR / "control_trade_entry_features.csv", index=False)
    bool_wins.to_csv(OUTDIR / "patterns_bool_wins_vs_all.csv", index=False)
    bool_top.to_csv(OUTDIR / "patterns_bool_topwins_vs_all.csv", index=False)
    bool_wins_vs_losses.to_csv(OUTDIR / "patterns_bool_wins_vs_losses.csv", index=False)
    bool_wins_vs_non_winners.to_csv(OUTDIR / "patterns_bool_wins_vs_non_winners.csv", index=False)
    bool_high_mfe.to_csv(OUTDIR / "patterns_bool_highmfe_vs_all.csv", index=False)

    num_wins.to_csv(OUTDIR / "patterns_numeric_wins_vs_all.csv", index=False)
    num_top.to_csv(OUTDIR / "patterns_numeric_topwins_vs_all.csv", index=False)
    num_wins_vs_losses.to_csv(OUTDIR / "patterns_numeric_wins_vs_losses.csv", index=False)
    num_wins_vs_non_winners.to_csv(OUTDIR / "patterns_numeric_wins_vs_non_winners.csv", index=False)
    num_high_mfe.to_csv(OUTDIR / "patterns_numeric_highmfe_vs_all.csv", index=False)

    stability_bool.to_csv(OUTDIR / "pattern_stability_matrix.csv", index=False)
    stability_year_fold.to_csv(OUTDIR / "pattern_stability_year_fold.csv", index=False)
    if loser_overlap.empty:
        # File still exists from helper when no overlap profile is available.
        pass

    summary = {
        "control_metrics": {
            "trades": int(res["trades"]),
            "profit_factor": float(res["profit_factor"]),
            "expectancy": float(res["expectancy"]),
            "total_pnl": float(res["total_pnl"]),
        },
        "discovery_sets": {
            "all_trades": int(len(features)),
            "wins": int(len(wins)),
            "losses": int(len(losses)),
            "non_winners": int(len(non_winners)),
            "top_wins_threshold_pnl": win_pnl_threshold,
            "top_wins": int(len(top_wins)),
            "high_mfe_threshold_pts": high_mfe_threshold,
            "high_mfe": int(len(high_mfe)),
        },
        "discovery_note": "Discovery signal, not rule candidate yet.",
        "artifacts": {
            "features_csv": str(OUTDIR / "control_trade_entry_features.csv"),
            "bool_wins_csv": str(OUTDIR / "patterns_bool_wins_vs_all.csv"),
            "bool_top_csv": str(OUTDIR / "patterns_bool_topwins_vs_all.csv"),
            "bool_wins_vs_losses_csv": str(OUTDIR / "patterns_bool_wins_vs_losses.csv"),
            "bool_wins_vs_non_winners_csv": str(OUTDIR / "patterns_bool_wins_vs_non_winners.csv"),
            "bool_high_mfe_csv": str(OUTDIR / "patterns_bool_highmfe_vs_all.csv"),
            "numeric_wins_csv": str(OUTDIR / "patterns_numeric_wins_vs_all.csv"),
            "numeric_top_csv": str(OUTDIR / "patterns_numeric_topwins_vs_all.csv"),
            "numeric_wins_vs_losses_csv": str(OUTDIR / "patterns_numeric_wins_vs_losses.csv"),
            "numeric_wins_vs_non_winners_csv": str(OUTDIR / "patterns_numeric_wins_vs_non_winners.csv"),
            "numeric_high_mfe_csv": str(OUTDIR / "patterns_numeric_highmfe_vs_all.csv"),
            "stability_matrix_csv": str(OUTDIR / "pattern_stability_matrix.csv"),
            "stability_year_fold_csv": str(OUTDIR / "pattern_stability_year_fold.csv"),
            "loser_overlap_csv": str(OUTDIR / "loser_overlap_winner_profile.csv"),
        },
        "params": asdict(p),
    }

    (OUTDIR / "expectation_discovery_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("WROTE", OUTDIR / "expectation_discovery_summary.json")
    print(
        "Control trades:",
        len(features),
        "| Wins:",
        len(wins),
        "| Losses:",
        len(losses),
        "| Non-winners:",
        len(non_winners),
        "| Top wins:",
        len(top_wins),
        "| High-MFE:",
        len(high_mfe),
    )
    print("Top bool stability signals (wins vs non-winners):")
    print(stability_bool.head(10).to_string(index=False))
    print("Top year/fold-stable winner signals:")
    print(stability_year_fold.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
