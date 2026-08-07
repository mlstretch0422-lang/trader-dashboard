import unittest

import pandas as pd

from strat.backtest import run_orb_midpoint_backtest


class OrbBacktestTests(unittest.TestCase):
    def test_runs_on_synthetic_ohlc(self) -> None:
        rows = []
        base = pd.Timestamp("2024-01-02 09:30")
        for day in range(3):
            day_start = base + pd.Timedelta(days=day)
            for minute in range(0, 75):
                ts = day_start + pd.Timedelta(minutes=minute)
                open_price = 1000.0 + day * 10.0
                if minute < 15:
                    high = open_price + 2.0
                    low = open_price - 2.0
                    close = open_price + 1.0
                elif minute < 20:
                    high = open_price + 8.0
                    low = open_price + 1.0
                    close = open_price + 7.0
                elif minute < 25:
                    high = open_price + 1.0
                    low = open_price - 1.0
                    close = open_price - 0.5
                else:
                    high = open_price + 0.5
                    low = open_price - 0.5
                    close = open_price + 0.2
                rows.append({
                    "timestamp": ts,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 100,
                })
        df = pd.DataFrame(rows)
        results = run_orb_midpoint_backtest(df, timezone="UTC")
        self.assertGreater(len(results), 0)
        self.assertIn("pnl_usd", results.columns)


if __name__ == "__main__":
    unittest.main()
