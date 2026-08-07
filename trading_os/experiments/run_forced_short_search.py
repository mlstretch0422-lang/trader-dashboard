#!/usr/bin/env python3
"""Forced short-enabled search for ORB V2 with ICT/candle options."""

import json
import random
from pathlib import Path
import sys
import argparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orb_v2_optimizer import (
    StrategyParams,
    backtest,
    build_orb_lookup,
    load_data,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Forced short-enabled ICT search")
    parser.add_argument("--trials", type=int, default=220)
    parser.add_argument("--seed", type=int, default=20260703)
    parser.add_argument("--years", type=int, default=8)
    parser.add_argument("--min-trades", type=int, default=60)
    parser.add_argument("--min-months", type=int, default=36)
    parser.add_argument("--outfile", default="trading_os/experiments/outputs/opt_forced_short_ict_220.csv")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    df = load_data(ROOT / "ES_backtest_data.csv", years=args.years)

    rows = []
    for i in range(args.trials):
        p = StrategyParams(
            orb_start_min=480,
            orb_end_min=rng.choice([495, 500, 510]),
            min_orb_range=rng.choice([3.0, 4.0, 5.0]),
            max_orb_range=rng.choice([16.0, 20.0]),
            min_confluence=rng.choice([2, 3]),
            min_confluence_long=rng.choice([0, 2, 3, 4]),
            min_confluence_short=rng.choice([0, 2, 3, 4]),
            volume_mult=rng.choice([1.0, 1.25, 1.5]),
            displacement_mult=rng.choice([1.0, 1.5]),
            retest_fraction=rng.choice([0.5, 0.65]),
            retest_tolerance_pts=rng.choice([0.0, 0.5, 1.0]),
            tp_r=rng.choice([1.5, 2.0, 2.5]),
            break_even_r=rng.choice([0.0, 0.75, 1.0]),
            sl_buffer_pts=rng.choice([0.0, 0.5, 1.0]),
            entry_end_min=rng.choice([615, 630]),
            require_ema=True,
            require_vwap=True,
            use_volume=rng.choice([True, False]),
            use_displacement=rng.choice([True, False]),
            use_liquidity_sweep=rng.choice([False, True]),
            use_bull_rejection=rng.choice([False, True]),
            use_bull_engulfing=rng.choice([False, True]),
            use_bull_mss=rng.choice([False, True]),
            use_bull_fvg=rng.choice([False, True]),
            allow_short=True,
            max_trades_per_day=rng.choice([1, 2]),
            mss_lookback=rng.choice([3, 5, 8]),
            min_daily_atr14=rng.choice([0.0, 20.0, 30.0]),
            max_daily_atr14=rng.choice([100.0, 120.0, 9999.0]),
        )

        orb = build_orb_lookup(
            df,
            orb_start=p.orb_start_min,
            orb_end=p.orb_end_min,
            min_orb_range=p.min_orb_range,
            max_orb_range=p.max_orb_range,
        )
        r = backtest(
            df,
            orb,
            p,
            funded_monthly_target=3000,
            funded_daily_loss=1500,
            funded_trailing_max_drawdown=2000,
            funded_static_max_drawdown=2500,
        )

        if r["status"] != "SUCCESS":
            continue

        rows.append(
            {
                "trial": i + 1,
                "trades": r["trades"],
                "pf": r["profit_factor"],
                "wr": r["win_rate"],
                "expectancy": r["expectancy"],
                "pnl": r["total_pnl"],
                "maxdd": r["max_drawdown"],
                "pass_rate": r["funded"]["monthly_pass_rate"],
                "pass_months": r["funded"]["months_with_pass"],
                "months": r["funded"]["months_total"],
                "dd_breached": r["funded"]["dd_breached"],
                "params": json.dumps(p.__dict__),
            }
        )

        if (i + 1) % 10 == 0:
            print(f"Completed {i + 1}/{args.trials} forced-short trials...", flush=True)

    out = ROOT / args.outfile
    outdir = out.parent
    outdir.mkdir(parents=True, exist_ok=True)

    if not rows:
        print("No successful trials")
        return

    resdf = pd.DataFrame(rows)
    eligible = resdf[(resdf["trades"] >= args.min_trades) & (resdf["months"] >= args.min_months)].copy()

    if eligible.empty:
        eligible = resdf.copy()

    ranked = eligible.sort_values(
        by=["pass_rate", "pass_months", "pnl", "pf", "trades"],
        ascending=[False, False, False, False, False],
    )
    ranked.to_csv(out, index=False)

    print(f"Saved: {out}")
    print("Top 10 forced-short candidates:")
    print(
        ranked[
            [
                "trial",
                "trades",
                "pf",
                "wr",
                "expectancy",
                "pnl",
                "maxdd",
                "pass_rate",
                "pass_months",
                "months",
                "dd_breached",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )
    print("\nBest params JSON:")
    print(ranked.iloc[0]["params"])


if __name__ == "__main__":
    main()
