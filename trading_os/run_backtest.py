"""Tiny CLI to run a regime-aware ORB analysis on available ES market data."""
import os
import sys

import pandas as pd

# Ensure `src/` is importable when running this script from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.system.core import backtest_stub
from src import describe, get_version, summary_from_trades
from src.strategies.clean_orb import compute_orb, generate_signals


def main():
    info = describe()
    print(f"{info['name']} v{info['version']}")
    results = backtest_stub()
    print("Backtest results:", results)

    data_path = os.path.join(os.path.dirname(__file__), "../ES_backtest_data.market_hours_only.backup.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(__file__), "../ES_backtest_data.csv")

    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        orb_map = compute_orb(df, 570, 585)
        trades = generate_signals(df, orb_map, 570, 585, market_phase_filter=True, market_phase_threshold=0.5, use_vwap=False, use_ema=False)
        summary = summary_from_trades(trades)
        print("Regime summary:", summary)
    else:
        print("No market data file found; using stub output only.")


if __name__ == "__main__":
    main()
