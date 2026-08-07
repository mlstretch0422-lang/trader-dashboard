import argparse
from pathlib import Path
import pandas as pd
from strat.metrics import compute_metrics


def load_reconstructed(path: Path) -> pd.DataFrame:
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Reconstructed trades file not found: {path}")
    return pd.read_csv(path, parse_dates=["entry_time", "exit_time"], low_memory=False)


# compute_metrics is provided by `strat.metrics`


def print_metrics(name: str, m: dict) -> None:
    print(f"--- {name} ---")
    if m.get("total_trades", 0) == 0:
        print("No closed trades")
        return
    print(f"trades: {m['total_trades']}")
    print(f"total P&L: {m['total_pnl']:.2f}")
    print(f"profit factor: {m['profit_factor']:.3f}")
    print(f"expectancy/trade: {m['expectancy']:.2f}")
    print(f"win rate: {m['win_rate']*100:.1f}%")
    print(f"avg win: {m['avg_win']:.2f} avg loss: {m['avg_loss']:.2f}")
    print()


def ab_compare(df: pd.DataFrame, by: str) -> None:
    groups = df["exit_price"].notna().groupby(df[by])
    vals = df[df["exit_price"].notna()].copy()
    for name, group in vals.groupby(by):
        m = compute_metrics(group)
        print_metrics(f"Group {by}={name}", m)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple A/B tests on reconstructed trades")
    parser.add_argument("--file", type=Path, default=Path("data/reconstructed_trades.csv"))
    parser.add_argument("--group-by", type=str, default="entry_type", help="column to group by for A/B comparison")
    args = parser.parse_args()

    df = load_reconstructed(args.file)
    overall = compute_metrics(df)
    print_metrics("Overall", overall)
    if args.group_by in df.columns:
        ab_compare(df, args.group_by)
    else:
        print(f"Group column '{args.group_by}' not in dataset columns: {df.columns.tolist()}")
