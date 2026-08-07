from pathlib import Path
import pandas as pd


def tag_trades(infile_or_df, outfile) -> pd.DataFrame:
    if isinstance(infile_or_df, pd.DataFrame):
        df = infile_or_df.copy()
    else:
        df = pd.read_csv(infile_or_df, parse_dates=["entry_time", "exit_time"], low_memory=False)
    df = df.copy()

    if "entry_time" in df.columns:
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
    if "exit_time" in df.columns:
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")

    # session hour
    df["entry_hour"] = df["entry_time"].dt.hour

    # simple heuristics
    df["trade_label"] = df["entry_type"].fillna("").apply(lambda v: "retest" if str(v).lower().startswith("limit") else "break")
    df["outcome"] = df["realized_pnl_usd"].apply(lambda x: "win" if pd.notna(x) and float(x) > 0 else ("loss" if pd.notna(x) else "open"))
    df["symbol_short"] = df["symbol"].astype(str).str.split(":").str[1].str.replace("1!", "", regex=False).str.replace("MES", "M", regex=False)

    # add duration (seconds) for closed trades
    df["duration_s"] = (df["exit_time"] - df["entry_time"]).dt.total_seconds()

    out_path = Path(outfile).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tag reconstructed trades with simple heuristics")
    parser.add_argument("--infile", type=Path, default=Path("data/reconstructed_trades.csv"))
    parser.add_argument("--outfile", type=Path, default=Path("data/reconstructed_trades_tagged.csv"))
    args = parser.parse_args()
    df = tag_trades(args.infile, args.outfile)
    print(f"Tagged trades saved to {args.outfile} rows={len(df)}")
