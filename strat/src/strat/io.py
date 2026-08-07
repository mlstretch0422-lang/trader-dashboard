import glob
from pathlib import Path
import pandas as pd


def load_csv_files(directory: Path, pattern: str = "*.csv") -> list[pd.DataFrame]:
    directory = directory.expanduser().resolve()
    paths = sorted(directory.glob(pattern))
    return [pd.read_csv(path) for path in paths]


def load_paper_trading_order_history(directory: Path, pattern: str = "paper-trading-order-history-all-*.csv") -> pd.DataFrame:
    directory = directory.expanduser().resolve()
    paths = sorted(directory.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No paper trading order history CSVs found in {directory}")

    frames = []
    for idx, path in enumerate(paths):
        df = pd.read_csv(path)
        df["source_file"] = path.name
        df["source_rank"] = idx
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    if "Order ID" in combined.columns:
        combined = combined.sort_values(["source_rank"], ascending=True)
        combined = combined.drop_duplicates(subset=["Order ID"], keep="last")

    return combined.drop(columns=["source_rank"], errors="ignore")


def normalize_order_history(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rename_map = {
        "Symbol": "symbol",
        "Side": "side",
        "Type": "order_type",
        "Qty": "qty",
        "Limit Price": "limit_price",
        "Stop Price": "stop_price",
        "Fill Price": "fill_price",
        "Status": "status",
        "Commission": "commission",
        "Placing Time": "placing_time",
        "Closing Time": "closing_time",
        "Order ID": "order_id",
        "Level ID": "level_id",
        "Leverage": "leverage",
        "Margin": "margin",
    }
    df = df.rename(columns=rename_map)

    for col in ("placing_time", "closing_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "qty" in df.columns:
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    for col in ("fill_price", "limit_price", "stop_price"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "side" in df.columns:
        df["side"] = df["side"].astype(str).str.strip().str.title()
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str)

    return df


def load_data(directory: Path) -> pd.DataFrame:
    files = sorted(directory.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {directory}")

    frames = []
    for path in files:
        df = pd.read_csv(path)
        df["source_file"] = path.name
        frames.append(df)

    return pd.concat(frames, ignore_index=True)
