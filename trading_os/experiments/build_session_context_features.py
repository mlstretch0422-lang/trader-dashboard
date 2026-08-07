#!/usr/bin/env python3
"""Build full-session context features (Asia/London/overnight) for ES.

Outputs a per-NY-date feature table that can be joined to regular-hours backtest data.
This script does not change strategy logic; it supplies missing visual context inputs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _pick_continuous_outright(full_path: Path, chunksize: int = 750_000) -> pd.DataFrame:
    picks = []
    usecols = ["ts_event", "open", "high", "low", "close", "volume", "symbol"]

    for chunk in pd.read_csv(full_path, usecols=usecols, chunksize=chunksize):
        # Keep outright ES contracts only; drop calendar spreads.
        chunk = chunk[chunk["symbol"].astype(str).str.startswith("ES")]
        chunk = chunk[~chunk["symbol"].astype(str).str.contains("-", regex=False)]
        if chunk.empty:
            continue

        # One row per minute: choose highest-volume outright as active contract proxy.
        idx = chunk.groupby("ts_event")["volume"].idxmax()
        picks.append(chunk.loc[idx, ["ts_event", "open", "high", "low", "close", "volume"]])

    if not picks:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

    merged = pd.concat(picks, ignore_index=True)
    idx2 = merged.groupby("ts_event")["volume"].idxmax()
    out = merged.loc[idx2].copy()
    out["datetime"] = pd.to_datetime(out["ts_event"], utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
    out = out.drop(columns=["ts_event"]).sort_values("datetime").reset_index(drop=True)
    return out


def _build_daily_features(full_df: pd.DataFrame) -> pd.DataFrame:
    if full_df.empty:
        return pd.DataFrame()

    d = full_df.copy()
    d["date"] = d["datetime"].dt.date
    d["time_min"] = d["datetime"].dt.hour * 60 + d["datetime"].dt.minute

    # Session-date mapping: 18:00-23:59 belongs to next NY trade date.
    d["trade_date"] = d["date"]
    after_18 = d["time_min"] >= 18 * 60
    d.loc[after_18, "trade_date"] = (pd.to_datetime(d.loc[after_18, "date"]) + pd.Timedelta(days=1)).dt.date

    asia = d[((d["time_min"] >= 20 * 60) | (d["time_min"] < 3 * 60))]
    london = d[(d["time_min"] >= 3 * 60) & (d["time_min"] < 8 * 60)]
    overnight = d[((d["time_min"] >= 18 * 60) | (d["time_min"] < 9 * 60 + 30))]
    ny_open = d[d["time_min"] == 9 * 60 + 30][["trade_date", "open"]].rename(columns={"open": "ny_open"})

    asia_agg = asia.groupby("trade_date").agg(
        asia_high=("high", "max"),
        asia_low=("low", "min"),
    )
    london_agg = london.groupby("trade_date").agg(
        london_high=("high", "max"),
        london_low=("low", "min"),
    )
    over_agg = overnight.groupby("trade_date").agg(
        overnight_high=("high", "max"),
        overnight_low=("low", "min"),
    )

    # Prior NY regular-session levels (09:30-16:00), shifted by one date.
    ny_rth = d[(d["time_min"] >= 9 * 60 + 30) & (d["time_min"] <= 16 * 60)]
    prior = ny_rth.groupby("date").agg(prior_day_high=("high", "max"), prior_day_low=("low", "min"))
    prior.index = pd.to_datetime(prior.index)
    prior = prior.shift(1)
    prior.index = prior.index.date

    out = asia_agg.join(london_agg, how="outer").join(over_agg, how="outer")
    out = out.join(ny_open.set_index("trade_date"), how="left")
    out = out.join(prior, how="left")

    # Pre-open sweep checks against Asia/London pools must occur AFTER each pool is formed.
    # Asia sweeps are checked from 03:00 to 09:29 ET.
    post_asia = d[(d["time_min"] >= 3 * 60) & (d["time_min"] < 9 * 60 + 30)]
    post_asia_agg = post_asia.groupby("trade_date").agg(
        post_asia_min_low=("low", "min"),
        post_asia_max_high=("high", "max"),
    )

    # London sweeps are checked from 08:00 to 09:29 ET.
    post_london = d[(d["time_min"] >= 8 * 60) & (d["time_min"] < 9 * 60 + 30)]
    post_london_agg = post_london.groupby("trade_date").agg(
        post_london_min_low=("low", "min"),
        post_london_max_high=("high", "max"),
    )

    out = out.join(post_asia_agg, how="left").join(post_london_agg, how="left")

    out["swept_asia_low_preopen"] = out["post_asia_min_low"] <= out["asia_low"]
    out["swept_asia_high_preopen"] = out["post_asia_max_high"] >= out["asia_high"]
    out["swept_london_low_preopen"] = out["post_london_min_low"] <= out["london_low"]
    out["swept_london_high_preopen"] = out["post_london_max_high"] >= out["london_high"]

    out["overnight_range"] = out["overnight_high"] - out["overnight_low"]

    # NY open location vs ranges.
    asia_den = (out["asia_high"] - out["asia_low"]).replace(0.0, np.nan)
    london_den = (out["london_high"] - out["london_low"]).replace(0.0, np.nan)
    out["ny_open_pos_in_asia_range"] = ((out["ny_open"] - out["asia_low"]) / asia_den).clip(-2, 3)
    out["ny_open_pos_in_london_range"] = ((out["ny_open"] - out["london_low"]) / london_den).clip(-2, 3)

    pools = ["asia_high", "asia_low", "london_high", "london_low", "prior_day_high", "prior_day_low"]
    for p in pools:
        out[f"dist_ny_open_to_{p}"] = (out["ny_open"] - out[p]).abs()

    out["dist_ny_open_to_nearest_pool"] = out[[f"dist_ny_open_to_{p}" for p in pools]].min(axis=1)

    out = out.reset_index().rename(columns={"trade_date": "date"})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build full-session context features for expectation validation")
    parser.add_argument("--full-data", default="glbx-mdp3-20100606-20260701.ohlcv-1m.csv.zst")
    parser.add_argument("--out", default="trading_os/experiments/outputs/session_context_features.csv")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not args.force:
        print(f"EXISTS {out_path} (use --force to rebuild)")
        return

    full_df = _pick_continuous_outright(Path(args.full_data))
    features = _build_daily_features(full_df)
    features.to_csv(out_path, index=False)

    print(f"WROTE {out_path}")
    print("rows", len(features))
    if len(features):
        print(
            features[
                [
                    "date",
                    "asia_high",
                    "asia_low",
                    "london_high",
                    "london_low",
                    "overnight_range",
                    "ny_open",
                    "dist_ny_open_to_nearest_pool",
                ]
            ]
            .head(5)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
