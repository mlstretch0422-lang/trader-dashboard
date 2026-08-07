#!/usr/bin/env python3
"""Validate Expectation Engine variants as isolated, testable modules.

This script intentionally avoids optimizer sweeps. It runs paired module tests
against a fixed base strategy so we can attribute impact to expectation logic only.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

import pandas as pd

from orb_v2_optimizer import (
    StrategyParams,
    backtest,
    build_orb_lookup,
    load_data,
    run_gate_funnel_diagnostics,
    walk_forward_eval,
)


BASELINE_SUMMARY_PATH = Path(
    "trading_os/experiments/outputs/opt_funded_recovery_260_retryD/orb_v2_optimizer_summary.json"
)
SESSION_CONTEXT_PATH = Path("trading_os/experiments/outputs/session_context_features.csv")


def _load_base_params() -> StrategyParams:
    summary = json.loads(BASELINE_SUMMARY_PATH.read_text(encoding="utf-8"))
    return StrategyParams(**summary["best_trial"]["params"])


def _promote_or_reject(control: Dict, candidate: Dict) -> str:
    # Minimum quality gates before any promotion discussion.
    if candidate["trades"] < 20:
        return "REJECT_SAMPLE"
    if candidate["funded"]["dd_breached"]:
        return "REJECT_RISK"

    uplift_expectancy = candidate["expectancy"] - control["expectancy"]
    uplift_pf = candidate["profit_factor"] - control["profit_factor"]
    uplift_wf = (
        candidate["walk_forward"]["summary"].get("profitable_fold_rate", 0.0)
        - control["walk_forward"]["summary"].get("profitable_fold_rate", 0.0)
    )

    if uplift_expectancy > 0 and uplift_pf > 0 and uplift_wf >= 0:
        return "PROMOTE_CANDIDATE"
    return "REJECT_NO_EDGE"


def _compute_expectation_tag_attribution(
    df: pd.DataFrame, control_trades: pd.DataFrame, session_ctx: pd.DataFrame
) -> pd.DataFrame:
    if control_trades.empty:
        return pd.DataFrame()

    bars = df.copy()
    bars = bars.set_index("datetime", drop=False)

    swing_high = bars["high"].rolling(5).max().shift(1)
    swing_low = bars["low"].rolling(5).min().shift(1)
    bull_mss = swing_high.notna() & (bars["close"] > swing_high)
    bear_mss = swing_low.notna() & (bars["close"] < swing_low)

    t = control_trades.copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"])
    t["side"] = t["side"].astype(str)

    ctx_cols = [
        "date",
        "swept_asia_low_preopen",
        "swept_asia_high_preopen",
        "swept_london_low_preopen",
        "swept_london_high_preopen",
        "ny_open_pos_in_asia_range",
        "ny_open_pos_in_london_range",
        "dist_ny_open_to_nearest_pool",
    ]
    session_ctx = session_ctx[ctx_cols].copy()
    session_ctx["date"] = pd.to_datetime(session_ctx["date"]).dt.date

    t = control_trades.copy()
    t["entry_time"] = pd.to_datetime(t["entry_time"])
    t["side"] = t["side"].astype(str)
    t["date"] = t["entry_time"].dt.date
    t = t.merge(session_ctx, on="date", how="left")

    labels = []
    for row in t.itertuples(index=False):
        if row.entry_time not in bars.index:
            labels.append({
                "expectation_tag": False,
                "sweep_tag": False,
                "response_tag": False,
                "context_tag": False,
            })
            continue

        near_pool = bool(getattr(row, "dist_ny_open_to_nearest_pool", 999.0) <= 6.0)
        in_asia_band = bool(-0.25 <= float(getattr(row, "ny_open_pos_in_asia_range", -99.0)) <= 1.25)
        in_london_band = bool(-0.25 <= float(getattr(row, "ny_open_pos_in_london_range", -99.0)) <= 1.25)

        if row.side == "LONG":
            sweep_tag = bool(
                getattr(row, "swept_asia_low_preopen", False)
                or getattr(row, "swept_london_low_preopen", False)
            )
            response_tag = bool(
                bars.loc[row.entry_time, "bull_rejection"]
                or bars.loc[row.entry_time, "bull_engulfing"]
                or bull_mss.loc[row.entry_time]
            )
            context_tag = bool(near_pool and (in_asia_band or in_london_band))
        else:
            sweep_tag = bool(
                getattr(row, "swept_asia_high_preopen", False)
                or getattr(row, "swept_london_high_preopen", False)
            )
            response_tag = bool(
                bars.loc[row.entry_time, "bear_rejection"]
                or bars.loc[row.entry_time, "bear_engulfing"]
                or bear_mss.loc[row.entry_time]
            )
            context_tag = bool(near_pool and (in_asia_band or in_london_band))

        labels.append({
            "expectation_tag": bool(context_tag and sweep_tag and response_tag),
            "sweep_tag": sweep_tag,
            "response_tag": response_tag,
            "context_tag": context_tag,
        })

    tags = pd.DataFrame(labels)
    t = pd.concat([t.reset_index(drop=True), tags], axis=1)

    rows = []
    for grp_val, grp in t.groupby("expectation_tag"):
        wins = grp[grp["pnl_usd"] > 0]
        losses = grp[grp["pnl_usd"] < 0]
        gross_profit = float(wins["pnl_usd"].sum())
        gross_loss = float(abs(losses["pnl_usd"].sum()))
        pf = gross_profit / gross_loss if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
        rows.append(
            {
                "expectation_tag": bool(grp_val),
                "trades": int(len(grp)),
                "win_rate": float((grp["pnl_usd"] > 0).mean()) if len(grp) else 0.0,
                "expectancy": float(grp["pnl_usd"].mean()) if len(grp) else 0.0,
                "profit_factor": float(pf),
                "total_pnl": float(grp["pnl_usd"].sum()),
                "avg_confluence": float(grp["confluence"].mean()) if "confluence" in grp else 0.0,
            }
        )

    rows.append(
        {
            "expectation_tag": "ALL",
            "trades": int(len(t)),
            "win_rate": float((t["pnl_usd"] > 0).mean()) if len(t) else 0.0,
            "expectancy": float(t["pnl_usd"].mean()) if len(t) else 0.0,
            "profit_factor": float(
                (t[t["pnl_usd"] > 0]["pnl_usd"].sum() / abs(t[t["pnl_usd"] < 0]["pnl_usd"].sum()))
                if abs(t[t["pnl_usd"] < 0]["pnl_usd"].sum()) > 0
                else (999.0 if t[t["pnl_usd"] > 0]["pnl_usd"].sum() > 0 else 0.0)
            ),
            "total_pnl": float(t["pnl_usd"].sum()),
            "avg_confluence": float(t["confluence"].mean()) if "confluence" in t else 0.0,
        }
    )

    return pd.DataFrame(rows)


def main() -> None:
    outdir = Path("trading_os/experiments/outputs/expectation_engine_validation_2026-07-08")
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_data(Path("ES_backtest_data.csv"), years=8)
    if not SESSION_CONTEXT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {SESSION_CONTEXT_PATH}. Build it with trading_os/experiments/build_session_context_features.py"
        )
    session_ctx = pd.read_csv(SESSION_CONTEXT_PATH)

    base = _load_base_params()
    # Freeze operating constraints used throughout this project phase.
    base.max_trades_per_day = 1
    base.trade_start_min = 570
    base.entry_end_min = 630
    base.strategy_daily_loss_stop_usd = 200.0

    variants: List[Dict] = [
        {
            "variant_id": "control_no_expectation",
            "hypothesis": "No expectation filter baseline for paired comparison.",
            "patch": {
                "use_liquidity_sweep": False,
                "use_bull_rejection": False,
                "use_bear_rejection": False,
            },
        },
        {
            "variant_id": "exp_sweep_reclaim_state",
            "hypothesis": "Require mapped sweep state plus reclaim acceptance band.",
            "patch": {
                "use_liquidity_sweep": True,
                "sweep_tolerance_pts": 1.0,
                "sweep_lookback_bars": 20,
                "use_bull_rejection": False,
                "use_bear_rejection": False,
            },
        },
        {
            "variant_id": "exp_sweep_plus_rejection",
            "hypothesis": "Sweep state plus rejection proxy captures failed continuation.",
            "patch": {
                "use_liquidity_sweep": True,
                "sweep_tolerance_pts": 1.0,
                "sweep_lookback_bars": 20,
                "use_bull_rejection": True,
                "use_bear_rejection": True,
                "rejection_wick_ratio": 1.0,
            },
        },
        {
            "variant_id": "exp_sweep_plus_engulfing",
            "hypothesis": "Sweep state plus body reclaim proxy improves response quality.",
            "patch": {
                "use_liquidity_sweep": True,
                "sweep_tolerance_pts": 1.0,
                "sweep_lookback_bars": 20,
                "use_bull_rejection": False,
                "use_bear_rejection": False,
                "use_bull_engulfing": True,
                "use_bear_engulfing": True,
            },
        },
        {
            "variant_id": "exp_sweep_plus_mss",
            "hypothesis": "Sweep state plus structure-shift proxy improves directional validity.",
            "patch": {
                "use_liquidity_sweep": True,
                "sweep_tolerance_pts": 1.0,
                "sweep_lookback_bars": 20,
                "use_bull_rejection": False,
                "use_bear_rejection": False,
                "use_bull_mss": True,
                "use_bear_mss": True,
                "mss_lookback": 5,
            },
        },
    ]

    results: List[Dict] = []
    detail: Dict[str, Dict] = {}
    bt_objects: Dict[str, Dict] = {}

    for item in variants:
        p = StrategyParams(**asdict(base))
        for key, value in item["patch"].items():
            setattr(p, key, value)

        orb = build_orb_lookup(df, p.orb_start_min, p.orb_end_min, p.min_orb_range, p.max_orb_range)
        bt = backtest(
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
        wf = walk_forward_eval(
            df,
            p,
            train_years=4,
            test_years=1,
            funded_monthly_target=3000.0,
            funded_monthly_stretch_target=5000.0,
            funded_daily_loss=2000.0,
            funded_trailing_max_drawdown=2500.0,
            funded_static_max_drawdown=3000.0,
            point_value=50.0,
        )
        gf = run_gate_funnel_diagnostics(df, orb, p)

        vdir = outdir / item["variant_id"]
        vdir.mkdir(parents=True, exist_ok=True)
        gf.to_csv(vdir / "gate_funnel.csv", index=False)

        variant_payload = {
            "variant_id": item["variant_id"],
            "hypothesis": item["hypothesis"],
            "params": asdict(p),
            "backtest": {
                "status": bt["status"],
                "trades": bt["trades"],
                "profit_factor": bt["profit_factor"],
                "expectancy": bt["expectancy"],
                "total_pnl": bt["total_pnl"],
                "max_drawdown": bt["max_drawdown"],
                "funded": bt["funded"],
            },
            "walk_forward": wf,
            "artifact_dir": str(vdir),
        }
        (vdir / "summary.json").write_text(json.dumps(variant_payload, indent=2), encoding="utf-8")

        detail[item["variant_id"]] = variant_payload
        bt_objects[item["variant_id"]] = bt
        results.append(
            {
                "variant_id": item["variant_id"],
                "hypothesis": item["hypothesis"],
                "status": bt["status"],
                "trades": bt["trades"],
                "profit_factor": bt["profit_factor"],
                "expectancy": bt["expectancy"],
                "total_pnl": bt["total_pnl"],
                "monthly_pass_rate": bt["funded"].get("monthly_pass_rate", 0.0),
                "trailing_dd_breached": bt["funded"].get("trailing_dd_breached", False),
                "static_dd_breached": bt["funded"].get("static_dd_breached", False),
                "wf_profitable_fold_rate": wf.get("summary", {}).get("profitable_fold_rate", 0.0),
                "wf_count": wf.get("summary", {}).get("count", 0),
            }
        )

    report = pd.DataFrame(results)
    control = detail["control_no_expectation"]
    control_bt = control["backtest"]

    decisions = []
    for _, row in report.iterrows():
        variant_id = str(row["variant_id"])
        payload = detail[variant_id]
        decision = _promote_or_reject(
            {
                "trades": control_bt["trades"],
                "expectancy": control_bt["expectancy"],
                "profit_factor": control_bt["profit_factor"],
                "walk_forward": control["walk_forward"],
                "funded": control_bt["funded"],
            },
            {
                "trades": payload["backtest"]["trades"],
                "expectancy": payload["backtest"]["expectancy"],
                "profit_factor": payload["backtest"]["profit_factor"],
                "walk_forward": payload["walk_forward"],
                "funded": payload["backtest"]["funded"],
            },
        )
        decisions.append(decision)

    report["decision"] = decisions
    report["delta_expectancy_vs_control"] = report["expectancy"] - float(control_bt["expectancy"])
    report["delta_pf_vs_control"] = report["profit_factor"] - float(control_bt["profit_factor"])
    report["delta_trades_vs_control"] = report["trades"] - int(control_bt["trades"])
    report = report.sort_values(["decision", "trades", "profit_factor"], ascending=[True, False, False])

    report.to_csv(outdir / "expectation_engine_report.csv", index=False)

    control_trades = bt_objects["control_no_expectation"]["trades_df"]
    attribution = _compute_expectation_tag_attribution(df, control_trades, session_ctx)
    attribution.to_csv(outdir / "expectation_tag_attribution.csv", index=False)

    (outdir / "expectation_engine_report.json").write_text(
        json.dumps(
            {
                "control_variant": "control_no_expectation",
                "report_rows": report.to_dict(orient="records"),
                "variants": detail,
                "expectation_tag_attribution_csv": str(outdir / "expectation_tag_attribution.csv"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    cols = [
        "variant_id",
        "decision",
        "trades",
        "profit_factor",
        "expectancy",
        "total_pnl",
        "delta_expectancy_vs_control",
        "wf_profitable_fold_rate",
    ]
    print("WROTE", outdir / "expectation_engine_report.csv")
    print(report[cols].to_string(index=False))
    if not attribution.empty:
        print("WROTE", outdir / "expectation_tag_attribution.csv")
        print(attribution.to_string(index=False))


if __name__ == "__main__":
    main()
