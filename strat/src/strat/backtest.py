from pathlib import Path
import pandas as pd


class Strategy:
    """Minimal strategy interface for the backtest scaffold.

    Implement `generate_signals(prices_df)` to return a DataFrame of intended
    trades: columns `entry_time`, `entry_price`, `side`, `qty`, `exit_time`, `exit_price`.
    """

    def __init__(self, name: str = "base"):
        self.name = name

    def generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError("Strategy must implement generate_signals")


def run_backtest(prices: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    # Simple evaluator: match signals to P&L using exit_price and entry_price
    trades = signals.copy()
    trades["realized_pnl_points"] = trades.apply(lambda r: (r["exit_price"] - r["entry_price"]) if r["side"].lower() == "long" else (r["entry_price"] - r["exit_price"]), axis=1)
    # naive contract multiplier inference
    trades["contract_multiplier"] = trades["symbol"].apply(lambda s: 50 if "ES1!" in s else (5 if "MES1!" in s else 1))
    trades["realized_pnl_usd"] = trades["realized_pnl_points"] * trades["contract_multiplier"] * trades.get("qty", 1)
    return trades


def find_price_files(data_dir: Path) -> list[Path]:
    p = data_dir.expanduser().resolve()
    files = sorted(p.glob("*.csv"))
    return files


def run_orb_midpoint_backtest(prices: pd.DataFrame, timezone: str = "America/New_York") -> pd.DataFrame:
    """Run a simple ORB midpoint retest backtest on OHLC data.

    Logic mirrors the user's described setup:
    - build a 9:30-9:45 ORB window
    - wait for the first breakout to the upside/downside
    - enter on a retest of the midpoint / boundary
    - exit at the next opposite-side signal or at the close of the session
    """
    df = prices.copy()
    if "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "datetime"})
    if "datetime" not in df.columns and "time" in df.columns:
        df = df.rename(columns={"time": "datetime"})
    if "datetime" not in df.columns:
        raise ValueError("prices must include a datetime-like column")

    df["datetime"] = pd.to_datetime(df["datetime"], utc=False, errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)

    if timezone != "UTC":
        df["datetime"] = df["datetime"].dt.tz_localize(None)

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

        if time_mins >= 570 and time_mins < 585:
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

        if orb_done and not entry_pending and breakout_long and time_mins >= 585 and time_mins < 1100:
            if row["low"] <= orb_mid and row["close"] >= orb_mid:
                entry_pending = True
                entry_dir = 1
                entry_price = row["close"]
                entry_time = ts
        elif orb_done and not entry_pending and breakout_short and time_mins >= 585 and time_mins < 1100:
            if row["high"] >= orb_mid and row["close"] <= orb_mid:
                entry_pending = True
                entry_dir = -1
                entry_price = row["close"]
                entry_time = ts

        if entry_pending and entry_dir == 1 and time_mins >= 585 and time_mins < 1100:
            if row["low"] <= orb_mid and row["close"] >= orb_mid:
                pnl = (row["close"] - entry_price) * 50
                rows.append({
                    "entry_time": entry_time,
                    "exit_time": ts,
                    "side": "long",
                    "entry_price": entry_price,
                    "exit_price": row["close"],
                    "pnl_points": row["close"] - entry_price,
                    "pnl_usd": pnl,
                })
                entry_pending = False
                entry_dir = 0
                entry_price = None
                entry_time = None
        elif entry_pending and entry_dir == -1 and time_mins >= 585 and time_mins < 1100:
            if row["high"] >= orb_mid and row["close"] <= orb_mid:
                pnl = (entry_price - row["close"]) * 50
                rows.append({
                    "entry_time": entry_time,
                    "exit_time": ts,
                    "side": "short",
                    "entry_price": entry_price,
                    "exit_price": row["close"],
                    "pnl_points": entry_price - row["close"],
                    "pnl_usd": pnl,
                })
                entry_pending = False
                entry_dir = 0
                entry_price = None
                entry_time = None

    return pd.DataFrame(rows)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Backtest scaffold (requires price CSVs in data/prices)")
    parser.add_argument("--price-dir", type=Path, default=Path("data/prices"))
    args = parser.parse_args()
    files = find_price_files(args.price_dir)
    if not files:
        print(f"No price CSVs found in {args.price_dir}. Add OHLC CSVs to run experiments.")
    else:
        print(f"Found price files: {files}")
